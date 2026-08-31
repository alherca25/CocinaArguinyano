# MvInterface.py
# Interfaz móvil (Kivy/KivyMD-ready) que replica PyInterface.py para Android.
# Compatible con Buildozer (python-for-android).

import os
import os
import random
import threading
from datetime import datetime
import json

import requests
import functions

# ---------------------------------------------------------------------------
# Kivy imports
# ---------------------------------------------------------------------------
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ---------------------------------------------------------------------------
# Exportador nativo a TXT (reemplazo de FPDF)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Directorio de salida para los PDF
# ---------------------------------------------------------------------------
from kivy.utils import platform

def get_local_pdf_dir():
    if platform == 'android':
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and app.user_data_dir:
                return app.user_data_dir
        except Exception:
            pass
        return "."
    else:
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(docs):
            docs = "."
        return docs


# ===========================================================================
# LÓGICA DE NEGOCIO (sin dependencias de UI)
# ===========================================================================

class CocinaArguinyanoLogic:
    """Lógica pura: carga de recetas, selección aleatoria, generación de PDF."""

    JSON_URL = (
        "https://raw.githubusercontent.com/alherca25/BaseDatosRecetas/"
        "main/CocinaArguinyano.json"
    )

    def __init__(self):
        self.recipes_table: dict = {}      
        self.selected_dishes: dict = {}    # {tipo: cantidad}
        self.active_filter: str = "Todo"
        self.actual_date: str = datetime.now().strftime("%Y-%m-%d")

    def get_cache_path(self) -> str:
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and app.user_data_dir:
                os.makedirs(app.user_data_dir, exist_ok=True)
                return os.path.join(app.user_data_dir, "CocinaArguinyano.json")
        except Exception as e:
            print(f"Error al obtener ruta de caché: {e}")
        return None

    def load_recipes(self) -> str:
        """Carga el JSON desde GitHub o caché/local."""
        cache_path = self.get_cache_path()

        try:
            self.recipes_table = functions.load_recipes(self.JSON_URL, is_local=False)
            if cache_path:
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(self.recipes_table, f, ensure_ascii=False)
                except Exception:
                    pass
            return ""
        except Exception as exc:
            print(f"Descarga fallida: {exc}")
            
        if cache_path and os.path.exists(cache_path):
            try:
                self.recipes_table = functions.load_recipes(cache_path, is_local=True)
                return ""
            except Exception:
                pass

        try:
            local_file = "CocinaArguinyano.json"
            if not os.path.exists(local_file):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                local_file = os.path.join(script_dir, "CocinaArguinyano.json")

            if os.path.exists(local_file):
                self.recipes_table = functions.load_recipes(local_file, is_local=True)
                return ""
            else:
                return f"No se encontró JSON local ni en GitHub."
        except Exception as local_exc:
            return f"Fallo descarga y fallo lectura local ({local_exc})"

    def get_recipe_types(self) -> list:
        return list(self.recipes_table.keys())

    def add_dish(self, dish_type: str, quantity: str) -> str:
        if not dish_type or dish_type == "—":
            return "Selecciona un tipo de receta."
        try:
            qty = int(quantity)
        except ValueError:
            return "La cantidad debe ser un número entero."
        if qty <= 0:
            return "La cantidad debe ser mayor que 0."

        adjusted_msg = ""
        if dish_type in self.recipes_table:
            valid_recipes = functions.filter_recipes(self.recipes_table[dish_type], self.active_filter)
            max_recetas = len(valid_recipes)
            if qty > max_recetas:
                qty = max_recetas
                adjusted_msg = f"Ajustado: Con el filtro '{self.active_filter}', solo hay {max_recetas} platos disponibles."

        self.selected_dishes[dish_type] = qty
        return adjusted_msg

    def edit_dish(self, old_type: str, new_type: str, new_quantity: str) -> str:
        self.selected_dishes.pop(old_type, None)
        return self.add_dish(new_type, new_quantity)

    def remove_dish(self, dish_type: str):
        self.selected_dishes.pop(dish_type, None)

    def get_selected_dishes(self, save_pdf: bool = False):
        result = []
        for plate_type, desired_num in self.selected_dishes.items():
            if desired_num <= 0: continue
            
            dishes, limited = functions.select_random_dishes(
                self.recipes_table, plate_type, desired_num, self.active_filter
            )
            
            for d in dishes:
                d_copy = d.copy()
                d_copy["Tipo"] = plate_type
                result.append(d_copy)

        if not result:
            raise RuntimeError("No se pudo seleccionar ningún plato.")

        if save_pdf:
            return self.generate_recipes_pdf(result, f"Recetas-{self.actual_date}")

        return result

    def get_ingredients_from_dishes(self, save_pdf: bool = True, dishes_list: list = None):
        if dishes_list is None:
            dishes_list = self.get_selected_dishes(save_pdf=False)
        if not dishes_list:
            raise RuntimeError("No hay platos seleccionados.")

        grouped = {}
        for recipe in dishes_list:
            for ing in recipe.get("ingredientes", []):
                nombre = str(ing.get("nombre", "")).strip()
                if not nombre: continue
                key = nombre.lower()
                
                unidad = str(ing.get("unidad", "")).strip()
                cantidad_str = str(ing.get("cantidad", "")).strip()
                
                cantidad_val = 0.0
                is_numeric = False
                try:
                    if cantidad_str and cantidad_str.lower() != 'nan':
                        cantidad_val = float(cantidad_str)
                        is_numeric = True
                except ValueError:
                    pass
                
                full_key = (key, unidad)
                if full_key not in grouped:
                    grouped[full_key] = {
                        "Ingredientes": nombre,
                        "Cantidades": cantidad_val if is_numeric else cantidad_str,
                        "Unidades": unidad,
                        "is_numeric": is_numeric
                    }
                else:
                    if is_numeric and grouped[full_key]["is_numeric"]:
                        grouped[full_key]["Cantidades"] += cantidad_val

        result = list(grouped.values())
        result.sort(key=lambda x: x["Ingredientes"].lower())

        for item in result:
            cant = item["Cantidades"]
            if item["is_numeric"] and float(cant).is_integer():
                cant = int(float(cant))
            item["Cantidades"] = str(cant)
            
        if not result:
            raise RuntimeError("No hay ingredientes.")

        if save_pdf:
            return self.generate_pdf(result, f"Compra-{self.actual_date}")
        return result

    def generate_all(self) -> str:
        dishes = self.get_selected_dishes(save_pdf=False)
        msg1 = self.generate_recipes_pdf(dishes, f"Recetas-{self.actual_date}")
        ingredients = self.get_ingredients_from_dishes(save_pdf=False, dishes_list=dishes)
        msg2 = self.generate_pdf(ingredients, f"Compra-{self.actual_date}")
        return f"Recetas:\n{msg1}\n\nCompra:\n{msg2}"

    def generate_pdf(self, rows: list, title: str) -> str:
        if not rows:
            raise RuntimeError("Sin datos para generar el documento.")

        pdf_dir = get_local_pdf_dir()
        os.makedirs(pdf_dir, exist_ok=True)
        txt_name = f"{title}.txt"
        local_path = os.path.join(pdf_dir, txt_name)

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(f"--- {title.upper()} ---\n\n")
            f.write(f"{'Ingrediente':<30} | {'Cantidad':<10} | {'Unidad':<15}\n")
            f.write("-" * 60 + "\n")
            for row in rows:
                ing = str(row.get("Ingredientes", ""))[:30]
                cant = str(row.get("Cantidades", ""))[:10]
                unid = str(row.get("Unidades", ""))[:15]
                f.write(f"{ing:<30} | {cant:<10} | {unid:<15}\n")
            f.write("\n" + "-" * 60 + "\n")

        # Compartir el TXT mediante menú nativo si estamos en Android
        if platform == 'android':
            try:
                from plyer import share
                share.share(local_path, title=txt_name)
                return f"Lista generada. Abre el menú para compartirla/guardarla."
            except Exception as e:
                return f"Guardado internamente debido a un fallo al compartir:\n{local_path}\nError: {e}"

        return local_path

    def generate_recipes_pdf(self, dishes: list, title: str) -> str:
        if not dishes:
            raise RuntimeError("Sin platos seleccionados para generar el documento.")

        pdf_dir = get_local_pdf_dir()
        os.makedirs(pdf_dir, exist_ok=True)
        txt_name = f"{title}.txt"
        local_path = os.path.join(pdf_dir, txt_name)

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(f"=== {title.upper()} ===\n\n")
            for dish in dishes:
                dish_name = dish.get("nombre", dish.get("Plato", ""))
                plate_type = dish.get("Tipo", "")
                elaboration = dish.get("elaboracion", dish.get("Elaboración", ""))
                page_val = dish.get("pagina", dish.get("Página", ""))

                f.write(f"PLATILLO: {dish_name}\n")
                meta = f"Categoría: {plate_type}"
                if page_val:
                    meta += f" | Página: {page_val}"
                f.write(f"{meta}\n\n")

                f.write("INGREDIENTES:\n")
                for ing in dish.get("ingredientes", []):
                    formatted_ing = functions.format_ingredient(ing)
                    if formatted_ing:
                        f.write(f" - {formatted_ing}\n")
                
                f.write("\nELABORACIÓN:\n")
                f.write(f"{elaboration if elaboration else 'Sin elaboración.'}\n")
                f.write("\n" + "=" * 40 + "\n\n")

        # Compartir el TXT mediante menú nativo si estamos en Android
        if platform == 'android':
            try:
                from plyer import share
                share.share(local_path, title=txt_name)
                return f"Recetas generadas. Abre el menú para compartir/guardar."
            except Exception as e:
                return f"Guardado internamente debido a un fallo al compartir:\n{local_path}\nError: {e}"

        return local_path


# ===========================================================================
# COMPONENTES DE UI (Kivy)
# ===========================================================================

class SelectableRow(BoxLayout):
    """Fila seleccionable en la lista de platos seleccionados."""

    NORMAL_COLOR = (0.15, 0.15, 0.2, 1)
    SELECTED_COLOR = (0.2, 0.5, 0.85, 1)

    def __init__(self, dish_type: str, quantity: int, on_select_cb, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(4),
            padding=(dp(6), dp(4)),
            **kwargs
        )
        self.dish_type = dish_type
        self.quantity = quantity
        self._on_select_cb = on_select_cb
        self._selected = False

        with self.canvas.before:
            self._bg_color_inst = Color(*self.NORMAL_COLOR)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

        self.lbl_type = Label(
            text=dish_type,
            size_hint_x=0.65,
            halign="left",
            valign="middle"
        )
        self.lbl_type.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        self.lbl_qty = Label(
            text=str(quantity),
            size_hint_x=0.20,
            halign="center",
            valign="middle"
        )
        self.lbl_qty.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )

        btn_select = Button(
            text="Seleccionar",
            size_hint_x=0.15,
            background_color=(0.3, 0.6, 1, 1),
            font_size="12sp"
        )
        btn_select.bind(on_release=self._toggle_select)

        self.add_widget(self.lbl_type)
        self.add_widget(self.lbl_qty)
        self.add_widget(btn_select)

    def _update_rect(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _toggle_select(self, *_):
        self._selected = not self._selected
        color = self.SELECTED_COLOR if self._selected else self.NORMAL_COLOR
        self._bg_color_inst.rgba = color
        self._on_select_cb(self)

    @property
    def is_selected(self) -> bool:
        return self._selected

    def deselect(self):
        self._selected = False
        self._bg_color_inst.rgba = self.NORMAL_COLOR


class HeaderRow(BoxLayout):
    """Cabecera de la tabla de platos."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            **kwargs
        )

        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(
            pos=lambda *_: setattr(self._rect, "pos", self.pos),
            size=lambda *_: setattr(self._rect, "size", self.size)
        )

        for text, hint in (
            ("Tipo de plato", 0.65),
            ("Cant.", 0.20),
            ("", 0.15),
        ):
            lbl = Label(
                text=text,
                size_hint_x=hint,
                bold=True,
                color=(0.8, 0.9, 1, 1),
                halign="center",
                valign="middle"
            )
            lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            self.add_widget(lbl)


# ===========================================================================
# POPUP: Añadir plato
# ===========================================================================

class AddDishPopup(Popup):
    def __init__(self, recipe_types: list, on_confirm, **kwargs):
        kwargs.setdefault("title", "Añadir plato")
        kwargs.setdefault("size_hint", (0.88, 0.55))
        super().__init__(**kwargs)
        self._on_confirm = on_confirm

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12)
        )

        layout.add_widget(
            Label(text="Tipo de receta:", size_hint_y=None, height=dp(28))
        )

        self.spinner = Spinner(
            text=recipe_types[0] if recipe_types else "—",
            values=recipe_types,
            size_hint_y=None,
            height=dp(44),
        )
        layout.add_widget(self.spinner)

        layout.add_widget(
            Label(text="Número de platos:", size_hint_y=None, height=dp(28))
        )

        self.qty_input = TextInput(
            hint_text="Ej: 3",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(44),
        )
        layout.add_widget(self.qty_input)

        layout.add_widget(Widget())  # spacer

        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))

        btn_cancel = Button(
            text="Cancelar",
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_cancel.bind(on_release=self.dismiss)

        btn_ok = Button(
            text="Añadir",
            background_color=(0.2, 0.6, 0.3, 1)
        )
        btn_ok.bind(on_release=self._on_ok)

        btns.add_widget(btn_cancel)
        btns.add_widget(btn_ok)
        layout.add_widget(btns)

        self.content = layout

    def _on_ok(self, *_):
        dish_type = self.spinner.text
        qty = self.qty_input.text.strip() or "1"
        self._on_confirm(dish_type, qty)
        self.dismiss()


# ===========================================================================
# POPUP: Editar plato
# ===========================================================================

class EditDishPopup(Popup):
    def __init__(self, dish_type: str, quantity: int, recipe_types: list,
                 on_confirm, **kwargs):
        kwargs.setdefault("title", "Editar plato")
        kwargs.setdefault("size_hint", (0.88, 0.55))
        super().__init__(**kwargs)
        self._old_type = dish_type
        self._on_confirm = on_confirm

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12)
        )

        layout.add_widget(
            Label(text="Tipo de receta:", size_hint_y=None, height=dp(28))
        )

        self.spinner = Spinner(
            text=dish_type,
            values=recipe_types,
            size_hint_y=None,
            height=dp(44),
        )
        layout.add_widget(self.spinner)

        layout.add_widget(
            Label(text="Número de platos:", size_hint_y=None, height=dp(28))
        )

        self.qty_input = TextInput(
            text=str(quantity),
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(44),
        )
        layout.add_widget(self.qty_input)

        layout.add_widget(Widget())

        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))

        btn_cancel = Button(
            text="Cancelar",
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_cancel.bind(on_release=self.dismiss)

        btn_ok = Button(
            text="Actualizar",
            background_color=(0.2, 0.5, 0.85, 1)
        )
        btn_ok.bind(on_release=self._on_ok)

        btns.add_widget(btn_cancel)
        btns.add_widget(btn_ok)
        layout.add_widget(btns)

        self.content = layout

    def _on_ok(self, *_):
        new_type = self.spinner.text
        new_qty = self.qty_input.text.strip() or "1"
        self._on_confirm(self._old_type, new_type, new_qty)
        self.dismiss()


# ===========================================================================
# POPUP: Mensaje informativo / error
# ===========================================================================

class InfoPopup(Popup):
    def __init__(self, title: str, message: str, **kwargs):
        kwargs.setdefault("size_hint", (0.85, 0.4))
        super().__init__(title=title, **kwargs)

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12)
        )

        lbl = Label(
            text=message,
            halign="center",
            valign="middle"
        )
        lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        layout.add_widget(lbl)

        btn = Button(
            text="OK",
            size_hint_y=None,
            height=dp(44),
            background_color=(0.2, 0.6, 0.3, 1)
        )
        btn.bind(on_release=self.dismiss)
        layout.add_widget(btn)

        self.content = layout


# ===========================================================================
# PANTALLA PRINCIPAL
# ===========================================================================

class MainScreen(BoxLayout):
    """Widget raíz de la aplicación."""

    BG_COLOR = (0.08, 0.08, 0.12, 1)

    def __init__(self, logic: CocinaArguinyanoLogic, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10),
            **kwargs
        )
        self.logic = logic
        self._selected_row = None  # fila actualmente seleccionada

        with self.canvas.before:
            Color(*self.BG_COLOR)
            self._bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(
            pos=lambda *_: setattr(self._bg, "pos", self.pos),
            size=lambda *_: setattr(self._bg, "size", self.size)
        )

        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _build_ui(self):
        # --- Título ---
        title_lbl = Label(
            text="Cocina Rápida",
            font_size="22sp",
            bold=True,
            color=(1, 0.85, 0.3, 1),
            size_hint_y=None,
            height=dp(48),
            halign="center",
            valign="middle",
        )
        title_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.add_widget(title_lbl)

        # --- Estado de carga ---
        self.lbl_status = Label(
            text="Cargando recetas...",
            font_size="13sp",
            color=(0.7, 0.9, 1, 1),
            size_hint_y=None,
            height=dp(28),
            halign="center",
            valign="middle",
        )
        self.lbl_status.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        self.add_widget(self.lbl_status)

        # --- Filtro ---
        filter_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5), padding=(0, 0, 0, dp(5)))
        filter_lbl = Label(
            text="Filtro:", size_hint_x=0.2, halign="right", valign="middle"
        )
        filter_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.filter_spinner = Spinner(
            text="Todo",
            values=["Todo", "Vegetariano", "Gluten Free"],
            size_hint_x=0.8,
            height=dp(36),
            background_color=(0.2, 0.2, 0.3, 1)
        )
        self.filter_spinner.bind(text=self.on_filter_change)
        filter_layout.add_widget(filter_lbl)
        filter_layout.add_widget(self.filter_spinner)
        self.add_widget(filter_layout)

        # --- Cabecera de la tabla ---
        self.add_widget(HeaderRow())

        # --- Lista de platos seleccionados (scroll) ---
        scroll = ScrollView()
        self.list_container = GridLayout(
            cols=1,
            spacing=dp(4),
            size_hint_y=None,
        )
        self.list_container.bind(
            minimum_height=self.list_container.setter("height")
        )
        scroll.add_widget(self.list_container)
        self.add_widget(scroll)

        # --- Botones CRUD ---
        crud_btns = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))

        for label, color, cb in (
            ("Añadir", (0.2, 0.6, 0.3, 1), self.on_add),
            ("Editar", (0.2, 0.5, 0.85, 1), self.on_edit),
            ("Eliminar", (0.75, 0.25, 0.2, 1), self.on_delete),
        ):
            btn = Button(
                text=label,
                background_color=color,
                font_size="14sp"
            )
            btn.bind(on_release=cb)
            crud_btns.add_widget(btn)

        self.add_widget(crud_btns)

        # --- Separador ---
        sep_lbl = Label(
            text="Generar listas:",
            font_size="13sp",
            color=(0.75, 0.75, 0.75, 1),
            size_hint_y=None,
            height=dp(26),
            halign="center",
            valign="middle",
        )
        sep_lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        self.add_widget(sep_lbl)

        # --- Botones de generación ---
        gen_btns = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))

        for label, color, cb in (
            ("Recetas", (0.6, 0.3, 0.8, 1), self.on_gen_recipes),
            ("Compra", (0.2, 0.55, 0.65, 1), self.on_gen_shopping),
            ("Ambas", (0.7, 0.45, 0.1, 1), self.on_gen_both),
        ):
            btn = Button(
                text=label,
                background_color=color,
                font_size="14sp"
            )
            btn.bind(on_release=cb)
            gen_btns.add_widget(btn)

        self.add_widget(gen_btns)

    # ------------------------------------------------------------------
    # Actualizar lista visual
    # ------------------------------------------------------------------

    def refresh_list(self):
        self._selected_row = None
        self.list_container.clear_widgets()

        if not self.logic.selected_dishes:
            lbl = Label(
                text="(Ningún plato añadido aún)",
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(44),
                halign="center",
                valign="middle",
            )
            lbl.bind(size=lambda instance, value: setattr(instance, "text_size", value))
            self.list_container.add_widget(lbl)
            return

        for dtype, qty in self.logic.selected_dishes.items():
            row = SelectableRow(dtype, qty, self._on_row_selected)
            self.list_container.add_widget(row)

    def on_filter_change(self, spinner, text):
        self.logic.active_filter = text

    def _on_row_selected(self, row: SelectableRow):
        # Des-seleccionar anterior si es distinto
        if self._selected_row and self._selected_row is not row:
            self._selected_row.deselect()

        self._selected_row = row if row.is_selected else None

    # ------------------------------------------------------------------
    # Acciones CRUD
    # ------------------------------------------------------------------

    def on_add(self, *_):
        types = self.logic.get_recipe_types()
        if not types:
            self._show_info("Error", "No hay recetas cargadas todavía.")
            return

        AddDishPopup(recipe_types=types, on_confirm=self._confirm_add).open()

    def _confirm_add(self, dish_type: str, qty: str):
        err = self.logic.add_dish(dish_type, qty)
        if err:
            if err.startswith("Ajustado:"):
                self._show_info("Cantidad ajustada", err)
                self.refresh_list()
            else:
                self._show_info("Error", err)
        else:
            self.refresh_list()

    def on_edit(self, *_):
        if not self._selected_row:
            self._show_info("Aviso", "Selecciona un plato de la lista para editarlo.")
            return

        row = self._selected_row
        EditDishPopup(
            dish_type=row.dish_type,
            quantity=row.quantity,
            recipe_types=self.logic.get_recipe_types(),
            on_confirm=self._confirm_edit,
        ).open()

    def _confirm_edit(self, old_type: str, new_type: str, new_qty: str):
        err = self.logic.edit_dish(old_type, new_type, new_qty)
        if err:
            if err.startswith("Ajustado:"):
                self._show_info("Cantidad ajustada", err)
                self._selected_row = None
                self.refresh_list()
            else:
                self._show_info("Error", err)
        else:
            self._selected_row = None
            self.refresh_list()

    def on_delete(self, *_):
        if not self._selected_row:
            self._show_info("Aviso", "Selecciona un plato de la lista para eliminarlo.")
            return

        dish_type = self._selected_row.dish_type
        self.logic.remove_dish(dish_type)
        self._selected_row = None
        self.refresh_list()

    # ------------------------------------------------------------------
    # Acciones de generación (ejecutadas en hilo secundario)
    # ------------------------------------------------------------------

    def _run_in_thread(self, fn):
        """Ejecuta fn() en un hilo y muestra popup con el mensaje devuelto al terminar."""

        def worker():
            try:
                msg = fn()
                # Si retorna una lista u otro objeto que no sea string, ponemos un mensaje genérico
                if not isinstance(msg, str):
                    msg = "Operación completada con éxito."
                Clock.schedule_once(
                    lambda _: self._show_info("Listo", str(msg)), 0
                )
            except Exception as exc:
                msg = str(exc)
                Clock.schedule_once(
                    lambda _: self._show_info("Error", msg), 0
                )

        threading.Thread(target=worker, daemon=True).start()

    def on_gen_recipes(self, *_):
        if not self.logic.selected_dishes:
            self._show_info("Aviso", "Añade al menos un tipo de plato.")
            return

        self._run_in_thread(
            lambda: self.logic.get_selected_dishes(save_pdf=True)
        )

    def on_gen_shopping(self, *_):
        if not self.logic.selected_dishes:
            self._show_info("Aviso", "Añade al menos un tipo de plato.")
            return

        self._run_in_thread(
            lambda: self.logic.get_ingredients_from_dishes(save_pdf=True)
        )

    def on_gen_both(self, *_):
        if not self.logic.selected_dishes:
            self._show_info("Aviso", "Añade al menos un tipo de plato.")
            return

        self._run_in_thread(
            self.logic.generate_all
        )

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _show_info(self, title: str, message: str):
        InfoPopup(title=title, message=message).open()

    def set_status(self, text: str):
        self.lbl_status.text = text


# ===========================================================================
# APLICACIÓN PRINCIPAL (Kivy App)
# ===========================================================================

class CocinaApp(App):
    """Punto de entrada de la aplicación Kivy."""

    def build(self):
        self.title = "Cocina Rápida"
        self.logic = CocinaArguinyanoLogic()
        self.screen = MainScreen(logic=self.logic)

        # Cargar recetas en background para no bloquear la UI
        threading.Thread(target=self._load_data, daemon=True).start()
        return self.screen

    def _load_data(self):
        err = self.logic.load_recipes()

        if err:
            Clock.schedule_once(
                lambda _: self.screen.set_status(f"Error: {err}"), 0
            )
        else:
            types = self.logic.get_recipe_types()
            msg = (
                f"{len(types)} tipos de plato cargados"
                if types else
                "Sin tipos de plato"
            )
            Clock.schedule_once(lambda _: self.screen.set_status(msg), 0)
            Clock.schedule_once(lambda _: self.screen.refresh_list(), 0)


if __name__ == "__main__":
    CocinaApp().run()