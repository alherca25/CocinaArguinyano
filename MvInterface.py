# MvInterface.py
# Interfaz móvil (Kivy/KivyMD-ready) que replica PyInterface.py para Android.
# Compatible con Buildozer (python-for-android).

import os
import random
import threading
import warnings
from datetime import datetime
from io import BytesIO

import requests
from openpyxl import load_workbook

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
# PDF backend: fpdf2 (compatible con Android a través de python-for-android)
# ---------------------------------------------------------------------------
try:
    from fpdf import FPDF
    _FPDF_AVAILABLE = True
except ImportError:
    _FPDF_AVAILABLE = False

# ---------------------------------------------------------------------------
# Directorio de salida para los PDF
# ---------------------------------------------------------------------------
try:
    from android.storage import app_storage_path  # type: ignore
    PDF_DIR = app_storage_path()
except Exception:
    PDF_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


# ===========================================================================
# LÓGICA DE NEGOCIO (sin dependencias de UI)
# ===========================================================================

class CocinaArguinyanoLogic:
    """Lógica pura: carga de recetas, selección aleatoria, generación de PDF."""

    EXCEL_URL = (
        "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/"
        "main/CocinaArguinyano.xlsx"
    )
    _EXCLUDED_SHEETS = ("Ingredientes", "Unidades")

    def __init__(self):
        self.recipes_table: dict = {}      # {sheet_name: [row_dict, ...]}
        self.selected_dishes: dict = {}    # {tipo: cantidad}
        self.actual_date: str = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def load_recipes(self) -> str:
        """Carga el Excel desde GitHub. Devuelve "" si OK, mensaje de error si falla."""
        try:
            resp = requests.get(self.EXCEL_URL, timeout=20)
            resp.raise_for_status()

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                workbook = load_workbook(
                    filename=BytesIO(resp.content),
                    data_only=True
                )

            self.recipes_table = self._workbook_to_dict(workbook)
            return ""

        except Exception as exc:
            return f"No se pudo cargar el Excel:\n{exc}"

    def _workbook_to_dict(self, workbook) -> dict:
        """Convierte el workbook a un diccionario por hojas con filas tipo dict."""
        sheets_data = {}

        for sheet_name in workbook.sheetnames:
            ws = workbook[sheet_name]
            rows = list(ws.iter_rows(values_only=True))

            if not rows:
                sheets_data[sheet_name] = []
                continue

            headers = []
            for header in rows[0]:
                header_text = "" if header is None else str(header).strip()
                headers.append(header_text)

            clean_rows = []
            for row in rows[1:]:
                row_dict = {}
                has_any_value = False

                for idx, value in enumerate(row):
                    key = headers[idx] if idx < len(headers) else f"Col{idx + 1}"
                    if not key:
                        key = f"Col{idx + 1}"

                    if value is not None and str(value).strip() != "":
                        has_any_value = True

                    row_dict[key] = value

                if has_any_value:
                    clean_rows.append(row_dict)

            sheets_data[sheet_name] = clean_rows

        return sheets_data

    # ------------------------------------------------------------------
    # Tipos de receta disponibles
    # ------------------------------------------------------------------

    def get_recipe_types(self) -> list:
        return [
            sheet_name
            for sheet_name in self.recipes_table.keys()
            if sheet_name not in self._EXCLUDED_SHEETS
        ]

    # ------------------------------------------------------------------
    # CRUD sobre selected_dishes
    # ------------------------------------------------------------------

    def add_dish(self, dish_type: str, quantity: str) -> str:
        if not dish_type or dish_type == "—":
            return "Selecciona un tipo de receta."

        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            return "La cantidad debe ser un número entero."

        if qty <= 0:
            return "La cantidad debe ser mayor que 0."

        self.selected_dishes[dish_type] = qty
        return ""

    def edit_dish(self, old_type: str, new_type: str, new_quantity: str) -> str:
        self.selected_dishes.pop(old_type, None)
        return self.add_dish(new_type, new_quantity)

    def remove_dish(self, dish_type: str):
        self.selected_dishes.pop(dish_type, None)

    # ------------------------------------------------------------------
    # Helpers de datos
    # ------------------------------------------------------------------

    def _normalize_text(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_number(self, value) -> float:
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().replace(",", ".")
        if not text:
            return 0.0

        try:
            return float(text)
        except ValueError:
            return 0.0

    def _format_number(self, value) -> str:
        if isinstance(value, int):
            return str(value)

        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip("0").rstrip(".")

        return str(value)

    def _fill_forward_plate(self, rows: list) -> list:
        """Replica el comportamiento de ffill() sobre la columna Plato."""
        current_plate = ""

        for row in rows:
            plate = self._normalize_text(row.get("Plato"))
            if plate:
                current_plate = plate
            else:
                row["Plato"] = current_plate

        return rows

    # ------------------------------------------------------------------
    # Selección aleatoria de platos
    # ------------------------------------------------------------------

    def get_selected_dishes(self, save_pdf: bool = False) -> list:
        result = []

        for plate_type, desired_num in self.selected_dishes.items():
            if plate_type not in self.recipes_table or desired_num <= 0:
                continue

            rows = [dict(item) for item in self.recipes_table.get(plate_type, [])]
            if not rows:
                continue

            rows = self._fill_forward_plate(rows)

            unique_dishes = []
            seen = set()

            for row in rows:
                plate_name = self._normalize_text(row.get("Plato"))
                if plate_name and plate_name not in seen:
                    seen.add(plate_name)
                    unique_dishes.append(plate_name)

            n = min(len(unique_dishes), desired_num)
            if n == 0:
                continue

            try:
                chosen = random.sample(unique_dishes, n)
            except ValueError:
                continue

            for dish_name in chosen:
                first_row = None

                for row in rows:
                    if self._normalize_text(row.get("Plato")) == dish_name:
                        first_row = row
                        break

                if first_row is None:
                    continue

                page_value = first_row.get("Página", first_row.get("Pagina", ""))

                result.append({
                    "Tipo": plate_type,
                    "Plato": dish_name,
                    "Página": "" if page_value is None else str(page_value),
                })

        if save_pdf and result:
            self.generate_pdf(result, f"Recetas-{self.actual_date}")

        return result

    # ------------------------------------------------------------------
    # Extracción de ingredientes
    # ------------------------------------------------------------------

    def get_ingredients_from_dishes(self, save_pdf: bool = True) -> list:
        dishes_list = self.get_selected_dishes(save_pdf=False)

        if not dishes_list:
            return []

        selected_by_type = {}
        for item in dishes_list:
            dish_type = item.get("Tipo", "")
            dish_name = item.get("Plato", "")
            selected_by_type.setdefault(dish_type, set()).add(dish_name)

        grouped = {}

        for plate_type in self.selected_dishes:
            if plate_type not in self.recipes_table:
                continue

            rows = [dict(item) for item in self.recipes_table.get(plate_type, [])]
            if not rows:
                continue

            rows = self._fill_forward_plate(rows)
            selected_names = selected_by_type.get(plate_type, set())

            for row in rows:
                dish_name = self._normalize_text(row.get("Plato"))
                if dish_name not in selected_names:
                    continue

                ingredient = self._normalize_text(row.get("Ingredientes"))
                if not ingredient:
                    continue

                quantity = self._normalize_number(row.get("Cantidades"))
                unit = self._normalize_text(row.get("Unidades"))

                if ingredient not in grouped:
                    grouped[ingredient] = {
                        "Ingredientes": ingredient,
                        "Cantidades": 0.0,
                        "Unidades": unit,
                    }

                grouped[ingredient]["Cantidades"] += quantity

                if not grouped[ingredient]["Unidades"] and unit:
                    grouped[ingredient]["Unidades"] = unit

        result = list(grouped.values())

        result.sort(key=lambda x: self._normalize_text(x.get("Ingredientes")).lower())

        for item in result:
            item["Cantidades"] = self._format_number(item.get("Cantidades", 0))

        if save_pdf and result:
            self.generate_pdf(result, f"Compra-{self.actual_date}")

        return result

    def generate_all(self):
        """Genera ambas listas (recetas + compra) y sus PDF."""
        self.get_selected_dishes(save_pdf=True)
        self.get_ingredients_from_dishes(save_pdf=True)

    # ------------------------------------------------------------------
    # Generación de PDF (fpdf2)
    # ------------------------------------------------------------------

    def generate_pdf(self, rows: list, title: str) -> str:
        if not _FPDF_AVAILABLE:
            return "fpdf2 no está instalado."

        if not rows:
            return "Sin datos para generar el PDF."

        os.makedirs(PDF_DIR, exist_ok=True)
        pdf_path = os.path.join(PDF_DIR, f"{title}.pdf")

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Título
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 12, title, align="C")
        pdf.ln(12)

        headers = list(rows[0].keys())
        effective_page_width = pdf.w - pdf.l_margin - pdf.r_margin
        ncols = max(1, len(headers))
        col_w = effective_page_width / ncols

        # Cabecera de la tabla
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(80, 80, 80)
        pdf.set_text_color(255, 255, 255)

        for col in headers:
            pdf.cell(col_w, 9, str(col)[:30], border=1, align="C", fill=True)
        pdf.ln()

        # Filas
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)

        for row in rows:
            for header in headers:
                value = row.get(header, "")
                text = "" if value is None else str(value)
                pdf.cell(col_w, 8, text[:30], border=1, align="C")
            pdf.ln()

        pdf.output(pdf_path)
        return pdf_path


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

    def _run_in_thread(self, fn, success_msg: str):
        """Ejecuta fn() en un hilo y muestra popup al terminar."""

        def worker():
            try:
                fn()
                Clock.schedule_once(
                    lambda _: self._show_info("Listo", success_msg), 0
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
            lambda: self.logic.get_selected_dishes(save_pdf=True),
            f"PDF de recetas guardado en:\n{PDF_DIR}",
        )

    def on_gen_shopping(self, *_):
        if not self.logic.selected_dishes:
            self._show_info("Aviso", "Añade al menos un tipo de plato.")
            return

        self._run_in_thread(
            lambda: self.logic.get_ingredients_from_dishes(save_pdf=True),
            f"PDF de compra guardado en:\n{PDF_DIR}",
        )

    def on_gen_both(self, *_):
        if not self.logic.selected_dishes:
            self._show_info("Aviso", "Añade al menos un tipo de plato.")
            return

        self._run_in_thread(
            self.logic.generate_all,
            f"PDFs de recetas y compra guardados en:\n{PDF_DIR}",
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