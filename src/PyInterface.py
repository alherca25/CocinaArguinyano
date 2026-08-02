import customtkinter as ctk
import json
import requests
import warnings
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import random
from datetime import datetime

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_LEFT

import tkinter.messagebox as messagebox

import functions  # Archivo de utilidades comunes

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RecipeRow(ctk.CTkFrame):
    def __init__(self, master, recipe_type, quantity, **kwargs):
        super().__init__(master, **kwargs)
        self.recipe_type = recipe_type
        self.quantity = quantity
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.type_lbl = ctk.CTkLabel(self, text=recipe_type, font=("Arial", 14))
        self.type_lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.qty_lbl = ctk.CTkLabel(self, text=str(quantity), font=("Arial", 14))
        self.qty_lbl.grid(row=0, column=1, padx=10, pady=5, sticky="e")

class CocinaArguinyano(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        import platform
        if platform.system() == "Windows":
            try:
                import ctypes
                myappid = 'alherca25.cocina_arguinyano.pyinterface.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass
                
        import tkinter as tk
        from PIL import Image, ImageTk
        import os
        import sys
        
        def resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
                return os.path.join(base_path, os.path.basename(relative_path))
            except Exception:
                base_path = os.path.abspath(os.path.dirname(__file__))
                base_path = os.path.dirname(base_path)
                return os.path.join(base_path, relative_path)

        ico_path = resource_path("assets/main_logo.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception as e:
                print(f"Error al cargar logo ico: {e}")
                
        self.JSON_MAIN_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/main/CocinaArguinyano.json"
        self.JSON_DEV_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/_dev/data/CocinaArguinyano.json"
        
        self.recipes_table = self.load_recipes()
        self.selected_dishes = {}
        self.actual_date = datetime.now().strftime("%Y-%m-%d")
    
        self.title("Recetario - Cocina Rápida")
        self.geometry("600x650")

        self.setup_ui()
        
    def show_help(self):
        messagebox.showinfo("Ayuda / Soporte", "En caso de necesitar ayuda/soporte o tener alguna sugerencia, mande un correo a alherca25@gmail.com")
        
    def setup_ui(self):
        self.help_btn = ctk.CTkButton(self, text="?", width=30, height=30, corner_radius=15, font=("Arial", 16, "bold"), command=self.show_help)
        self.help_btn.place(relx=0.95, rely=0.02, anchor="ne")

        self.title_lbl = ctk.CTkLabel(self, text="¡Bienvenid@ a la Cocina Rápida!", font=("Arial", 20, "bold"))
        self.title_lbl.pack(pady=20)
        
        # Table equivalent (Scrollable Frame)
        self.table_header = ctk.CTkFrame(self, fg_color="transparent")
        self.table_header.pack(fill="x", padx=40)
        self.table_header.grid_columnconfigure(0, weight=1)
        self.table_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.table_header, text="Tipo de plato", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(self.table_header, text="Cantidad", font=("Arial", 14, "bold")).grid(row=0, column=1, sticky="e", padx=10)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=200)
        self.scroll_frame.pack(fill="x", padx=40, pady=(5, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.row_widgets = {} # category -> RecipeRow widget
        
        # Action Buttons
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)
        
        self.add_button = ctk.CTkButton(self.button_frame, text="Añadir", width=120, command=self.add_recipe)
        self.add_button.pack(side="left", padx=10)
        
        self.edit_button = ctk.CTkButton(self.button_frame, text="Editar", width=120, command=self.edit_recipe)
        self.edit_button.pack(side="left", padx=10)
        
        self.delete_button = ctk.CTkButton(self.button_frame, text="Eliminar", width=120, fg_color="#c0392b", hover_color="#e74c3c", command=self.delete_recipe)
        self.delete_button.pack(side="left", padx=10)
        
        # Filter Frame
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(pady=15)
        
        ctk.CTkLabel(self.filter_frame, text="Filtro:", font=("Arial", 14)).pack(side="left", padx=10)
        self.filter_combo = ctk.CTkComboBox(self.filter_frame, values=["Todo", "Vegetariano", "Gluten Free"], state="readonly", width=200)
        self.filter_combo.pack(side="left", padx=10)
        self.filter_combo.set("Todo")
        
        # Generation Buttons
        ctk.CTkLabel(self, text="Generar listas:", font=("Arial", 14)).pack(pady=(10, 5))
        
        self.list_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_buttons_frame.pack(pady=5)
        
        self.generate_recipes_btn = ctk.CTkButton(self.list_buttons_frame, text="Recetas", width=120, command=lambda: self.get_selected_dishes(True))
        self.generate_recipes_btn.pack(side="left", padx=10)
        
        self.generate_shopping_btn = ctk.CTkButton(self.list_buttons_frame, text="Compra", width=120, command=self.get_ingredients_from_dishes)
        self.generate_shopping_btn.pack(side="left", padx=10)
        
        self.generate_both_btn = ctk.CTkButton(self, text="Generar Ambas", height=40, font=("Arial", 14, "bold"), command=self.generate_list)
        self.generate_both_btn.pack(pady=20)
        
    def refresh_table(self):
        for w in self.row_widgets.values():
            w.destroy()
        self.row_widgets.clear()
        
        for idx, (cat, qty) in enumerate(self.selected_dishes.items()):
            row = RecipeRow(self.scroll_frame, cat, qty, fg_color=("gray75", "gray25") if idx % 2 == 0 else "transparent")
            row.grid(row=idx, column=0, sticky="ew", pady=2)
            self.row_widgets[cat] = row

    def get_cache_path(self):
        home = os.path.expanduser("~")
        cache_dir = os.path.join(home, ".cocinarapida")
        try:
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, "CocinaArguinyano.json")
        except Exception as e:
            print(f"Error al crear directorio de caché: {e}")
            return None

    def load_recipes(self):
        print("Cargando recetas JSON...")
        cache_path = self.get_cache_path()
        content = None

        # 1. Intentar descargar de GitHub
        try:
            print("Intentando descargar de GitHub...")
            try:
                recipes = functions.load_recipes(self.JSON_MAIN_URL, is_local=False)
            except:
                recipes = functions.load_recipes(self.JSON_DEV_URL, is_local=False)
            if cache_path:
                try:
                    with open(cache_path, "w", encoding='utf-8') as f:
                        json.dump(recipes, f, ensure_ascii=False, indent=2)
                    print(f"Caché de JSON actualizada en: {cache_path}")
                except Exception as cache_err:
                    print(f"No se pudo escribir en caché: {cache_err}")
            return recipes
        except Exception as exc:
            print(f"Error al descargar de GitHub: {exc}. Buscando copia local/cacheada...")

        # 2. Caché local
        if cache_path and os.path.exists(cache_path):
            try:
                return functions.load_recipes(cache_path, is_local=True)
            except Exception as cache_read_err:
                print(f"Fallo al leer caché: {cache_read_err}")

        # 3. Archivo local en script_dir
        local_file = "data/CocinaArguinyano.json"
        if not os.path.exists(local_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_file = os.path.join(os.path.dirname(script_dir), "data", "CocinaArguinyano.json")
            
        if os.path.exists(local_file):
            print(f"Cargado JSON original local: {local_file}")
            return functions.load_recipes(local_file, is_local=True)
            
        raise FileNotFoundError("No se encontró JSON local ni en GitHub.")

    def add_recipe(self):
        self._open_modal("Añadir Receta")

    def edit_recipe(self):
        if not self.selected_dishes:
            messagebox.showwarning("Aviso", "No hay ninguna receta en la lista para editar.")
            return
        self._open_modal("Editar Receta", edit_mode=True)

    def _open_modal(self, title, edit_mode=False):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry("400x250")
        modal.transient(self)
        modal.grab_set()
        
        modal_frame = ctk.CTkFrame(modal, fg_color="transparent")
        modal_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(modal_frame, text="Tipo de Receta:").pack(pady=5)
        recipe_types = list(self.selected_dishes.keys()) if edit_mode else list(self.recipes_table.keys())
        
        recipe_combo = ctk.CTkComboBox(modal_frame, values=recipe_types, width=250)
        recipe_combo.pack(pady=5)
        
        if recipe_types:
            recipe_combo.set(recipe_types[0])
            
        ctk.CTkLabel(modal_frame, text="Número de platos:").pack(pady=5)
        cantidad_entry = ctk.CTkEntry(modal_frame, width=250)
        cantidad_entry.pack(pady=5)
        
        if edit_mode and recipe_types:
            cantidad_entry.insert(0, str(self.selected_dishes[recipe_types[0]]))
            
            def on_combo_change(choice):
                cantidad_entry.delete(0, 'end')
                if choice in self.selected_dishes:
                    cantidad_entry.insert(0, str(self.selected_dishes[choice]))
                    
            recipe_combo.configure(command=on_combo_change)
        
        def save_modal():
            recipe_type = recipe_combo.get()
            cantidad = cantidad_entry.get().strip()

            if not recipe_type or not cantidad:
                messagebox.showwarning("Aviso", "Por favor, completa todos los campos.")
                return

            valid, result = self.validate_recipe_amount(recipe_type, cantidad)
            if not valid:
                messagebox.showwarning("Aviso", result)
                return

            self.selected_dishes[recipe_type] = result
            self.refresh_table()
            modal.destroy()
        
        btn_text = "Actualizar" if edit_mode else "Añadir"
        ctk.CTkButton(modal_frame, text=btn_text, command=save_modal).pack(pady=15)

    def validate_recipe_amount(self, recipe_type, cantidad):
        if recipe_type not in self.recipes_table:
            return False, f"No existe el tipo de receta '{recipe_type}'"

        try:
            cantidad = int(cantidad)
        except ValueError:
            return False, "Por favor, ingresa un número válido"

        if cantidad < 1:
            return False, "La cantidad debe ser mayor que 0"

        active_filter = self.filter_combo.get()
        
        valid_recipes = functions.filter_recipes(self.recipes_table[recipe_type], active_filter)
        max_recetas = len(valid_recipes)

        if cantidad > max_recetas:
            messagebox.showwarning(
                "Cantidad ajustada",
                f"Se están solicitando {cantidad} platos pero con el filtro '{active_filter}' "
                f"solo existen {max_recetas} platos. Se aplicará la cantidad máxima."
            )
            return True, max_recetas

        return True, cantidad

    def delete_recipe(self):
        if not self.selected_dishes:
            messagebox.showwarning("Aviso", "No hay ninguna receta en la lista para eliminar.")
            return
            
        modal = ctk.CTkToplevel(self)
        modal.title("Eliminar Receta")
        modal.geometry("400x200")
        modal.transient(self)
        modal.grab_set()
        
        modal_frame = ctk.CTkFrame(modal, fg_color="transparent")
        modal_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(modal_frame, text="Selecciona la categoría a eliminar:").pack(pady=5)
        recipe_types = list(self.selected_dishes.keys())
        
        recipe_combo = ctk.CTkComboBox(modal_frame, values=recipe_types, width=250)
        recipe_combo.pack(pady=10)
        if recipe_types:
            recipe_combo.set(recipe_types[0])
            
        def perform_delete():
            cat = recipe_combo.get()
            if cat in self.selected_dishes:
                del self.selected_dishes[cat]
                self.refresh_table()
                messagebox.showinfo("Éxito", f"Categoría '{cat}' eliminada.")
                modal.destroy()
            else:
                messagebox.showwarning("Aviso", "La categoría no está en la lista.")
                
        ctk.CTkButton(modal_frame, text="Eliminar", fg_color="#c0392b", hover_color="#e74c3c", command=perform_delete).pack(pady=15)

    def generate_tabled_pdf(self, headers, data, title):          
        pdf_file = fr".\{title}.pdf"
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        elements = []

        table_data = [headers] + data
        table = Table(table_data)

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
        messagebox.showinfo("Completado", f"PDF generado: {pdf_file}")
    
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

    def generate_recipes_pdf(self, selected_dishes_list, title):
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

        from xml.sax.saxutils import escape

        for i, recipe in enumerate(selected_dishes_list):
            recipe_name = str(recipe.get("nombre", "")).strip()
            elaboration = str(recipe.get("elaboracion", "")).strip()

            ingredient_lines = []
            for ing in recipe.get("ingredientes", []):
                formatted_ing = functions.format_ingredient(ing)
                if formatted_ing:
                    ingredient_lines.append(f"• {formatted_ing}")

            ingredients_text = "<br/>".join(escape(line) for line in ingredient_lines)

            story.append(Paragraph(recipe_name, title_style))
            story.append(Spacer(1, 8))

            story.append(Paragraph("Ingredientes", subtitle_style))
            story.append(Paragraph(ingredients_text if ingredients_text else "Sin ingredientes.", body_style))
            story.append(Spacer(1, 10))

            story.append(Paragraph("Elaboración", subtitle_style))
            story.append(Paragraph(elaboration if elaboration else "Sin elaboración.", body_style))

            if i < len(selected_dishes_list) - 1:
                story.append(PageBreak())

        doc.build(story)
        print(f"PDF generado: {pdf_file}")
        messagebox.showinfo("Completado", f"PDF generado: {pdf_file}")

    def generate_list(self):
        ingredients_result, dishes_result = self.get_ingredients_and_dishes()

        if dishes_result:
            self.generate_recipes_pdf(dishes_result, f"Recetas-{self.actual_date}")
        if ingredients_result:
            self.generate_tabled_pdf(["Ingrediente", "Cantidad", "Unidad"], ingredients_result, f"Compra-{self.actual_date}")

        return ingredients_result, dishes_result

    def get_selected_dishes(self, saving_dishes=False):
        """Selecciona y retorna una lista de recetas (dicts)"""
        active_filter = self.filter_combo.get()
        selected_recipes = []

        for plate_type, desired_num in self.selected_dishes.items():
            if plate_type not in self.recipes_table:
                print(f'No se han encontrado recetas de {plate_type}')
                continue
            
            if desired_num <= 0:
                continue

            dishes, limited = functions.select_random_dishes(self.recipes_table, plate_type, desired_num, active_filter)
            
            print(f'\nSeleccionando {len(dishes)} platos de tipo {plate_type}...\n')
            selected_recipes.extend(dishes)

        if saving_dishes and selected_recipes:
            self.generate_recipes_pdf(selected_recipes, f"Recetas-{self.actual_date}")
            
        return selected_recipes

    def get_ingredients_from_dishes(self, dishes_list=None, saving=True):
        if dishes_list is None:
            dishes_list = self.get_selected_dishes(False)

        # Agrupar ingredientes
        # Al no usar pandas, lo hacemos manual. Agruparemos por nombre, sumando cantidades numéricas si es posible
        from collections import defaultdict
        
        # Para agrupar, la clave será el nombre del ingrediente. 
        # Intentaremos sumar las cantidades si son float/int.
        grouped_ings = {}

        for recipe in dishes_list:
            for ing in recipe.get("ingredientes", []):
                nombre = str(ing.get("nombre", "")).strip().lower()
                if not nombre: continue
                
                # Para mostrar, usamos el formato original (Capitalizado o como viniese, guardamos el original)
                original_nombre = str(ing.get("nombre", "")).strip()
                unidad = str(ing.get("unidad", "")).strip()
                cantidad_str = str(ing.get("cantidad", "")).strip()
                
                # Intentamos parsear la cantidad
                cantidad_val = 0.0
                is_numeric = False
                try:
                    if cantidad_str and cantidad_str.lower() != 'nan':
                        cantidad_val = float(cantidad_str)
                        is_numeric = True
                except ValueError:
                    pass
                
                key = (nombre, unidad)
                if key not in grouped_ings:
                    grouped_ings[key] = {
                        "nombre": original_nombre,
                        "cantidad": cantidad_val if is_numeric else cantidad_str,
                        "unidad": unidad,
                        "is_numeric": is_numeric
                    }
                else:
                    if is_numeric and grouped_ings[key]["is_numeric"]:
                        grouped_ings[key]["cantidad"] += cantidad_val
                    else:
                        pass

        # Construir la lista final de filas
        data_rows = []
        for v in grouped_ings.values():
            cant = v["cantidad"]
            # Si era numerico y acaba en .0, quitar decimal
            if v["is_numeric"] and float(cant).is_integer():
                cant = int(float(cant))
            data_rows.append([v["nombre"], str(cant), v["unidad"]])
            
        # Ordenar alfabéticamente
        data_rows.sort(key=lambda x: x[0].lower())

        if saving and data_rows:
            self.generate_tabled_pdf(["Ingrediente", "Cantidad", "Unidad"], data_rows, f"Compra-{self.actual_date}")
            
        return data_rows

    def get_ingredients_and_dishes(self):
        dishes_result = self.get_selected_dishes(saving_dishes=False)
        ingredients_result = self.get_ingredients_from_dishes(dishes_list=dishes_result, saving=False)
        return ingredients_result, dishes_result

if __name__ == "__main__":
    app = CocinaArguinyano()
    app.mainloop()