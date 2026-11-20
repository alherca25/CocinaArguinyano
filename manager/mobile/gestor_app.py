"""
Gestor de Recetas «Cocina Rápida» — app móvil del administrador (Kivy / Android).

Lee la base de datos de alherca25/BaseDatosRecetas y guarda los cambios
directamente en GitHub con un token personal (permiso «Contents: write»).

Seguridad de los datos:
  - No se puede guardar nada hasta haber cargado la BD correctamente.
  - Cada guardado usa el «sha» de la versión cargada: si alguien la cambió
    entretanto, GitHub lo rechaza y la app pide recargar (no se pisa nada).
  - Los cambios se aplican sobre una copia; si la subida falla, no se pierden
    ni se quedan a medias.
"""
import copy
import os
import sys
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

# Desde el repositorio, los módulos comunes están en ../../shared; en el APK/.exe van junto a este archivo.
_SHARED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared")
if os.path.isdir(_SHARED):
    sys.path.insert(0, os.path.abspath(_SHARED))

import functions
from mobile_ui import (AppBar, AutoLabel, Busy, C, Card, Chip, Dialog, Field, IconButton,
                       RoundButton, TabBar, TickBox, Toast, asset_path, confirm, empty_state,
                       muted_label, setup_window, show_info, spacer, tag_row, title_label,
                       user_dir)

LOGO = "icon_edit.png"
UNIT_CHOICES = [""] + functions.UNITS


# ===========================================================================
# LÓGICA
# ===========================================================================
class ManagerLogic:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.db = None          # None = no cargada todavía (no se permite guardar)
        self.sha = None
        self.user = ""          # login de GitHub tras validar el token

    # --- token ------------------------------------------------------------
    @property
    def token_path(self):
        return os.path.join(self.data_dir, "token.txt")

    def get_token(self):
        try:
            with open(self.token_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""

    def save_token(self, token):
        with open(self.token_path, "w", encoding="utf-8") as f:
            f.write(token.strip())

    def delete_token(self):
        try:
            os.remove(self.token_path)
        except OSError:
            pass
        self.user, self.db, self.sha = "", None, None

    def unlock(self, token):
        """Valida el token contra GitHub; si es correcto lo guarda. Lanza GitHubError si no."""
        self.user = functions.github_check_access(token.strip())
        self.save_token(token)

    # --- base de datos ---------------------------------------------------------
    @property
    def loaded(self):
        return self.db is not None and bool(self.sha)

    @property
    def categories(self):
        cats = list(self.db.keys()) if self.db else []
        return cats or list(functions.DEFAULT_CATEGORIES)

    @property
    def total(self):
        return sum(len(v) for v in self.db.values()) if self.db else 0

    def load(self):
        data, sha = functions.github_get_json(self.get_token() or None)
        if not isinstance(data, dict):
            raise ValueError("El archivo de recetas no tiene el formato esperado.")
        self.db = {cat: [functions.normalize_recipe(r) for r in recipes]
                   for cat, recipes in data.items()}
        self.sha = sha

    def _require_loaded(self):
        if not self.loaded:
            raise functions.GitHubError("La base de datos no está cargada.")

    def _commit(self, new_db, message):
        self._require_loaded()
        new_sha = functions.github_put_json(self.get_token(), new_db, self.sha, message)
        self.db, self.sha = new_db, new_sha

    def find_duplicate(self, category, name, ignore=None):
        for i, r in enumerate(self.db.get(category, [])):
            if (category, i) != ignore and r["nombre"].strip().lower() == name.strip().lower():
                return True
        return False

    def add(self, category, recipe):
        self._require_loaded()
        new_db = copy.deepcopy(self.db)
        new_db.setdefault(category, []).append(recipe)
        self._commit(new_db, f"Añadir receta: {recipe['nombre']} ({category})")

    def update(self, old_category, index, new_category, recipe):
        self._require_loaded()
        new_db = copy.deepcopy(self.db)
        if new_category == old_category:
            new_db[old_category][index] = recipe
        else:
            del new_db[old_category][index]
            new_db.setdefault(new_category, []).append(recipe)
        self._commit(new_db, f"Editar receta: {recipe['nombre']} ({new_category})")

    def delete(self, category, index):
        self._require_loaded()
        new_db = copy.deepcopy(self.db)
        name = new_db[category][index]["nombre"]
        del new_db[category][index]
        self._commit(new_db, f"Eliminar receta: {name} ({category})")


def validate_recipe(name, page, ingredients):
    """Devuelve (receta_normalizada_parcial, lista_de_errores)."""
    errors = []
    if not name.strip():
        errors.append("El nombre del plato es obligatorio.")
    if page.strip() and not page.strip().isdigit():
        errors.append("La página debe ser un número.")
    clean = []
    for i, ing in enumerate(ingredients, 1):
        if not ing["nombre"]:
            if ing["cantidad"] or ing["unidad"]:
                errors.append(f"Ingrediente {i}: falta el nombre.")
            continue
        qty = ing["cantidad"].replace(",", ".")
        if qty and functions.parse_quantity(qty) is None:
            errors.append(f"«{ing['nombre']}»: la cantidad debe ser un número (ej. 2 o 0.5).")
        clean.append({"nombre": ing["nombre"], "cantidad": qty, "unidad": ing["unidad"]})
    if not clean and not errors:
        errors.append("Añade al menos un ingrediente.")
    return clean, errors


# ===========================================================================
# WIDGETS
# ===========================================================================
class UnitButton(RoundButton):
    """Botón que va cambiando entre las unidades disponibles al pulsarlo."""

    def __init__(self, unit="", **kwargs):
        super().__init__(variant="secondary", size_hint=(None, None), size=(dp(64), dp(48)),
                         font_size=sp(14), **kwargs)
        # Una unidad antigua que no esté en la lista se conserva como opción extra.
        self.choices = UNIT_CHOICES + ([unit] if unit and unit not in UNIT_CHOICES else [])
        self.unit = unit or ""
        self._paint()
        self.bind(on_release=self._next)

    def _next(self, *_):
        self.unit = self.choices[(self.choices.index(self.unit) + 1) % len(self.choices)]
        self._paint()

    def _paint(self):
        self.text = self.unit or "-"

    def value(self):
        return self.unit


class IngredientRow(BoxLayout):
    def __init__(self, on_remove, data=None, **kwargs):
        super().__init__(size_hint_y=None, height=dp(48), spacing=dp(6), **kwargs)
        data = data or {}
        self.name = Field(hint_text="Ingrediente", text=data.get("nombre", ""))
        self.qty = Field(hint_text="Cant.", text=functions.format_quantity(data.get("cantidad", "")),
                         size_hint_x=None, width=dp(70), input_filter="float")
        self.unit = UnitButton(data.get("unidad", ""))
        rm = IconButton("x", variant="danger", size=dp(40), pos_hint={"center_y": 0.5})
        rm.bind(on_release=lambda *_: on_remove(self))
        for w in (self.name, self.qty, self.unit, rm):
            self.add_widget(w)

    def get(self):
        return {"nombre": self.name.text.strip(), "cantidad": self.qty.text.strip(),
                "unidad": self.unit.value()}


class RecipePicker(ModalView):
    """Diálogo para buscar y elegir la receta que se va a editar."""

    def __init__(self, logic, on_pick, **kwargs):
        super().__init__(size_hint=(0.94, 0.86), background="", background_color=(0, 0, 0, 0),
                         overlay_color=(0.13, 0.09, 0.06, 0.55), **kwargs)
        self.logic, self.on_pick = logic, on_pick
        card = Card(padding=dp(16), spacing=dp(10))
        head = BoxLayout(size_hint_y=None, height=dp(42))
        head.add_widget(title_label("Elegir receta", size=19))
        close = IconButton("x", size=dp(40))
        close.bind(on_release=lambda *_: self.dismiss())
        head.add_widget(close)
        card.add_widget(head)
        self.search = Field(hint_text="Buscar por nombre...")
        self.search.bind(text=lambda *_: self.refresh())
        card.add_widget(self.search)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.list.bind(minimum_height=self.list.setter("height"))
        scroll.add_widget(self.list)
        card.add_widget(scroll)
        self.add_widget(card)
        self.refresh()

    def refresh(self):
        q = self.search.text.strip().lower()
        self.list.clear_widgets()
        for cat, recipes in self.logic.db.items():
            matches = [(i, r) for i, r in enumerate(recipes) if q in r["nombre"].lower()]
            if not matches:
                continue
            self.list.add_widget(AutoLabel(text=cat.upper(), bold=True, font_size=sp(12),
                                           color=C.ACCENT, height=dp(26)))
            for i, r in matches:
                btn = RoundButton(text=r["nombre"], variant="ghost", height=dp(46), bold=False,
                                  halign="left", valign="middle", shorten=True,
                                  padding=[dp(14), 0])
                btn.bind(size=lambda b, s: setattr(b, "text_size", s))
                btn.bind(on_release=lambda *_b, c=cat, idx=i: self._pick(c, idx))
                self.list.add_widget(btn)

    def _pick(self, cat, idx):
        self.dismiss()
        self.on_pick(cat, idx)


# ===========================================================================
# PANTALLA PRINCIPAL
# ===========================================================================
class ManagerScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.logic = app.logic
        self.mode = "add"
        self.editing = None      # (categoría, índice) en modo edición
        self.category = ""

        btn_settings = RoundButton(text="Salir", variant="secondary", size_hint_x=None,
                                   width=dp(84), height=dp(40), font_size=sp(14))
        btn_settings.bind(on_release=lambda *_: self.logout())
        self.bar = AppBar("Gestor de Recetas", "Cargando...", logo=LOGO, actions=[btn_settings])
        self.add_widget(self.bar)

        self.tabs = TabBar(["Nueva receta", "Editar receta"], self._on_tab, group="mgr_tabs",
                           padding=[dp(16), 0])
        self.add_widget(spacer(dp(12)))
        self.add_widget(self.tabs)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.form = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12),
                              padding=[dp(16), dp(14), dp(16), dp(30)])
        self.form.bind(minimum_height=self.form.setter("height"))
        self.scroll.add_widget(self.form)
        self.add_widget(self.scroll)

        self.bottom = BoxLayout(size_hint_y=None, height=dp(76), padding=[dp(16), dp(12)],
                                spacing=dp(10))
        from kivy.graphics import Color, Rectangle
        with self.bottom.canvas.before:
            Color(*C.SURFACE)
            self._bb = Rectangle()
        self.bottom.bind(pos=lambda *_: setattr(self._bb, "pos", self.bottom.pos),
                         size=lambda *_: setattr(self._bb, "size", self.bottom.size))
        self.btn_secondary = RoundButton(text="Limpiar", variant="ghost", size_hint_x=0.4)
        self.btn_secondary.bind(on_release=lambda *_: self._secondary())
        self.btn_save = RoundButton(text="Guardar receta")
        self.btn_save.bind(on_release=lambda *_: self.save())
        self.bottom.add_widget(self.btn_secondary)
        self.bottom.add_widget(self.btn_save)
        self.add_widget(self.bottom)
        self.show_message("Cargando la base de datos...")

    # --- estados -----------------------------------------------------------
    def show_message(self, text, retry=False):
        self.form.clear_widgets()
        self.form.add_widget(empty_state(text, LOGO))
        if retry:
            btn = RoundButton(text="Reintentar", variant="ghost")
            btn.bind(on_release=lambda *_: self.app.load_data())
            self.form.add_widget(btn)
        self.btn_save.disabled = True
        self.btn_secondary.disabled = True

    def refresh_header(self):
        who = f"@{self.logic.user}" if self.logic.user else "administrador"
        self.bar.set_subtitle(f"{self.logic.total} recetas · {who}")

    # --- pestañas ----------------------------------------------------------
    def _on_tab(self, name):
        self.change_mode("add" if name.startswith("Nueva") else "edit")

    def change_mode(self, mode):
        self.mode = mode
        self.tabs.select("Nueva receta" if mode == "add" else "Editar receta")
        self.editing = None
        if mode == "add":
            self.btn_secondary.text = "Limpiar"
            self.btn_save.text = "Guardar receta"
            self.build_form()
        else:
            self.btn_secondary.text = "Eliminar"
            self.btn_save.text = "Guardar cambios"
            self.build_edit_start()

    def build_edit_start(self):
        self.form.clear_widgets()
        self.form.add_widget(empty_state("Elige la receta que quieres modificar.", LOGO))
        btn = RoundButton(text="Buscar receta")
        btn.bind(on_release=lambda *_: self.pick())
        self.form.add_widget(btn)
        self.btn_save.disabled = True
        self.btn_secondary.disabled = True

    def pick(self):
        if self.logic.loaded:
            RecipePicker(self.logic, self.load_recipe).open()

    def load_recipe(self, category, index):
        self.editing = (category, index)
        self.build_form(self.logic.db[category][index], category)

    # --- formulario ----------------------------------------------------------
    def build_form(self, recipe=None, category=None):
        recipe = recipe or {}
        f = self.form
        f.clear_widgets()
        self.btn_save.disabled = not self.logic.loaded
        self.btn_secondary.disabled = False

        if self.mode == "edit":
            head = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            head.add_widget(AutoLabel(text=f"Editando: {recipe.get('nombre', '')}", bold=True,
                                      color=C.ACCENT, shorten=True))
            other = RoundButton(text="Cambiar", variant="ghost", size_hint_x=None,
                                width=dp(96), height=dp(40), font_size=sp(14))
            other.bind(on_release=lambda *_: self.pick())
            head.add_widget(other)
            f.add_widget(head)

        # Categoría
        self.category = category or self.category or self.logic.categories[0]
        f.add_widget(title_label("Categoría", size=15))
        cat_scroll = ScrollView(do_scroll_y=False, size_hint_y=None, height=dp(40), bar_width=0)
        row = BoxLayout(size_hint_x=None, spacing=dp(8))
        row.bind(minimum_width=row.setter("width"))
        for cat in self.logic.categories:
            chip = Chip(text=cat, group="mgr_cat", size_hint_x=None,
                        state="down" if cat == self.category else "normal")
            chip.texture_update()
            chip.width = chip.texture_size[0] + dp(28)
            chip.bind(on_release=lambda c: setattr(self, "category", c.text))
            row.add_widget(chip)
        cat_scroll.add_widget(row)
        f.add_widget(cat_scroll)

        # Datos básicos
        card = Card(size_hint_y=None, spacing=dp(10))
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(title_label("Datos del plato", size=15))
        self.f_name = Field(hint_text="Nombre del plato", text=recipe.get("nombre", ""))
        self.f_page = Field(hint_text="Página del libro (opcional)", input_filter="int",
                            text=functions.format_page(recipe.get("pagina", "")))
        card.add_widget(self.f_name)
        card.add_widget(self.f_page)
        filtros = recipe.get("filtros") or {}
        flt = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        self.f_veg = TickBox(active=bool(filtros.get("vegetariano")), pos_hint={"center_y": 0.5})
        self.f_gf = TickBox(active=bool(filtros.get("gluten_free")), pos_hint={"center_y": 0.5})
        flt.add_widget(self.f_veg)
        flt.add_widget(AutoLabel(text="Vegetariano", pos_hint={"center_y": 0.5}))
        flt.add_widget(self.f_gf)
        flt.add_widget(AutoLabel(text="Sin gluten", pos_hint={"center_y": 0.5}))
        card.add_widget(flt)
        f.add_widget(card)

        # Ingredientes
        ing_card = Card(size_hint_y=None, spacing=dp(8))
        ing_card.bind(minimum_height=ing_card.setter("height"))
        ing_card.add_widget(title_label("Ingredientes", size=15))
        ing_card.add_widget(muted_label("Pulsa la unidad para cambiarla: uds, g, mL, cuch."))
        self.ing_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8))
        self.ing_box.bind(minimum_height=self.ing_box.setter("height"))
        ing_card.add_widget(self.ing_box)
        for ing in recipe.get("ingredientes", []) or [None]:
            self.add_ingredient(ing)
        add = RoundButton(text="+ Añadir ingrediente", variant="secondary", height=dp(44))
        add.bind(on_release=lambda *_: self.add_ingredient())
        ing_card.add_widget(add)
        f.add_widget(ing_card)

        # Elaboración
        el = Card(size_hint_y=None, spacing=dp(10))
        el.bind(minimum_height=el.setter("height"))
        el.add_widget(title_label("Elaboración", size=15))
        self.f_elab = Field(hint_text="Pasos de la receta...", multiline=True, height=dp(220),
                            text=recipe.get("elaboracion", ""))
        el.add_widget(self.f_elab)
        f.add_widget(el)
        self.scroll.scroll_y = 1

    def add_ingredient(self, data=None):
        self.ing_box.add_widget(IngredientRow(self.remove_ingredient, data))

    def remove_ingredient(self, row):
        self.ing_box.remove_widget(row)
        if not self.ing_box.children:
            self.add_ingredient()

    def collect(self):
        ings = [row.get() for row in reversed(self.ing_box.children)]
        clean, errors = validate_recipe(self.f_name.text, self.f_page.text, ings)
        recipe = {
            "nombre": self.f_name.text.strip(),
            "pagina": self.f_page.text.strip(),
            "elaboracion": self.f_elab.text.strip(),
            "filtros": {"vegetariano": self.f_veg.active, "gluten_free": self.f_gf.active},
            "ingredientes": clean,
        }
        return recipe, errors

    # --- acciones ------------------------------------------------------------
    def _secondary(self):
        if self.mode == "add":
            confirm("¿Limpiar el formulario?", "Se borrará lo que has escrito.",
                    lambda: self.build_form(), yes_text="Limpiar")
        elif self.editing:
            cat, idx = self.editing
            name = self.logic.db[cat][idx]["nombre"]
            confirm("¿Eliminar receta?",
                    f"Se eliminará «{name}» de {cat} en GitHub. No se puede deshacer.",
                    lambda: self.app.run_remote(lambda: self.logic.delete(cat, idx),
                                                "Receta eliminada", self._after_delete),
                    yes_text="Eliminar")

    def _after_delete(self):
        self.change_mode("edit")

    def save(self):
        if not self.logic.loaded:
            show_info("Sin datos", "Primero hay que cargar la base de datos.")
            return
        if not self.logic.get_token():
            self.app.lock("Tu sesión ha caducado. Vuelve a introducir el token.")
            return
        recipe, errors = self.collect()
        if errors:
            show_info("Revisa la receta", "\n".join(errors))
            return
        cat = self.category
        if self.mode == "add":
            if self.logic.find_duplicate(cat, recipe["nombre"]):
                show_info("Receta repetida", f"Ya existe «{recipe['nombre']}» en {cat}.")
                return
            self.app.run_remote(lambda: self.logic.add(cat, recipe), "Receta añadida",
                                lambda: self.build_form())
        else:
            if not self.editing:
                return
            old_cat, idx = self.editing
            if self.logic.find_duplicate(cat, recipe["nombre"], ignore=(old_cat, idx)):
                show_info("Receta repetida", f"Ya existe «{recipe['nombre']}» en {cat}.")
                return

            def done():
                new_idx = idx if cat == old_cat else len(self.logic.db[cat]) - 1
                self.load_recipe(cat, new_idx)
            self.app.run_remote(lambda: self.logic.update(old_cat, idx, cat, recipe),
                                "Cambios guardados", done)

    def logout(self):
        confirm("¿Cerrar sesión?", "Se borrará el token de este dispositivo y la app quedará bloqueada.",
                self.app.logout, yes_text="Cerrar sesión")


class LockScreen(BoxLayout):
    """Pantalla de bloqueo: sólo el administrador (token con permiso de escritura) puede entrar."""

    def __init__(self, app, message="", **kwargs):
        super().__init__(orientation="vertical", padding=[dp(24), dp(40), dp(24), dp(24)],
                         spacing=dp(16), **kwargs)
        self.app = app
        from kivy.uix.image import Image
        if asset_path(LOGO):
            self.add_widget(Image(source=asset_path(LOGO), size_hint_y=None, height=dp(150),
                                  fit_mode="contain"))
        t = title_label("Gestor de Recetas", size=24)
        t.halign = "center"
        self.add_widget(t)
        info = muted_label("Acceso restringido al administrador del recetario.\n"
                           "Introduce tu token personal de GitHub con permiso de escritura "
                           "sobre alherca25/BaseDatosRecetas.", size=14)
        info.halign = "center"
        self.add_widget(info)
        self.field = Field(hint_text="github_pat_...", password=True)
        self.add_widget(self.field)
        from kivy.uix.label import Label
        self.error = Label(text=message, color=C.DANGER, halign="center", valign="middle",
                           font_size=sp(14), size_hint_y=None, height=dp(36))
        self.error.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.add_widget(self.error)
        self.btn = RoundButton(text="Entrar")
        self.btn.bind(on_release=lambda *_: self.submit())
        self.add_widget(self.btn)
        self.add_widget(Widget())
        foot = muted_label("El token se guarda sólo en este dispositivo. "
                           "Pulsa «Salir» dentro de la app para borrarlo.", size=12)
        foot.halign = "center"
        self.add_widget(foot)

    def submit(self):
        token = self.field.text.strip()
        if not token:
            self.error.text = "Introduce un token."
            return
        self.error.text = ""
        self.btn.disabled = True
        self.app.try_unlock(token, on_fail=self._failed)

    def _failed(self, msg):
        self.btn.disabled = False
        self.error.text = msg


class MvRecipeApp(App):
    title = "Gestor de Recetas"

    def build(self):
        setup_window()
        self.icon = asset_path(LOGO)
        self.logic = ManagerLogic(user_dir())
        self.root_box = BoxLayout()
        self.screen = None
        token = self.logic.get_token()
        if token:
            self._show(LockScreen(self, "Comprobando acceso..."))
            self.try_unlock(token, on_fail=lambda msg: self.lock(msg), busy=False)
        else:
            self.lock()
        return self.root_box

    def _show(self, widget):
        self.root_box.clear_widgets()
        self.root_box.add_widget(widget)

    def lock(self, message=""):
        self.screen = None
        self._show(LockScreen(self, message))

    def logout(self):
        self.logic.delete_token()
        self.lock("Sesión cerrada.")

    def try_unlock(self, token, on_fail, busy=True):
        def ok():
            self.screen = ManagerScreen(self)
            self._show(self.screen)
            self.load_data()
        self._run(lambda: self.logic.unlock(token), ok, lambda msg, _e=None: on_fail(msg), busy=busy)

    def load_data(self):
        self.screen.show_message("Cargando la base de datos...")
        self._run(self.logic.load, self._loaded, self._load_failed, busy=False)

    def _loaded(self):
        self.screen.refresh_header()
        self.screen.change_mode(self.screen.mode)

    def _load_failed(self, msg, _exc=None):
        self.screen.bar.set_subtitle("Sin conexión")
        self.screen.show_message(f"No se pudo cargar la base de datos.\n{msg}\n\n"
                                 "Por seguridad no se puede editar sin ella.", retry=True)

    def run_remote(self, action, ok_text, after=None):
        """Ejecuta una operación contra GitHub en segundo plano."""
        def ok():
            self.screen.refresh_header()
            Toast.show(ok_text)
            if after:
                after()

        def fail(msg, exc=None):
            if isinstance(exc, functions.GitHubConflict):
                confirm("Cambios en GitHub", msg + "\n\nTu cambio no se ha guardado.",
                        self.load_data, yes_text="Recargar", variant="primary")
            else:
                show_info("No se pudo guardar", msg)
        self._run(action, ok, fail)

    def _run(self, action, on_ok, on_fail, busy=True):
        spinner = Busy("Conectando con GitHub...") if busy else None
        if spinner:
            spinner.open()

        def worker():
            try:
                action()
                Clock.schedule_once(lambda *_: (spinner and spinner.dismiss(), on_ok()), 0)
            except Exception as exc:
                msg, err = str(exc), exc
                def report(*_):
                    if spinner:
                        spinner.dismiss()
                    on_fail(msg, err)
                Clock.schedule_once(report, 0)
        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    MvRecipeApp().run()
