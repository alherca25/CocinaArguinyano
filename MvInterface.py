# MvInterface.py
import sys
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.properties import ListProperty, StringProperty
from kivy.clock import mainthread

import pandas as pd
import requests
from io import BytesIO
import warnings
import numpy as np

# --- Librería para PDF (reemplaza ReportLab)
from fpdf import FPDF

# --- Ruta donde se guardarán los PDFs (en Android /storage/emulated/0/Download)
# Si usas android.storage, puedes cambiar PDF_DIR dinámicamente
try:
    from android.storage import primary_external_storage_path
    PDF_DIR = os.path.join(primary_external_storage_path(), 'Download')
except:
    PDF_DIR = "/storage/emulated/0/Download"  # ruta típica en Android


class DishEntry(BoxLayout):
    dish_type = StringProperty("")
    quantity = StringProperty("0")


class CocinaArguinyano:
    def __init__(self):
        # Configuración de rutas
        self.EXCEL_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/main/CocinaArguinyano.xlsx"
        self.recipes_table = self.load_recipes()
        self.selected_dishes = {}  # {tipo: cantidad}
        self.actual_date = datetime.now().strftime("%Y-%m-%d")

    def load_recipes(self):
        print("Cargando recetas...")
        """Lee XLSX directamente desde GitHub raw URL"""
        try:
            # Método 1: directo con pandas
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                return pd.read_excel(self.EXCEL_URL, sheet_name=None)
        except Exception as e:
            print(f"Error directo: {e}")
            # Método 2: requests + BytesIO
            response = requests.get(self.EXCEL_URL)
            response.raise_for_status()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                return pd.read_excel(BytesIO(response.content), sheet_name=None)

    def get_recipe_types(self):
        # Devuelve lista de tipos de plato (sin "Ingredientes", "Unidades")
        return [sheet for sheet in self.recipes_table.keys()
                if sheet not in ('Ingredientes', 'Unidades')]

    def add_selected_dish(self, dish_type, quantity):
        if not dish_type:
            return "No se ha seleccionado tipo de receta"
        try:
            qty = int(quantity)
            if qty <= 0:
                return "La cantidad debe ser mayor que 0"
            self.selected_dishes[dish_type] = qty
            return ""
        except ValueError:
            return "La cantidad debe ser un número entero"

    def remove_selected_dish(self, dish_type):
        self.selected_dishes.pop(dish_type, None)

    def edit_selected_dish(self, old_type, new_type, new_quantity):
        self.remove_selected_dish(old_type)
        return self.add_selected_dish(new_type, new_quantity)

    # === NUEVA FUNCIONALIDAD === #
    # Reemplazo de generate_pdf (ReportLab → FPDF)

    def generate_pdf(self, from_df, title):
        """
        Genera un PDF con una tabla a partir de un DataFrame,
        usando fpdf2 en lugar de ReportLab.
        """
        if from_df is None or from_df.empty:
            return ""

        pdf_file = os.path.join(PDF_DIR, f"{title}.pdf")

        # Asegurar que el directorio exista
        if not os.path.exists(PDF_DIR):
            os.makedirs(PDF_DIR, exist_ok=True)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Times", "B", 16)
        pdf.cell(0, 10, title, ln=True, align="C")
        pdf.ln(10)

        # Encabezado de la tabla
        col_widths = [pdf.epw / max(1, len(from_df.columns))] * len(from_df.columns)
        pdf.set_font("Times", "B", 12)
        for i, col in enumerate(from_df.columns):
            pdf.cell(col_widths[i], 10, str(col), border=1, align="C")
        pdf.ln(10)

        # Filas de datos
        pdf.set_font("Times", "", 10)
        for _, row in from_df.iterrows():
            pdf.cell(col_widths[0], 10, str(row.iloc[0]), border=1, align="C")
            for i in range(1, len(row)):
                pdf.cell(col_widths[i], 10, str(row.iloc[i]), border=1, align="C")
            pdf.ln(10)

        pdf.output(pdf_file)
        print(f"PDF generado: {pdf_file}")
        return pdf_file

    # === Funciones de selección de platos e ingredientes === #

    def get_selected_dishes(self, saving_dishes=False):
        """Selecciona y retorna los platos basados en selected_dishes"""
        df_excel = self.recipes_table
        selected_dishes = []

        for plate_type, desired_num in self.selected_dishes.items():
            if plate_type not in df_excel:
                print(f'No se han encontrado recetas de {plate_type}')
                continue

            if desired_num <= 0:
                print(f'No se han solicitado platos de tipo {plate_type}')
                continue

            df_plate = df_excel[plate_type].copy()
            df_plate['Plato'] = df_plate['Plato'].ffill()
            platos = df_plate['Plato'].drop_duplicates().dropna()
            plate_num = min(len(platos), desired_num)

            if plate_num == 0:
                print(f'No hay platos disponibles de tipo {plate_type}')
                continue

            print(f'\nSeleccionando {plate_num} platos de tipo {plate_type}...\n')

            try:
                selected_plates = np.random.choice(platos.values, plate_num, replace=False)
            except ValueError as e:
                print(f'Error al seleccionar platos de {plate_type}: {e}')
                continue

            mask = df_plate['Plato'].isin(selected_plates)
            df_selected = df_plate[mask]
            page_col = 'Página' if 'Página' in df_selected.columns else 'Pagina'
            plate_info = df_selected.groupby('Plato', as_index=False).first()

            plate_info['Tipo'] = plate_type
            plate_info['Página'] = plate_info[page_col].astype('Int64')
            selected_dishes.extend(plate_info[['Tipo', 'Plato', 'Página']].to_dict('records'))

        # Almacenamos los platos seleccionados
        dishes_result = pd.DataFrame(selected_dishes) if selected_dishes else pd.DataFrame()
        if saving_dishes:
            pdf_path = self.generate_pdf(dishes_result, f"Recetas-{self.actual_date}")
            print(f"Lista de recetas guardada en: {pdf_path}")
        return dishes_result

    def get_ingredients_from_dishes(self):
        """Extrae y retorna los ingredientes de los platos seleccionados"""
        df_excel = self.recipes_table
        dishes_df = self.get_selected_dishes(False)

        all_ingredients = []

        for plate_type, desired_num in self.selected_dishes.items():
            if plate_type not in df_excel:
                continue

            if desired_num <= 0:
                continue

            df_plate = df_excel[plate_type].copy()
            df_plate['Plato'] = df_plate['Plato'].ffill()

            selected_plate_names = dishes_df[dishes_df['Tipo'] == plate_type]['Plato'].values
            mask = df_plate['Plato'].isin(selected_plate_names)
            df_selected = df_plate[mask]

            ingredients_df = df_selected[['Ingredientes', 'Cantidades', 'Unidades']].copy()
            all_ingredients.append(ingredients_df)

        if not all_ingredients:
            return pd.DataFrame(columns=['Ingredientes', 'Cantidades', 'Unidades'])

        combined_df = pd.concat(all_ingredients, ignore_index=True)
        ingredients_result = combined_df.groupby('Ingredientes', as_index=False).agg({
            'Cantidades': 'sum',
            'Unidades': 'first'
        })

        # Almacenamos los ingredientes seleccionados en PDF
        pdf_path = self.generate_pdf(ingredients_result, f"Compra-{self.actual_date}")
        print(f"Lista de compra guardada en: {pdf_path}")
        return ingredients_result

    def generate_list(self):
        # Generamos ambas listas
        ingredients_result = self.get_ingredients_from_dishes()
        dishes_result = self.get_selected_dishes(False)
        return ingredients_result, dishes_result


# --- Interfaz Kivy (CocinaApp)

class CocinaApp(App):
    def build(self):
        self.logic = CocinaArguinyano()
        self.entries = []  # Lista de widgets DishEntry

        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Título
        layout.add_widget(Label(text="¡Bienvenid@ a la Cocina Rápida!",
                               size_hint=(1, 0.1),
                               font_size='20sp',
                               bold=True))

        # Scroll area para la lista de platos
        scroll = ScrollView()
        self.scroll_content = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.scroll_content.bind(minimum_height=self.scroll_content.setter('height'))
        scroll.add_widget(self.scroll_content)
        layout.add_widget(scroll)

        # Botones de acción
        btn_layout = BoxLayout(size_hint=(1, 0.2))
        btn_add = Button(text="Añadir")
        btn_add.bind(on_release=self.on_add_press)
        btn_edit = Button(text="Editar")
        btn_edit.bind(on_release=self.on_edit_press)
        btn_delete = Button(text="Eliminar")
        btn_delete.bind(on_release=self.on_delete_press)

        btn_layout.add_widget(btn_add)
        btn_layout.add_widget(btn_edit)
        btn_layout.add_widget(btn_delete)
        layout.add_widget(btn_layout)

        # Botones de generación de listas
        label = Label(text="Generar listas:", size_hint=(1, 0.1))
        layout.add_widget(label)

        list_btns = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        btn_recetas = Button(text="Recetas")
        btn_recetas.bind(on_release=self.on_generate_recipes)
        btn_compra = Button(text="Compra")
        btn_compra.bind(on_release=self.on_generate_shopping)
        btn_ambas = Button(text="Ambas")
        btn_ambas.bind(on_release=self.on_generate_both)

        list_btns.add_widget(btn_recetas)
        list_btns.add_widget(btn_compra)
        layout.add_widget(list_btns)
        layout.add_widget(btn_ambas)

        # Cargar tipos de receta disponibles
        self.recipe_types = self.logic.get_recipe_types()
        if self.recipe_types:
            self.refresh_entries()
        else:
            layout.add_widget(Label(text="No se han cargado recetas", color=(1, 0, 0, 1)))

        return layout

    def refresh_entries(self, *args):
        self.scroll_content.clear_widgets()
        self.entries = []
        for dish_type, qty in self.logic.selected_dishes.items():
            entry = DishEntry()
            entry.dish_type = str(dish_type)
            entry.quantity = str(qty)
            self.scroll_content.add_widget(entry)
            self.entries.append(entry)

    def on_add_press(self, *args):
        types = self.logic.get_recipe_types()
        if not types:
            self.show_error("No hay tipos de receta disponibles")
            return

        popup = AddPopup(logic=self.logic, callback=self.on_add_confirm, types=types)
        popup.open()

    def on_add_confirm(self, dish_type, quantity):
        error = self.logic.add_selected_dish(dish_type, quantity)
        if error:
            self.show_error(error)
        else:
            self.refresh_entries()

    def on_edit_press(self, *args):
        if not self.entries:
            self.show_error("No hay platos seleccionados para editar")
            return

        # Tomar el último entry (puedes ajustar para seleccionar mejor en una UI)
        entry = self.entries[-1]
        popup = EditPopup(logic=self.logic,
                          entry=entry,
                          callback=self.on_edit_confirm,
                          types=self.logic.get_recipe_types())
        popup.open()

    def on_edit_confirm(self, old_type, new_type, new_quantity):
        error = self.logic.edit_selected_dish(old_type, new_type, new_quantity)
        if error:
            self.show_error(error)
        else:
            self.refresh_entries()

    def on_delete_press(self, *args):
        if not self.entries:
            self.show_error("No hay platos seleccionados para eliminar")
            return

        entry = self.entries[-1]
        dish_type = entry.dish_type
        self.logic.remove_selected_dish(dish_type)
        self.refresh_entries()

    def on_generate_recipes(self, *args):
        try:
            df = self.logic.get_selected_dishes(saving_dishes=True)
            if df.empty:
                self.show_info("No hay recetas seleccionadas")
            else:
                self.show_info("Lista de recetas generada")
        except Exception as e:
            self.show_error(f"Error al generar recetas: {str(e)}")

    def on_generate_shopping(self, *args):
        try:
            df = self.logic.get_ingredients_from_dishes()
            if df.empty:
                self.show_info("No hay ingredientes seleccionados")
            else:
                self.show_info("Lista de compra generada")
        except Exception as e:
            self.show_error(f"Error al generar compra: {str(e)}")

    def on_generate_both(self, *args):
        try:
            self.logic.generate_list()
            self.show_info("Listas de recetas y compra generadas")
        except Exception as e:
            self.show_error(f"Error al generar listas: {str(e)}")

    def show_error(self, msg):
        popup = Popup(title="Error",
                      content=Label(text=msg),
                      size_hint=(0.8, 0.4))
        popup.open()

    def show_info(self, msg):
        popup = Popup(title="Info",
                      content=Label(text=msg),
                      size_hint=(0.8, 0.4))
        popup.open()


class AddPopup(Popup):
    def __init__(self, logic, callback, types, **kwargs):
        self.logic = logic
        self.callback = callback
        self.types = types
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        layout.add_widget(Label(text="Tipo de receta:"))

        self.spinner = Spinner(
            text=self.types[0] if self.types else "No hay tipos",
            values=self.types,
            size_hint=(1, None),
            height=44
        )
        layout.add_widget(self.spinner)

        layout.add_widget(Label(text="Cantidad de platos:"))
        self.quantity_input = TextInput(multiline=False, input_filter="int")
        layout.add_widget(self.quantity_input)

        btn_layout = BoxLayout(size_hint=(1, None), height=50)
        btn_cancel = Button(text="Cancelar")
        btn_cancel.bind(on_release=self.dismiss)
        btn_ok = Button(text="Añadir")
        btn_ok.bind(on_release=self.on_ok)
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_ok)
        layout.add_widget(btn_layout)

        self.content = layout

    def on_ok(self, *args):
        dish_type = self.spinner.text
        quantity = self.quantity_input.text.strip()
        if not quantity:
            quantity = "1"

        if self.callback:
            self.callback(dish_type, quantity)
        self.dismiss()


class EditPopup(Popup):
    def __init__(self, logic, entry, callback, types, **kwargs):
        self.logic = logic
        self.entry = entry
        self.callback = callback
        self.types = types
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        layout.add_widget(Label(text="Tipo de receta:"))

        self.spinner = Spinner(
            text=entry.dish_type,
            values=types,
            size_hint=(1, None),
            height=44
        )
        layout.add_widget(self.spinner)

        layout.add_widget(Label(text="Cantidad:"))
        self.quantity_input = TextInput(text=str(entry.quantity), multiline=False, input_filter="int")
        layout.add_widget(self.quantity_input)

        btn_layout = BoxLayout(size_hint=(1, None), height=50)
        btn_cancel = Button(text="Cancelar")
        btn_cancel.bind(on_release=self.dismiss)
        btn_ok = Button(text="Actualizar")
        btn_ok.bind(on_release=self.on_ok)
        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_ok)
        layout.add_widget(btn_layout)

        self.content = layout

    def on_ok(self, *args):
        old_type = self.entry.dish_type
        new_type = self.spinner.text
        new_quantity = self.quantity_input.text.strip()
        if not new_quantity:
            self.dismiss()
            return

        if self.callback:
            self.callback(old_type, new_type, new_quantity)
        self.dismiss()


if __name__ == '__main__':
    CocinaApp().run()
