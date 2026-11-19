import customtkinter as ctk
import json
import os
import sys
import tkinter.messagebox as messagebox

import desktop_theme as T
import functions

T.apply_theme()

if getattr(sys, 'frozen', False):
    # Si se ejecuta como .exe compilado, sys.executable es la ruta al .exe
    base_dir = os.path.dirname(sys.executable)
else:
    # Si se ejecuta como script .py, usamos la ruta del script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Asumimos que la carpeta BaseDatosRecetas está al mismo nivel que CocinaArguinyano (o al mismo nivel que el .exe)
# Si el exe está en CocinaArguinyano/dist, entonces base_dir es dist.
# Si queremos que funcione tanto en dist como fuera, lo mejor es buscar BaseDatosRecetas
# Si base_dir es 'dist', subimos un nivel.
if os.path.basename(base_dir).lower() == "dist":
    base_dir = os.path.dirname(base_dir)

JSON_FILE = os.path.join(os.path.dirname(base_dir), "BaseDatosRecetas", "CocinaArguinyano.json")
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

        self.del_btn = T.danger_button(self, text="✕", width=34, command=self.on_delete)
        self.del_btn.grid(row=0, column=3, padx=2, pady=2)
        
        if init_data:
            self.name_entry.insert(0, init_data.get("nombre", ""))
            self.qty_entry.insert(0, functions.format_quantity(init_data.get("cantidad", "")))
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
        
        T.set_window_icon(self, "edit_logo.ico")
        self.title("Gestor de Recetas - Cocina Rápida")
        self.geometry("820x760")

        self.db = {}
        self.can_save = True   # False si el JSON existe pero no se pudo leer: no se sobrescribe
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
                    data = json.load(f)
                self.db = {cat: [functions.normalize_recipe(r) for r in recs] for cat, recs in data.items()}
            except Exception as e:
                self.can_save = False
                messagebox.showerror("Error", f"No se pudo cargar la base de datos: {e}\n\n"
                                     "Por seguridad no se permitirá guardar hasta corregir el archivo.")
        else:
            messagebox.showwarning("Aviso", "No se encontró el archivo JSON, se creará uno nuevo al guardar.")
            self.db = {}

    def save_db(self):
        """Guarda el JSON. Devuelve True si se guardó correctamente."""
        if not self.can_save:
            messagebox.showerror("Error", "La base de datos no se cargó bien; no se guardará nada.")
            return False
        try:
            os.makedirs(os.path.dirname(JSON_FILE), exist_ok=True)
            tmp = JSON_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=4, ensure_ascii=False)
            os.replace(tmp, JSON_FILE)   # escritura atómica: nunca queda un archivo a medias
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos: {e}")
            return False

    def show_help(self):
        messagebox.showinfo("Ayuda / Soporte", "En caso de necesitar ayuda/soporte o tener alguna sugerencia, mande un correo a alherca25@gmail.com")

    def setup_ui(self):
        total = sum(len(v) for v in self.db.values())
        T.header(self, "edit_logo.ico", "Gestor de Recetas",
                 f"{total} recetas · {os.path.join(os.path.basename(os.path.dirname(JSON_FILE)), os.path.basename(JSON_FILE))}",
                 on_help=self.show_help).pack(fill="x")

        # Top Bar
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.mode_switch = ctk.CTkSegmentedButton(self.top_frame, values=["Añadir Receta", "Editar Receta"], command=self.change_mode)
        self.mode_switch.pack(pady=10)
        self.mode_switch.set("Añadir Receta")
        
        # Search / Select (Only visible in edit mode)
        self.edit_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.cat_select_lbl = ctk.CTkLabel(self.edit_frame, text="Categoría:")
        self.cat_select_lbl.grid(row=0, column=0, padx=10, pady=5)
        self.cat_select = ctk.CTkComboBox(self.edit_frame, values=self.categories, command=self.on_edit_category_change)
        self.cat_select.grid(row=0, column=1, padx=10, pady=5)
        
        self.recipe_select_lbl = ctk.CTkLabel(self.edit_frame, text="Receta:")
        self.recipe_select_lbl.grid(row=0, column=2, padx=10, pady=5)
        self.recipe_select = ctk.CTkComboBox(self.edit_frame, values=["-- Seleccione Categoría --"], command=self.on_edit_recipe_change)
        self.recipe_select.grid(row=0, column=3, padx=10, pady=5)
        
        # Form
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=T.SURFACE, border_width=1, border_color=T.BORDER)
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
        
        self.gf_chk = ctk.CTkCheckBox(self.filters_frame, text="Sin gluten", variable=self.gf_var)
        self.gf_chk.pack(side="left", padx=20)
        
        # Elaboration
        self.elab_lbl = ctk.CTkLabel(self.form_inner, text="Elaboración:")
        self.elab_lbl.grid(row=4, column=0, padx=10, pady=5, sticky="ne")
        self.elab_text = ctk.CTkTextbox(self.form_inner, width=400, height=150)
        self.elab_text.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        
        # Ingredients Section
        self.ings_lbl = ctk.CTkLabel(self.form_inner, text="Ingredientes", font=(T.FONT, 16, "bold"))
        self.ings_lbl.grid(row=5, column=0, columnspan=2, pady=(20,5))
        
        self.ings_container = ctk.CTkFrame(self.form_inner, fg_color="transparent")
        self.ings_container.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10)
        self.ings_container.grid_columnconfigure(0, weight=1)
        
        self.ingredient_rows = []
        
        self.add_ing_btn = T.secondary_button(self.form_inner, text="+ Añadir Ingrediente", command=self.add_ingredient_row)
        self.add_ing_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        # Action Buttons Frame
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=20, pady=10)

        # Save Button
        self.save_btn = ctk.CTkButton(self.actions_frame, text="Guardar Receta", height=40, font=(T.FONT, 14, "bold"), command=self.save_recipe)
        self.save_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        # Delete Button (Hidden by default)
        self.delete_btn = T.danger_button(self.actions_frame, text="Eliminar Receta", height=40, font=(T.FONT, 14, "bold"), command=self.delete_recipe)
        
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
        
        # Un CTkComboBox deshabilitado no refresca el texto: se habilita, se cambia y se vuelve a bloquear.
        self.form_cat.configure(state="normal")
        self.form_cat.set(self.cat_select.get())
        self.form_cat.configure(state="disabled")
        self.name_entry.insert(0, recipe.get("nombre", ""))
        self.page_entry.insert(0, functions.format_page(recipe.get("pagina", "")))
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
        page = self.page_entry.get().strip()
        errors = []
        if not name:
            errors.append("El nombre del plato no puede estar vacío.")
        if page and not page.isdigit():
            errors.append("La página debe ser un número.")
        ings = []
        for row in self.ingredient_rows:
            data = row.get_data()
            if not data["nombre"]:
                continue
            data["cantidad"] = data["cantidad"].replace(",", ".")
            if data["cantidad"] and functions.parse_quantity(data["cantidad"]) is None:
                errors.append(f"«{data['nombre']}»: la cantidad debe ser un número (ej. 2 o 0.5).")
            ings.append(data)
        if not ings:
            errors.append("Añade al menos un ingrediente.")
        if errors:
            messagebox.showwarning("Revisa la receta", "\n".join(errors))
            return

        # Nombre repetido en la misma categoría (excepto la propia receta al editar)
        for i, r in enumerate(self.db.get(cat, [])):
            if r.get("nombre", "").strip().lower() == name.lower() and                     not (self.mode == "edit" and i == self.current_edit_index):
                messagebox.showwarning("Receta repetida", f"Ya existe «{name}» en {cat}.")
                return

        recipe = {
            "nombre": name,
            "pagina": page,
            "elaboracion": self.elab_text.get("1.0", "end").strip(),
            "filtros": {"vegetariano": bool(self.veg_var.get()), "gluten_free": bool(self.gf_var.get())},
            "ingredientes": ings,
        }

        backup = json.loads(json.dumps(self.db))
        if self.mode == "add":
            self.db.setdefault(cat, []).append(recipe)
        else:
            if self.current_edit_index < 0 or cat not in self.db:
                messagebox.showerror("Error", "No hay una receta seleccionada para editar.")
                return
            self.db[cat][self.current_edit_index] = recipe

        if not self.save_db():
            self.db = backup          # no dejar en memoria un cambio que no se guardó
            return

        if self.mode == "add":
            self.clear_form()
            messagebox.showinfo("Listo", "Receta añadida. Recuerda hacer commit y push en BaseDatosRecetas.")
        else:
            # Recargar la lista y volver a mostrar ESTA receta (antes se quedaba cargada la primera
            # de la categoría con el nombre de otra, y el siguiente guardado pisaba la receta equivocada).
            self.on_edit_category_change(cat)
            self.recipe_select.set(name)
            self.on_edit_recipe_change(name)
            messagebox.showinfo("Listo", "Cambios guardados.")

    def delete_recipe(self):
        cat = self.cat_select.get()
        if self.current_edit_index < 0 or cat not in self.db:
            messagebox.showwarning("Aviso", "No hay ninguna receta seleccionada para eliminar.")
            return
        name = self.db[cat][self.current_edit_index].get("nombre", "")
        if not messagebox.askyesno("Confirmar eliminación",
                                   f"¿Eliminar la receta «{name}» de {cat}?\n\nEsta acción no se puede deshacer."):
            return
        removed = self.db[cat].pop(self.current_edit_index)
        if not self.save_db():
            self.db[cat].insert(self.current_edit_index, removed)
            return
        messagebox.showinfo("Listo", "Receta eliminada correctamente.")
        self.on_edit_category_change(cat)


if __name__ == "__main__":
    app = RecipeManager()
    app.mainloop()
