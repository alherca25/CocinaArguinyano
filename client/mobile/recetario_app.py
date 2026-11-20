"""
Recetario «Cocina Rápida» — app móvil (Kivy / Android).

Pantallas:
  - Planificar: filtro + cuántos platos de cada categoría.
  - Mi menú:    platos elegidos (pestaña Platos) y lista de la compra (pestaña Compra).
  - Receta:     detalle de una receta.
  - Recetario:  buscador de todas las recetas.
"""
import json
import os
import sys
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

# Desde el repositorio, los módulos comunes están en ../../shared; en el APK/.exe van junto a este archivo.
_SHARED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared")
if os.path.isdir(_SHARED):
    sys.path.insert(0, os.path.abspath(_SHARED))

import functions
from mobile_ui import (AppBar, AutoLabel, C, Card, Chip, Field, IconButton, RoundButton,
                       Stepper, TabBar, TickBox, Toast, asset_path, confirm, empty_state,
                       muted_label, recipe_tags, setup_window, share_text, show_info,
                       spacer, tag_row, title_label, user_dir)

LOGO = "icon_main.png"
FILTER_LABELS = {"Todo": "Todo", "Vegetariano": "Vegetariano", "Gluten Free": "Sin gluten"}


# ===========================================================================
# LÓGICA (sin widgets)
# ===========================================================================
class PlannerLogic:
    """Estado de la app: recetas, selección, menú generado y compra marcada."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.db = {}
        self.source = ""
        self.active_filter = "Todo"
        self.selection = {}        # {categoría: cantidad}
        self.menu = []             # recetas elegidas (con clave "Tipo")
        self.menu_date = ""
        self.checked = set()       # claves de ingredientes ya comprados
        self.load_state()

    # --- persistencia -----------------------------------------------------
    @property
    def cache_path(self):
        return os.path.join(self.data_dir, "CocinaArguinyano.json")

    @property
    def state_path(self):
        return os.path.join(self.data_dir, "estado.json")

    def load_state(self):
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                st = json.load(f)
            self.active_filter = st.get("filter", "Todo")
            self.selection = {k: int(v) for k, v in st.get("selection", {}).items()}
            self.menu = st.get("menu", [])
            self.menu_date = st.get("menu_date", "")
            self.checked = set(st.get("checked", []))
        except (OSError, ValueError):
            pass

    def save_state(self):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump({"filter": self.active_filter, "selection": self.selection,
                           "menu": self.menu, "menu_date": self.menu_date,
                           "checked": sorted(self.checked)}, f, ensure_ascii=False)
        except OSError as exc:
            print(f"No se pudo guardar el estado: {exc}")

    # --- recetas ----------------------------------------------------------
    def load_recipes(self):
        db, self.source = functions.load_recipes_with_cache(self.cache_path, [functions.LOCAL_DB])
        self.db = {cat: [functions.normalize_recipe(r) for r in recipes]
                   for cat, recipes in db.items()}
        self.clamp_selection()

    @property
    def categories(self):
        return list(self.db.keys())

    @property
    def total_recipes(self):
        return sum(len(v) for v in self.db.values())

    def available(self, category):
        return functions.count_available(self.db, category, self.active_filter)

    def set_filter(self, value):
        self.active_filter = value
        return self.clamp_selection()

    def clamp_selection(self):
        """Ajusta las cantidades al máximo disponible con el filtro. Devuelve lo ajustado."""
        adjusted = []
        for cat in list(self.selection):
            if cat not in self.db:
                del self.selection[cat]
                continue
            maximum = self.available(cat)
            if self.selection[cat] > maximum:
                self.selection[cat] = maximum
                adjusted.append(cat)
            if self.selection[cat] <= 0:
                del self.selection[cat]
        return adjusted

    def set_amount(self, category, qty):
        if qty > 0:
            self.selection[category] = min(qty, self.available(category))
        else:
            self.selection.pop(category, None)

    @property
    def total_selected(self):
        return sum(self.selection.values())

    # --- menú -------------------------------------------------------------
    def generate_menu(self):
        if not self.selection:
            raise ValueError("Elige al menos un plato.")
        self.menu = functions.build_menu(self.db, self.selection, self.active_filter)
        self.menu_date = datetime.now().strftime("%d/%m/%Y")
        self.checked = set()
        self.save_state()

    def reroll(self, index):
        """Cambia un plato del menú por otro de la misma categoría que no esté ya."""
        dish = self.menu[index]
        cat = dish.get("Tipo", "")
        used = {d["nombre"] for d in self.menu if d.get("Tipo") == cat}
        options = [r for r in functions.filter_recipes(self.db.get(cat, []), self.active_filter)
                   if r["nombre"] not in used]
        if not options:
            return False
        import random
        new = dict(random.choice(options))
        new["Tipo"] = cat
        self.menu[index] = new
        self.save_state()
        return True

    def shopping_list(self):
        return functions.aggregate_ingredients(self.menu)

    def toggle_checked(self, key, value):
        (self.checked.add if value else self.checked.discard)(key)
        self.save_state()


# ===========================================================================
# PANTALLAS
# ===========================================================================
def scroll_list(padding=None):
    scroll = ScrollView(do_scroll_x=False, bar_width=dp(4), bar_color=C.INK_SOFT)
    box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10),
                    padding=padding if padding is not None else [dp(16), dp(14), dp(16), dp(24)])
    box.bind(minimum_height=box.setter("height"))
    scroll.add_widget(box)
    return scroll, box


def bottom_bar(*widgets):
    bar = BoxLayout(size_hint_y=None, height=dp(76), padding=[dp(16), dp(12)], spacing=dp(10))
    from kivy.graphics import Color, Rectangle
    with bar.canvas.before:
        Color(*C.SURFACE)
        rect = Rectangle()
        Color(*C.BORDER)
        line = Rectangle()
    def redraw(*_):
        rect.pos, rect.size = bar.pos, bar.size
        line.pos, line.size = (bar.x, bar.top - 1), (bar.width, 1)
    bar.bind(pos=redraw, size=redraw)
    for w in widgets:
        bar.add_widget(w)
    return bar


class PlannerScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(name="planner", **kwargs)
        self.app = app
        root = BoxLayout(orientation="vertical")

        self.btn_book = RoundButton(text="Recetario", variant="secondary", size_hint_x=None,
                                    width=dp(108), height=dp(40), font_size=sp(14))
        self.btn_book.bind(on_release=lambda *_: app.open_browse())
        self.bar = AppBar("Cocina Rápida", "Cargando recetas...", logo=LOGO,
                          actions=[self.btn_book])
        root.add_widget(self.bar)

        scroll, self.body = scroll_list()
        root.add_widget(scroll)

        self.lbl_total = AutoLabel(text="", bold=True, size_hint_x=0.42)
        self.btn_menu = RoundButton(text="Generar menú")
        self.btn_menu.bind(on_release=lambda *_: app.generate_menu())
        root.add_widget(bottom_bar(self.lbl_total, self.btn_menu))
        self.add_widget(root)
        self.steppers = {}
        self.show_loading()

    def show_loading(self):
        self.body.clear_widgets()
        self.body.add_widget(empty_state("Descargando el recetario...", LOGO))
        self.btn_menu.disabled = True

    def show_error(self, message):
        self.body.clear_widgets()
        self.body.add_widget(empty_state(message, LOGO))
        retry = RoundButton(text="Reintentar", variant="ghost")
        retry.bind(on_release=lambda *_: self.app.load_data())
        self.body.add_widget(retry)

    def build(self):
        logic = self.app.logic
        self.body.clear_widgets()
        self.steppers = {}

        # Último menú
        if logic.menu:
            card = Card(size_hint_y=None, height=dp(86), orientation="horizontal",
                        fill=C.PEACH, border=False)
            texts = BoxLayout(orientation="vertical")
            texts.add_widget(title_label("Tu último menú", size=16))
            texts.add_widget(muted_label(f"{len(logic.menu)} platos · {logic.menu_date}"))
            card.add_widget(texts)
            btn = RoundButton(text="Abrir", variant="primary", size_hint_x=None, width=dp(92),
                              height=dp(44), pos_hint={"center_y": 0.5})
            btn.bind(on_release=lambda *_: self.app.open_menu())
            card.add_widget(btn)
            self.body.add_widget(card)

        # Filtro
        self.body.add_widget(title_label("Tipo de dieta", size=17))
        chips = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        for value in functions.FILTERS:
            chip = Chip(text=FILTER_LABELS[value], group="filter",
                        state="down" if value == logic.active_filter else "normal")
            chip.bind(on_release=lambda c, v=value: self.app.change_filter(v))
            chips.add_widget(chip)
        self.body.add_widget(chips)

        # Categorías
        self.body.add_widget(spacer(dp(4)))
        self.body.add_widget(title_label("¿Cuántos platos de cada tipo?", size=17))
        for cat in logic.categories:
            card = Card(orientation="horizontal", size_hint_y=None, height=dp(74),
                        padding=[dp(16), dp(10)])
            texts = BoxLayout(orientation="vertical", spacing=dp(2))
            texts.add_widget(Widget())
            texts.add_widget(AutoLabel(text=cat, bold=True, font_size=sp(16)))
            avail = logic.available(cat)
            texts.add_widget(muted_label(f"{avail} disponibles" if avail else "Ninguna con este filtro"))
            texts.add_widget(Widget())
            card.add_widget(texts)
            stepper = Stepper(on_change=lambda v, c=cat: self.app.change_amount(c, v),
                              pos_hint={"center_y": 0.5})
            stepper.maximum = avail
            stepper.value = logic.selection.get(cat, 0)
            self.steppers[cat] = stepper
            card.add_widget(stepper)
            self.body.add_widget(card)
        self.update_total()

    def update_total(self):
        total = self.app.logic.total_selected
        self.lbl_total.text = f"{total} plato{'s' if total != 1 else ''}\nseleccionado{'s' if total != 1 else ''}"
        self.btn_menu.disabled = total == 0


class MenuScreen(Screen):
    TABS = ["Platos", "Compra"]

    def __init__(self, app, **kwargs):
        super().__init__(name="menu", **kwargs)
        self.app = app
        self.tab = "Platos"
        root = BoxLayout(orientation="vertical")
        self.bar = AppBar("Mi menú", "", on_back=app.go_home)
        root.add_widget(self.bar)
        self.tabs = TabBar(self.TABS, self.select_tab, group="menu_tabs",
                           padding=[dp(16), 0])
        root.add_widget(spacer(dp(12)))
        root.add_widget(self.tabs)
        scroll, self.body = scroll_list()
        self.scroll = scroll
        root.add_widget(scroll)

        self.btn_share = RoundButton(text="Compartir", variant="primary")
        self.btn_share.bind(on_release=lambda *_: self.share())
        self.btn_new = RoundButton(text="Nuevo menú", variant="ghost")
        self.btn_new.bind(on_release=lambda *_: app.go_home())
        root.add_widget(bottom_bar(self.btn_new, self.btn_share))
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def select_tab(self, name):
        self.tab = name
        self.tabs.select(name)
        self.refresh()
        self.scroll.scroll_y = 1

    def refresh(self):
        logic = self.app.logic
        self.bar.set_subtitle(f"{len(logic.menu)} platos · {logic.menu_date}")
        self.body.clear_widgets()
        if not logic.menu:
            self.body.add_widget(empty_state("Todavía no has generado ningún menú.", LOGO))
            return
        if self.tab == "Platos":
            self._build_dishes()
        else:
            self._build_shopping()

    def _build_dishes(self):
        logic = self.app.logic
        self.body.add_widget(muted_label("«Ver receta» muestra ingredientes y pasos. "
                                         "«Cambiar» elige otro plato de la misma categoría."))
        for idx, dish in enumerate(logic.menu):
            card = Card(size_hint_y=None, spacing=dp(8))
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(AutoLabel(text=dish["nombre"], bold=True, font_size=sp(17)))
            n_ing = len(dish.get("ingredientes", []))
            card.add_widget(tag_row(recipe_tags(dish) + [(f"{n_ing} ingredientes", "plain")]))
            row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
            swap = RoundButton(text="Cambiar", variant="ghost", height=dp(40), font_size=sp(14))
            swap.bind(on_release=lambda *_b, i=idx: self.reroll(i))
            see = RoundButton(text="Ver receta", variant="secondary", height=dp(40), font_size=sp(14))
            see.bind(on_release=lambda *_b, d=dish: self.app.open_recipe(d))
            row.add_widget(swap)
            row.add_widget(see)
            card.add_widget(row)
            self.body.add_widget(card)

    def reroll(self, index):
        if self.app.logic.reroll(index):
            self.refresh()
            Toast.show("Plato cambiado")
        else:
            show_info("Sin alternativas", "No hay más recetas de esta categoría con el filtro actual.")

    def _build_shopping(self):
        logic = self.app.logic
        items = logic.shopping_list()
        pending = [i for i in items if functions.item_key(i) not in logic.checked]
        done = [i for i in items if functions.item_key(i) in logic.checked]
        self.body.add_widget(muted_label(
            f"{len(pending)} por comprar · {len(done)} en el carro. "
            "Marca lo que ya tengas."))
        card = Card(size_hint_y=None, spacing=dp(2), padding=[dp(14), dp(8)])
        card.bind(minimum_height=card.setter("height"))
        for it in pending + done:
            card.add_widget(self._shopping_row(it))
        self.body.add_widget(card)
        if done:
            clear = RoundButton(text="Desmarcar todo", variant="flat", height=dp(42))
            clear.bind(on_release=lambda *_: self._uncheck_all())
            self.body.add_widget(clear)

    def _shopping_row(self, item):
        key = functions.item_key(item)
        checked = key in self.app.logic.checked
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
        box = TickBox(active=checked, pos_hint={"center_y": 0.5})
        name = item["nombre"]
        qty = " ".join(p for p in (item["cantidad"], item["unidad"]) if p)
        lbl = AutoLabel(text=f"[s]{name}[/s]" if checked else name, markup=True,
                        color=C.INK_SOFT if checked else C.INK, pos_hint={"center_y": 0.5})
        q = AutoLabel(text=qty, halign="right", bold=True, size_hint_x=0.38,
                      color=C.INK_SOFT if checked else C.ACCENT, pos_hint={"center_y": 0.5})
        box.bind(active=lambda _b, v, k=key: self._on_check(k, v))
        row.add_widget(box)
        row.add_widget(lbl)
        row.add_widget(q)
        return row

    def _on_check(self, key, value):
        self.app.logic.toggle_checked(key, value)
        Clock.schedule_once(lambda *_: self.refresh(), 0.15)

    def _uncheck_all(self):
        self.app.logic.checked = set()
        self.app.logic.save_state()
        self.refresh()

    def share(self):
        logic = self.app.logic
        if not logic.menu:
            return
        if self.tab == "Platos":
            text = functions.menu_to_text(logic.menu, f"Menú {logic.menu_date}")
        else:
            text = functions.shopping_to_text(logic.shopping_list(),
                                              f"Compra {logic.menu_date}", logic.checked)
        try:
            msg = share_text(text, subject=f"Cocina Rápida — {self.tab}")
            if msg:
                Toast.show(msg)
        except Exception as exc:
            show_info("No se pudo compartir", str(exc))


class RecipeScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(name="recipe", **kwargs)
        self.app = app
        self.back_to = "menu"
        root = BoxLayout(orientation="vertical")
        self.bar = AppBar("Receta", "", on_back=lambda: app.go(self.back_to, back=True))
        root.add_widget(self.bar)
        scroll, self.body = scroll_list()
        self.scroll = scroll
        root.add_widget(scroll)
        btn = RoundButton(text="Compartir receta", variant="secondary")
        btn.bind(on_release=lambda *_: self.share())
        root.add_widget(bottom_bar(btn))
        self.add_widget(root)
        self.recipe = None

    def show(self, recipe, back_to):
        self.recipe = recipe
        self.back_to = back_to
        self.bar.set_title(recipe.get("Tipo") or "Receta")
        self.bar.set_subtitle("Recetario Cocina Rápida")
        b = self.body
        b.clear_widgets()
        b.add_widget(title_label(recipe["nombre"], size=22))
        b.add_widget(tag_row(recipe_tags(recipe, include_category=False)))

        ings = Card(size_hint_y=None, spacing=dp(6))
        ings.bind(minimum_height=ings.setter("height"))
        ings.add_widget(title_label("Ingredientes", size=17))
        for ing in recipe.get("ingredientes", []):
            row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            qty = " ".join(p for p in (functions.format_quantity(ing.get("cantidad", "")),
                                       ing.get("unidad", "")) if p)
            row.add_widget(AutoLabel(text=ing["nombre"]))
            row.add_widget(AutoLabel(text=qty, halign="right", bold=True, color=C.ACCENT,
                                     size_hint_x=0.4))
            ings.add_widget(row)
        b.add_widget(ings)

        elab = Card(size_hint_y=None, spacing=dp(10))
        elab.bind(minimum_height=elab.setter("height"))
        elab.add_widget(title_label("Elaboración", size=17))
        text = recipe.get("elaboracion", "").strip() or "Sin elaboración registrada."
        for i, paragraph in enumerate(p for p in text.split("\n") if p.strip()):
            elab.add_widget(AutoLabel(text=paragraph.strip(), font_size=sp(15), line_height=1.25))
        b.add_widget(elab)
        self.scroll.scroll_y = 1

    def share(self):
        if self.recipe:
            msg = share_text(functions.menu_to_text([self.recipe], self.recipe["nombre"]))
            if msg:
                Toast.show(msg)


class BrowseScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(name="browse", **kwargs)
        self.app = app
        self.category = "Todas"
        root = BoxLayout(orientation="vertical")
        self.bar = AppBar("Recetario", "", on_back=app.go_home)
        root.add_widget(self.bar)
        top = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(112),
                        padding=[dp(16), dp(12), dp(16), 0], spacing=dp(10))
        self.search = Field(hint_text="Buscar receta o ingrediente...")
        self.search.bind(text=lambda *_: self._schedule())
        top.add_widget(self.search)
        cat_scroll = ScrollView(do_scroll_y=False, size_hint_y=None, height=dp(40), bar_width=0)
        self.cat_row = BoxLayout(size_hint_x=None, spacing=dp(8))
        self.cat_row.bind(minimum_width=self.cat_row.setter("width"))
        cat_scroll.add_widget(self.cat_row)
        top.add_widget(cat_scroll)
        root.add_widget(top)
        scroll, self.body = scroll_list()
        root.add_widget(scroll)
        self.add_widget(root)
        self._ev = None

    def on_pre_enter(self, *_):
        self.cat_row.clear_widgets()
        for cat in ["Todas"] + self.app.logic.categories:
            chip = Chip(text=cat, group="browse_cat", size_hint_x=None,
                        state="down" if cat == self.category else "normal")
            chip.texture_update()
            chip.width = chip.texture_size[0] + dp(28)
            chip.bind(on_release=lambda c: self._set_category(c.text))
            self.cat_row.add_widget(chip)
        self.refresh()

    def _set_category(self, cat):
        self.category = cat
        self.refresh()

    def _schedule(self):
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_once(lambda *_: self.refresh(), 0.25)

    def refresh(self):
        logic = self.app.logic
        query = self.search.text.strip().lower()
        results = []
        for cat, recipes in logic.db.items():
            if self.category not in ("Todas", cat):
                continue
            for r in functions.filter_recipes(recipes, logic.active_filter):
                haystack = " ".join([r["nombre"]] + [i["nombre"] for i in r["ingredientes"]]).lower()
                if query in haystack:
                    results.append(dict(r, Tipo=cat))
        self.bar.set_subtitle(f"{len(results)} recetas · filtro: {FILTER_LABELS[logic.active_filter]}")
        self.body.clear_widgets()
        if not results:
            self.body.add_widget(empty_state("No hay recetas que coincidan.", LOGO))
            return
        for r in results[:150]:
            card = Card(size_hint_y=None, spacing=dp(6), padding=[dp(14), dp(12)])
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(AutoLabel(text=r["nombre"], bold=True, font_size=sp(16)))
            card.add_widget(tag_row(recipe_tags(r)))
            card.bind(on_touch_up=lambda w, t, rec=r: self._tap(w, t, rec))
            self.body.add_widget(card)

    def _tap(self, widget, touch, recipe):
        if widget.collide_point(*touch.pos) and not touch.is_mouse_scrolling \
                and abs(touch.oy - touch.y) < dp(10):
            self.app.open_recipe(recipe, back_to="browse")


# ===========================================================================
# APP
# ===========================================================================
class CocinaApp(App):
    title = "Cocina Rápida"

    def build(self):
        setup_window()
        self.icon = asset_path(LOGO)
        self.logic = PlannerLogic(user_dir())
        self.sm = ScreenManager(transition=SlideTransition(duration=0.22))
        self.planner = PlannerScreen(self)
        self.menu_screen = MenuScreen(self)
        self.recipe_screen = RecipeScreen(self)
        self.browse_screen = BrowseScreen(self)
        for s in (self.planner, self.menu_screen, self.recipe_screen, self.browse_screen):
            self.sm.add_widget(s)
        from kivy.core.window import Window
        Window.bind(on_keyboard=self._on_key)
        self.load_data()
        return self.sm

    # --- navegación ---------------------------------------------------------
    def go(self, name, back=False):
        self.sm.transition.direction = "right" if back else "left"
        self.sm.current = name

    def go_home(self):
        self.go("planner", back=True)
        self.planner.build()

    def open_menu(self):
        self.go("menu")

    def open_browse(self):
        if self.logic.db:
            self.go("browse")

    def open_recipe(self, recipe, back_to="menu"):
        self.recipe_screen.show(recipe, back_to)
        self.go("recipe")

    def _on_key(self, _window, key, *_):
        if key == 27:  # botón «atrás» de Android / Esc
            current = self.sm.current
            if current == "recipe":
                self.go(self.recipe_screen.back_to, back=True)
                return True
            if current in ("menu", "browse"):
                self.go_home()
                return True
        return False

    # --- datos ----------------------------------------------------------------
    def load_data(self):
        self.planner.show_loading()
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        try:
            self.logic.load_recipes()
            Clock.schedule_once(lambda *_: self._loaded(), 0)
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda *_: self._load_failed(msg), 0)

    def _loaded(self):
        logic = self.logic
        origin = {"online": "actualizado", "cache": "sin conexión (copia guardada)",
                  "local": "copia incluida"}.get(logic.source, "")
        self.planner.bar.set_subtitle(f"{logic.total_recipes} recetas · {origin}")
        self.planner.build()
        if logic.source != "online":
            Toast.show("Sin conexión: usando la última copia guardada")

    def _load_failed(self, msg):
        self.planner.bar.set_subtitle("Sin recetas")
        self.planner.show_error(f"No se pudieron cargar las recetas.\n{msg}")

    # --- acciones ---------------------------------------------------------------
    def change_filter(self, value):
        adjusted = self.logic.set_filter(value)
        self.logic.save_state()
        self.planner.build()
        if adjusted:
            Toast.show("Cantidades ajustadas: " + ", ".join(adjusted))

    def change_amount(self, category, value):
        self.logic.set_amount(category, value)
        self.logic.save_state()
        self.planner.update_total()

    def generate_menu(self):
        def do():
            self.logic.generate_menu()
            self.menu_screen.tab = "Platos"
            self.menu_screen.tabs.select("Platos")
            self.open_menu()
        if self.logic.menu and self.logic.checked:
            confirm("¿Nuevo menú?", "Se sustituirá el menú actual y su lista de la compra.",
                    do, yes_text="Generar", variant="primary")
        else:
            do()

    def on_pause(self):
        self.logic.save_state()
        return True


if __name__ == "__main__":
    CocinaApp().run()
