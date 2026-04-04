# PyInterface.py
import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
from io import BytesIO
import warnings
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_LEFT

from tkinter import messagebox

class CocinaArguinyano:
    def __init__(self, master):
        # Configuración de rutas
        self.EXCEL_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/main/CocinaArguinyano.xlsx"
        response = requests.get(self.EXCEL_URL)
        print(f"Status: {response.status_code}")
        print(f"URL probada: {self.EXCEL_URL}")
        print(f"Primeros 100 bytes: {response.content[:100]}")

        self.recipes_table = self.load_recipes()
        self.selected_dishes = {}
        self.actual_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    
        self.master = master
        master.title("Cocina Rápida")

        self.label = tk.Label(master, text="¡Bienvenid@ a la Cocina Rápida!")
        self.label.pack()
        
        # Create frame for table
        self.frame = tk.Frame(master)
        self.frame.pack(pady=10)

        # Create table with columns
        self.tree = ttk.Treeview(self.frame, columns=("Tipo de plato", "Cantidad"), height=10)
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("Tipo de plato", anchor=tk.W, width=150)
        self.tree.column("Cantidad", anchor=tk.W, width=150)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("Tipo de plato", text="Tipo de plato", anchor=tk.W)
        self.tree.heading("Cantidad", text="Cantidad", anchor=tk.W)
        self.tree.pack()

        # Create frame for buttons
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=10)

        self.add_button = tk.Button(self.button_frame, text="Añadir", command=self.add_recipe)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = tk.Button(self.button_frame, text="Editar", command=self.edit_recipe)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.button_frame, text="Eliminar", command=self.delete_recipe)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        tk.Label(master, text="Generar listas:").pack(pady=5)

        # Frame para los botones de Recetas y Compra en la misma fila
        self.list_buttons_frame = tk.Frame(master)
        self.list_buttons_frame.pack(pady=5)
        self.generate_recipes = tk.Button(self.list_buttons_frame, text="Recetas", command=lambda: self.get_selected_dishes(True))
        self.generate_recipes.pack(side=tk.LEFT, padx=5)
        self.generate_shopping = tk.Button(self.list_buttons_frame, text="Compra", command=self.get_ingredients_from_dishes)
        self.generate_shopping.pack(side=tk.LEFT, padx=5)

        # Botón Ambas en la siguiente fila, centrado
        self.generate_both = tk.Button(master, text="Ambas", command=self.generate_list)
        self.generate_both.pack(pady=10)

    def load_recipes(self):
        print("Cargando recetas...")
        """Lee XLSX directamente desde GitHub raw URL"""
        try:
            # Método 1: directo con pandas (funciona muchas veces)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                return pd.read_excel(self.EXCEL_URL, sheet_name=None)
            
        except:
            # Método 2: requests + BytesIO (100% fiable para XLSX)
            response = requests.get(self.EXCEL_URL)
            response.raise_for_status()  # Lanza error si falla
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                return pd.read_excel(BytesIO(response.content), sheet_name=None)
        
    def display_recipes(self):
        # Limpiar tabla antes de mostrar nuevas recetas
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Mostrar recetas en la tabla
        for sheet_name, df in self.recipes_table.items():
            if sheet_name not in ('Ingredientes', 'Unidades'):
                for index, row in df.iterrows():
                    self.tree.insert("", "end", values=(row['Nombre'], row['Ingredientes']))

    def add_recipe(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("Añadir Receta")
        add_window.geometry("400x200")
        
        tk.Label(add_window, text="Tipo de Receta:").pack(pady=5)
        recipe_types = [sheet for sheet in self.recipes_table.keys() if sheet not in ('Ingredientes', 'Unidades')]
        recipe_combo = ttk.Combobox(add_window, values=recipe_types, width=37)
        recipe_combo.pack(pady=5)
        
        tk.Label(add_window, text="Número de platos:").pack(pady=5)
        cantidad_entry = tk.Entry(add_window, width=40)
        cantidad_entry.pack(pady=5)
        
        '''def save_recipe():
            recipe_type = recipe_combo.get()
            cantidad = cantidad_entry.get()
            
            if recipe_type and cantidad:
                try:
                    cantidad = int(cantidad)
                    self.tree.insert("", "end", values=(recipe_type, cantidad, ""))
                    add_window.destroy()
                    self.selected_dishes[recipe_type] = cantidad
                except ValueError:
                    print("Por favor, ingresa un número válido")
            else:
                print("Por favor, completa todos los campos")'''
        def save_recipe():
            recipe_type = recipe_combo.get()
            cantidad = cantidad_entry.get()

            if not recipe_type or not cantidad:
                print("Por favor, completa todos los campos")
                return

            valid, result = self.validate_recipe_amount(recipe_type, cantidad)
            if not valid:
                print(result)
                return

            cantidad = result
            self.tree.insert("", "end", values=(recipe_type, cantidad, ""))
            self.selected_dishes[recipe_type] = cantidad
            add_window.destroy()
        
        save_button = tk.Button(add_window, text="Guardar", command=save_recipe)
        save_button.pack(pady=10)

    def edit_recipe(self):
        selected = self.tree.selection()
        if not selected:
            print("No hay receta seleccionada para editar")
            return

        item = self.tree.item(selected[0])
        values = item['values']

        edit_window = tk.Toplevel(self.master)
        edit_window.title("Editar Receta")
        edit_window.geometry("400x300")

        tk.Label(edit_window, text="Tipo de Receta:").pack(pady=5)
        recipe_types = [sheet for sheet in self.recipes_table.keys() if sheet not in ('Ingredientes', 'Unidades')]
        recipe_combo = ttk.Combobox(edit_window, values=recipe_types, width=37)
        recipe_combo.pack(pady=5)
        recipe_combo.set(values[0])  # Prellenar con el valor actual
        
        tk.Label(edit_window, text="Número de platos:").pack(pady=5)
        cantidad_entry = tk.Entry(edit_window, width=40)
        cantidad_entry.pack(pady=5)
        cantidad_entry.insert(0, values[1])  # Prellenar con la cantidad actual

        '''def update_recipe():
            nombre = recipe_combo.get()
            cantidad = int(cantidad_entry.get())

            if nombre and cantidad:
                self.tree.delete(selected[0])
                self.tree.insert("", "end", values=(nombre, cantidad, ""))
                self.selected_dishes[nombre] = cantidad
                edit_window.destroy()
            else:
                print("Por favor, completa todos los campos")'''
        def update_recipe():
            nombre = recipe_combo.get()
            cantidad = cantidad_entry.get()

            if not nombre or not cantidad:
                print("Por favor, completa todos los campos")
                return

            valid, result = self.validate_recipe_amount(nombre, cantidad)
            if not valid:
                print(result)
                return

            cantidad = result
            self.tree.delete(selected[0])
            self.tree.insert("", "end", values=(nombre, cantidad, ""))
            self.selected_dishes[nombre] = cantidad
            edit_window.destroy()

        update_button = tk.Button(edit_window, text="Actualizar", command=update_recipe)
        update_button.pack(pady=10)

    # Comprobación de la cantidad de recetas solicitadas y existentes, en caso de que se hayan solicitado más de las existentes se limita la cantidad devuelta
    def validate_recipe_amount(self, recipe_type, cantidad):
        if recipe_type not in self.recipes_table:
            return False, f"No existe el tipo de receta '{recipe_type}'"

        try:
            cantidad = int(cantidad)
        except ValueError:
            return False, "Por favor, ingresa un número válido"

        if cantidad < 1:
            return False, "La cantidad debe ser mayor que 0"

        df_plate = self.recipes_table[recipe_type].copy()
        df_plate["Plato"] = df_plate["Plato"].ffill()
        max_recetas = df_plate["Plato"].drop_duplicates().dropna().shape[0]

        if cantidad > max_recetas:
            messagebox.showwarning(
                "Cantidad ajustada",
                f"Se están solicitando {cantidad} platos y solo existen {max_recetas} platos almacenados. "
                f"Se aplicará la cantidad máxima existente a su selección."
            )
            return True, max_recetas

        return True, cantidad

    def delete_recipe(self):
        # Eliminamos la receta seleccionada
        selected = self.tree.selection()
        if not selected:
            print("No hay receta seleccionada para eliminar")
            return
        self.tree.delete(selected[0])

    # Esta función genera un pdf en formato tabla, concretamente para la lista de ingredientes
    def generate_tabled_pdf(self, from_df, title):          
        # Generamos un PDF a partir de un DataFrame (placeholder)
        # Create PDF document
        pdf_file = fr".\{title}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        elements = []

        # Convert DataFrame to table data
        data = [from_df.columns.tolist()] + from_df.values.tolist()
        table = Table(data)

        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        doc.build(elements)
        print(f"PDF generado: {pdf_file}")
    
    def register_calibri(self):
        candidates = [
            r"C:\Windows\Fonts\calibri.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
        ]

        regular = candidates[0]
        bold = candidates[1]

        if os.path.exists(regular):
            pdfmetrics.registerFont(TTFont("Calibri", regular))
        if os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Calibri-Bold", bold))

    # Esta función genera un PDF con formato de receta, incluyendo ingredientes y elaboración    
    def generate_recipes_pdf(self, dishes_df, title):
        pdf_file = fr".\{title}.pdf"
        self.register_calibri()

        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=letter,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="RecipeTitle",
            parent=styles["Heading1"],
            fontName="Calibri-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=12,
            alignment=TA_LEFT
        )

        subtitle_style = ParagraphStyle(
            name="RecipeSubtitle",
            parent=styles["Heading2"],
            fontName="Calibri",
            fontSize=14,
            leading=18,
            spaceBefore=8,
            spaceAfter=6,
            alignment=TA_LEFT
        )

        body_style = ParagraphStyle(
            name="RecipeBody",
            parent=styles["BodyText"],
            fontName="Calibri",
            fontSize=12,
            leading=16,
            spaceAfter=8,
            alignment=TA_LEFT
        )

        story = []

        for i, row in dishes_df.iterrows():
            recipe_name = str(row.get("Plato", "")).strip()
            elaboration = str(row.get("Elaboración", "")).strip()

            plate_type = str(row.get("Tipo", "")).strip()
            df_plate = self.recipes_table[plate_type].copy()
            df_plate["Plato"] = df_plate["Plato"].ffill()

            from xml.sax.saxutils import escape
            import pandas as pd

            recipe_rows = df_plate[df_plate["Plato"] == recipe_name].copy()

            ingredient_lines = []
            for _, ing_row in recipe_rows[["Ingredientes", "Cantidades", "Unidades"]].iterrows():
                ingrediente = "" if pd.isna(ing_row["Ingredientes"]) else str(ing_row["Ingredientes"]).strip()
                cantidad = "" if pd.isna(ing_row["Cantidades"]) else str(ing_row["Cantidades"]).strip()
                unidad = "" if pd.isna(ing_row["Unidades"]) else f"[{str(ing_row['Unidades']).strip()}] "

                if not ingrediente:
                    continue

                partes = [p for p in [cantidad, unidad, ingrediente] if p]
                ingredient_lines.append(f"• {' '.join(partes)}")

            ingredients_text = "<br/>".join(escape(line) for line in ingredient_lines)

            story.append(Paragraph(recipe_name, title_style))
            story.append(Spacer(1, 8))

            story.append(Paragraph("Ingredientes", subtitle_style))
            story.append(Paragraph(ingredients_text if ingredients_text else "Sin ingredientes.", body_style))
            story.append(Spacer(1, 10))

            story.append(Paragraph("Elaboración", subtitle_style))
            story.append(Paragraph(elaboration if elaboration else "Sin elaboración.", body_style))

            if i < len(dishes_df) - 1:
                story.append(PageBreak())

        doc.build(story)
        print(f"PDF generado: {pdf_file}")

    def generate_list(self):
        # Generamos ambas listas
        ingredients_result, dishes_result = self.get_ingredients_and_dishes()

        # Almacenamos ambas listas
        self.generate_recipes_pdf(dishes_result, f"Recetas-{self.actual_date}")
        self.generate_tabled_pdf(ingredients_result, f"Compra-{self.actual_date}")

        return ingredients_result, dishes_result

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
            elaboration_col = 'Elaboración' if 'Elaboración' in df_selected.columns else 'Elaboracion'
            plate_info = df_selected.groupby('Plato', as_index=False).first()
            
            plate_info['Tipo'] = plate_type
            plate_info['Elaboración'] = plate_info[elaboration_col].astype('string')
            selected_dishes.extend(plate_info[['Tipo', 'Plato', 'Elaboración']].to_dict('records'))

        # Almacenamos los platos seleccionados
        dishes_result = pd.DataFrame(selected_dishes) if selected_dishes else pd.DataFrame()
        if saving_dishes:
            '''
            Debería ajustar el formato del texto de la elaboración de las recetas para que se vea mejor en el PDF
            '''
            self.generate_recipes_pdf(dishes_result, f"Recetas-{self.actual_date}")
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
        
        # Almacenamos los ingredientes seleccionados
        self.generate_tabled_pdf(ingredients_result, f"Compra-{self.actual_date}")
        return ingredients_result

    def get_ingredients_and_dishes(self):
        """Retorna tanto los platos como sus ingredientes"""
        dishes_result = self.get_selected_dishes(True)
        ingredients_result = self.get_ingredients_from_dishes()
        return ingredients_result, dishes_result

        
if __name__ == "__main__":
    root = tk.Tk()
    app = CocinaArguinyano(root)
    root.mainloop()