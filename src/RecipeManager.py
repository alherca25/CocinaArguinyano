import customtkinter as ctk
import json
import os
import tkinter.messagebox as messagebox

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
# Ahora la base de datos local está en la carpeta clonada BaseDatosRecetas
JSON_FILE = os.path.join(os.path.dirname(script_dir), "..", "BaseDatosRecetas", "CocinaArguinyano.json")
class IngredientRow(ctk.CTkFrame):
    def __init__(self, master, delete_callback, init_data=None, **kwargs):
        super().__init__(master, **kwargs)
        self.delete_callback = delete_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=0)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Nombre ingrediente")
        self.name_entry.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.qty_entry = ctk.CTkEntry(self, placeholder_text="Cantidad (ej: 1, 0.5)")
        self.qty_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.unit_entry = ctk.CTkEntry(self, placeholder_text="Unidad (ej: gr, ud)")
        self.unit_entry.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        self.del_btn = ctk.CTkButton(self, text="X", width=30, fg_color="#c0392b", hover_color="#e74c3c", command=self.on_delete)
        self.del_btn.grid(row=0, column=3, padx=2, pady=2)
        
        if init_data:
            self.name_entry.insert(0, init_data.get("nombre", ""))
            self.qty_entry.insert(0, str(init_data.get("cantidad", "")))
            self.unit_entry.insert(0, str(init_data.get("unidad", "")))

    def on_delete(self):
        self.delete_callback(self)
        self.destroy()

    def get_data(self):
        return {
            "nombre": self.name_entry.get().strip(),
            "cantidad": self.qty_entry.get().strip(),
            "unidad": self.unit_entry.get().strip()
        }


class RecipeManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        import platform
        if platform.system() == "Windows":
            try:
                import ctypes
                myappid = 'alherca25.cocina_arguinyano.recipemanager.1.0'
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

        ico_path = resource_path("assets/edit_logo.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception as e:
                print(f"Error al cargar logo ico: {e}")
        
        self.title("Gestor de Recetas - Cocina Rápida")
        self.geometry("800x700")
        
        self.db = {}
        self.load_db()
        
        self.categories = list(self.db.keys())
        if not self.categories:
            self.categories = ["Sopas", "Cremas", "Verduras", "Legumbres", "Huevos", "Arroces", "Pastas", "Carnes", "Pescados", "Postres", "Panes"]
            for cat in self.categories:
                self.db[cat] = []
        
        self.mode = "add" # 'add' or 'edit'
        self.current_edit_index = -1
        
        self.setup_ui()

    def load_db(self):
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la base de datos: {e}")
        else:
            messagebox.showwarning("Aviso", "No se encontró el archivo JSON, se creará uno nuevo al guardar.")
            self.db = {}

    def save_db(self):
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Base de datos guardada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos: {e}")

    def show_help(self):
        messagebox.showinfo("Ayuda / Soporte", "En caso de necesitar ayuda/soporte o tener alguna sugerencia, mande un correo a alherca25@gmail.com")

    def setup_ui(self):
        self.help_btn = ctk.CTkButton(self, text="?", width=30, height=30, corner_radius=15, font=("Arial", 16, "bold"), command=self.show_help)
        self.help_btn.place(relx=0.95, rely=0.02, anchor="ne")

        # Top Bar
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.mode_switch = ctk.CTkSegmentedButton(self.top_frame, values=["Añadir Receta", "Editar Receta"], command=self.change_mode)
        self.mode_switch.pack(pady=10)
        self.mode_switch.set("Añadir Receta")
        
        # Search / Select (Only visible in edit mode)
        self.edit_frame = ctk.CTkFrame(self)
        
        self.cat_select_lbl = ctk.CTkLabel(self.edit_frame, text="Categoría:")
        self.cat_select_lbl.grid(row=0, column=0, padx=10, pady=5)
        self.cat_select = ctk.CTkComboBox(self.edit_frame, values=self.categories, command=self.on_edit_category_change)
        self.cat_select.grid(row=0, column=1, padx=10, pady=5)
        
        self.recipe_select_lbl = ctk.CTkLabel(self.edit_frame, text="Receta:")
        self.recipe_select_lbl.grid(row=0, column=2, padx=10, pady=5)
        self.recipe_select = ctk.CTkComboBox(self.edit_frame, values=["-- Seleccione Categoría --"], command=self.on_edit_recipe_change)
        self.recipe_select.grid(row=0, column=3, padx=10, pady=5)
        
        # Form
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.form_inner = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.form_inner.pack(pady=20, padx=20, anchor="n")
        
        # Category (For Add Mode)
        self.form_cat_lbl = ctk.CTkLabel(self.form_inner, text="Categoría:")
        self.form_cat_lbl.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.form_cat = ctk.CTkComboBox(self.form_inner, values=self.categories)
        self.form_cat.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Recipe Name
        self.name_lbl = ctk.CTkLabel(self.form_inner, text="Nombre del Plato:")
        self.name_lbl.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.name_entry = ctk.CTkEntry(self.form_inner, width=300)
        self.name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Page
        self.page_lbl = ctk.CTkLabel(self.form_inner, text="Página (opcional):")
        self.page_lbl.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.page_entry = ctk.CTkEntry(self.form_inner, width=100)
        self.page_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Filters
        self.filters_frame = ctk.CTkFrame(self.form_inner, fg_color="transparent")
        self.filters_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.veg_var = ctk.BooleanVar()
        self.gf_var = ctk.BooleanVar()
        
        self.veg_chk = ctk.CTkCheckBox(self.filters_frame, text="Vegetariano", variable=self.veg_var)
        self.veg_chk.pack(side="left", padx=20)
        
        self.gf_chk = ctk.CTkCheckBox(self.filters_frame, text="Gluten Free", variable=self.gf_var)
        self.gf_chk.pack(side="left", padx=20)
        
        # Elaboration
        self.elab_lbl = ctk.CTkLabel(self.form_inner, text="Elaboración:")
        self.elab_lbl.grid(row=4, column=0, padx=10, pady=5, sticky="ne")
        self.elab_text = ctk.CTkTextbox(self.form_inner, width=400, height=150)
        self.elab_text.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # Ingredients Section
        self.ings_lbl = ctk.CTkLabel(self.form_inner, text="Ingredientes", font=("Arial", 16, "bold"))
        self.ings_lbl.grid(row=5, column=0, columnspan=2, pady=(20,5))
        
        self.ings_container = ctk.CTkFrame(self.form_inner, fg_color="transparent")
        self.ings_container.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10)
        self.ings_container.grid_columnconfigure(0, weight=1)
        
        self.ingredient_rows = []
        
        self.add_ing_btn = ctk.CTkButton(self.form_inner, text="+ Añadir Ingrediente", command=self.add_ingredient_row)
        self.add_ing_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Action Buttons Frame
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=20, pady=10)

        # Save Button
        self.save_btn = ctk.CTkButton(self.actions_frame, text="Guardar Receta", height=40, font=("Arial", 14, "bold"), command=self.save_recipe)
        self.save_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        # Delete Button (Hidden by default)
        self.delete_btn = ctk.CTkButton(self.actions_frame, text="Eliminar Receta", height=40, font=("Arial", 14, "bold"), fg_color="#c0392b", hover_color="#e74c3c", command=self.delete_recipe)
        
        # Initial ingredient row
        self.add_ingredient_row()

    def add_ingredient_row(self, init_data=None):
        row = IngredientRow(self.ings_container, self.remove_ingredient_row, init_data)
        row.pack(fill="x", pady=2)
        self.ingredient_rows.append(row)
        
    def remove_ingredient_row(self, row):
        if row in self.ingredient_rows:
            self.ingredient_rows.remove(row)

    def change_mode(self, mode):
        self.mode = "add" if mode == "Añadir Receta" else "edit"
        if self.mode == "edit":
            self.edit_frame.pack(fill="x", padx=10, pady=0, after=self.top_frame)
            self.form_cat.configure(state="disabled")
            self.delete_btn.pack(side="left", fill="x", expand=True, padx=5)
            self.clear_form()
            self.on_edit_category_change(self.cat_select.get())
        else:
            self.edit_frame.pack_forget()
            self.form_cat.configure(state="normal")
            self.delete_btn.pack_forget()
            self.clear_form()

    def clear_form(self):
        self.name_entry.delete(0, 'end')
        self.page_entry.delete(0, 'end')
        self.elab_text.delete("1.0", 'end')
        self.veg_var.set(False)
        self.gf_var.set(False)
        
        for row in self.ingredient_rows:
            row.destroy()
        self.ingredient_rows.clear()
        
        if self.mode == "add":
            self.add_ingredient_row()
            
        self.current_edit_index = -1

    def on_edit_category_change(self, choice):
        if choice in self.db:
            recipes = self.db[choice]
            names = [r.get("nombre", f"Receta {i}") for i, r in enumerate(recipes)]
            if not names:
                names = ["-- Sin recetas --"]
            self.recipe_select.configure(values=names)
            self.recipe_select.set(names[0])
            if recipes:
                self.on_edit_recipe_change(names[0])
            else:
                self.clear_form()

    def on_edit_recipe_change(self, choice):
        cat = self.cat_select.get()
        if cat in self.db:
            recipes = self.db[cat]
            for i, r in enumerate(recipes):
                if r.get("nombre") == choice:
                    self.current_edit_index = i
                    self.load_recipe_to_form(r)
                    return

    def load_recipe_to_form(self, recipe):
        idx = self.current_edit_index
        self.clear_form()
        self.current_edit_index = idx
        
        self.form_cat.set(self.cat_select.get())
        self.name_entry.insert(0, recipe.get("nombre", ""))
        self.page_entry.insert(0, recipe.get("pagina", ""))
        self.elab_text.insert("1.0", recipe.get("elaboracion", ""))
        
        filtros = recipe.get("filtros", {})
        self.veg_var.set(filtros.get("vegetariano", False))
        self.gf_var.set(filtros.get("gluten_free", False))
        
        for ing in recipe.get("ingredientes", []):
            self.add_ingredient_row(ing)
            
        if not recipe.get("ingredientes"):
            self.add_ingredient_row()

    def save_recipe(self):
        cat = self.form_cat.get()
        if self.mode == "edit":
            cat = self.cat_select.get()
            
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "El nombre del plato no puede estar vacío.")
            return
            
        # Collect ingredients
        ings = []
        for row in self.ingredient_rows:
            data = row.get_data()
            if data["nombre"]: # Only add if name is not empty
                ings.append(data)
                
        recipe = {
            "nombre": name,
            "pagina": self.page_entry.get().strip(),
            "elaboracion": self.elab_text.get("1.0", "end").strip(),
            "filtros": {
                "vegetariano": self.veg_var.get(),
                "gluten_free": self.gf_var.get()
            },
            "ingredientes": ings
        }
        
        if self.mode == "add":
            if cat not in self.db:
                self.db[cat] = []
            self.db[cat].append(recipe)
        else:
            if self.current_edit_index >= 0 and cat in self.db:
                self.db[cat][self.current_edit_index] = recipe
            else:
                messagebox.showerror("Error", "No hay una receta seleccionada para editar.")
                return
                
        self.save_db()
        
        if self.mode == "add":
            self.clear_form()
            messagebox.showinfo("Listo", "Receta añadida.")
        else:
            # Refresh edit dropdown
            self.on_edit_category_change(cat)
            self.recipe_select.set(name)

    def delete_recipe(self):
        cat = self.cat_select.get()
        name = self.name_entry.get().strip()
        
        if self.current_edit_index < 0 or cat not in self.db:
            messagebox.showwarning("Aviso", "No hay ninguna receta seleccionada para eliminar.")
            return
            
        confirm = messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de que deseas eliminar la receta '{name}' de la categoría '{cat}'?\n\nEsta acción no se puede deshacer.")
        if confirm:
            del self.db[cat][self.current_edit_index]
            self.save_db()
            messagebox.showinfo("Listo", "Receta eliminada correctamente.")
            self.on_edit_category_change(cat)

if __name__ == "__main__":
    app = RecipeManager()
    app.mainloop()
