# MvRecipeManager.py
# Gestor de recetas para móvil (Kivy).
# Permite añadir, editar y eliminar recetas del archivo JSON local.

import os
import json
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
from kivy.uix.checkbox import CheckBox
from kivy.utils import platform

class ManagerLogic:
    def __init__(self):
        self.db = {}
        self.load_db()
        self.categories = list(self.db.keys())
        if not self.categories:
            self.categories = ["Sopas", "Cremas", "Verduras", "Legumbres", "Huevos", "Arroces", "Pastas", "Carnes", "Pescados", "Postres", "Panes"]
            for cat in self.categories:
                self.db[cat] = []

    def get_json_path(self):
        if platform == 'android':
            try:
                from kivy.app import App
                app = App.get_running_app()
                if app and app.user_data_dir:
                    return os.path.join(app.user_data_dir, "token.txt")
            except Exception:
                pass
            return "token.txt"
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(os.path.dirname(script_dir), "token.txt")

    def load_db(self):
        import requests
        try:
            url = "https://raw.githubusercontent.com/alherca25/BaseDatosRecetas/main/CocinaArguinyano.json"
            resp = requests.get(url)
            if resp.status_code == 200:
                self.db = resp.json()
            else:
                self.db = {}
        except Exception as e:
            print(f"Error cargando BD desde GitHub: {e}")
            self.db = {}

    def get_token(self):
        path = self.get_json_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read().strip()
        return ""

    def save_token(self, token):
        path = self.get_json_path()
        with open(path, "w") as f:
            f.write(token.strip())

    def save_db_to_github(self, token):
        import requests
        import base64
        
        repo = "alherca25/BaseDatosRecetas"
        path = "CocinaArguinyano.json"
        branch = "main" # BaseDatosRecetas solo tendra la rama main
        url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 1. Obtener el SHA actual del archivo
        resp = requests.get(url, headers=headers)
        sha = ""
        if resp.status_code == 200:
            sha = resp.json().get("sha", "")
        
        # 2. Subir el nuevo archivo
        content_str = json.dumps(self.db, indent=4, ensure_ascii=False)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": "Actualización de recetas desde MvRecipeManager (App Móvil)",
            "content": content_b64,
            "branch": branch
        }
        if sha:
            data["sha"] = sha
            
        put_url = f"https://api.github.com/repos/{repo}/contents/{path}"
        put_resp = requests.put(put_url, headers=headers, json=data)
        
        if put_resp.status_code in [200, 201]:
            return True, "¡Recetas guardadas en GitHub exitosamente!"
        else:
            return False, f"Error al guardar en GitHub: {put_resp.json().get('message', 'Desconocido')}"


class InfoPopup(Popup):
    def __init__(self, title_text, msg_text, **kwargs):
        super().__init__(title=title_text, size_hint=(0.8, 0.4), **kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lbl = Label(text=msg_text, text_size=(self.width, None), halign="center")
        lbl.bind(width=lambda *x: lbl.setter('text_size')(lbl, (lbl.width, None)))
        layout.add_widget(lbl)
        btn = Button(text="OK", size_hint_y=None, height=dp(40))
        btn.bind(on_release=self.dismiss)
        layout.add_widget(btn)
        self.content = layout


class IngredientRow(BoxLayout):
    def __init__(self, remove_callback, init_data=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(5), **kwargs)
        self.remove_callback = remove_callback
        
        self.name_input = TextInput(hint_text="Nombre", multiline=False)
        self.qty_input = TextInput(hint_text="Cant.", multiline=False, size_hint_x=0.5)
        self.unit_input = TextInput(hint_text="Unid.", multiline=False, size_hint_x=0.5)
        self.del_btn = Button(text="X", size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1))
        self.del_btn.bind(on_release=self.on_delete)
        
        self.add_widget(self.name_input)
        self.add_widget(self.qty_input)
        self.add_widget(self.unit_input)
        self.add_widget(self.del_btn)
        
        if init_data:
            self.name_input.text = init_data.get("nombre", "")
            self.qty_input.text = str(init_data.get("cantidad", ""))
            self.unit_input.text = str(init_data.get("unidad", ""))

    def on_delete(self, instance):
        self.remove_callback(self)

    def get_data(self):
        return {
            "nombre": self.name_input.text.strip(),
            "cantidad": self.qty_input.text.strip(),
            "unidad": self.unit_input.text.strip()
        }


class ManagerScreen(BoxLayout):
    def __init__(self, logic: ManagerLogic, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(10), padding=dp(10), **kwargs)
        self.logic = logic
        
        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        self.mode = "add"
        self.current_edit_index = -1
        
        # Header Tabs
        self.tabs = BoxLayout(size_hint_y=None, height=dp(40))
        self.add_tab_btn = Button(text="Añadir Receta", background_color=(0.2, 0.6, 1, 1))
        self.add_tab_btn.bind(on_release=lambda x: self.change_mode("add"))
        self.edit_tab_btn = Button(text="Editar Receta", background_color=(0.3, 0.3, 0.3, 1))
        self.edit_tab_btn.bind(on_release=lambda x: self.change_mode("edit"))
        self.tabs.add_widget(self.add_tab_btn)
        self.tabs.add_widget(self.edit_tab_btn)
        self.add_widget(self.tabs)
        
        # Token Input
        self.token_frame = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(5))
        self.token_frame.add_widget(Label(text="GitHub Token:", size_hint_x=0.3))
        self.token_input = TextInput(hint_text="Pega aquí tu token", password=True, multiline=False, size_hint_x=0.7)
        self.token_input.text = self.logic.get_token()
        self.token_input.bind(text=self.on_token_change)
        self.token_frame.add_widget(self.token_input)
        self.add_widget(self.token_frame)
        
        # Edit Selectors (hidden in add mode)
        self.edit_frame = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(5))
        self.cat_spinner = Spinner(text="--Categoría--", values=self.logic.categories)
        self.cat_spinner.bind(text=self.on_edit_category_change)
        self.recipe_spinner = Spinner(text="--Receta--", values=[])
        self.recipe_spinner.bind(text=self.on_edit_recipe_change)
        self.edit_frame.add_widget(self.cat_spinner)
        self.edit_frame.add_widget(self.recipe_spinner)
        
        # Main Form Scroll
        self.scroll = ScrollView()
        self.form = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=dp(10))
        self.form.bind(minimum_height=self.form.setter("height"))
        
        self.form_cat = Spinner(text=self.logic.categories[0], values=self.logic.categories, size_hint_y=None, height=dp(40))
        self.form.add_widget(Label(text="Categoría:", size_hint_y=None, height=dp(30)))
        self.form.add_widget(self.form_cat)
        
        self.name_input = TextInput(hint_text="Nombre del Plato", multiline=False, size_hint_y=None, height=dp(40))
        self.form.add_widget(self.name_input)
        
        self.page_input = TextInput(hint_text="Página (opcional)", multiline=False, size_hint_y=None, height=dp(40))
        self.form.add_widget(self.page_input)
        
        # Filters (CheckBoxes)
        filters = BoxLayout(size_hint_y=None, height=dp(40))
        self.veg_chk = CheckBox(size_hint_x=0.2)
        filters.add_widget(self.veg_chk)
        filters.add_widget(Label(text="Vegetariano", size_hint_x=0.3))
        self.gf_chk = CheckBox(size_hint_x=0.2)
        filters.add_widget(self.gf_chk)
        filters.add_widget(Label(text="Gluten Free", size_hint_x=0.3))
        self.form.add_widget(filters)
        
        self.elab_input = TextInput(hint_text="Elaboración", multiline=True, size_hint_y=None, height=dp(150))
        self.form.add_widget(self.elab_input)
        
        self.form.add_widget(Label(text="Ingredientes", size_hint_y=None, height=dp(30)))
        
        self.ings_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self.ings_layout.bind(minimum_height=self.ings_layout.setter("height"))
        self.form.add_widget(self.ings_layout)
        
        add_ing_btn = Button(text="+ Añadir Ingrediente", size_hint_y=None, height=dp(40))
        add_ing_btn.bind(on_release=lambda x: self.add_ingredient_row())
        self.form.add_widget(add_ing_btn)
        
        self.scroll.add_widget(self.form)
        self.add_widget(self.scroll)
        
        # Action Buttons
        actions = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.save_btn = Button(text="Guardar Receta", background_color=(0.2, 0.8, 0.2, 1))
        self.save_btn.bind(on_release=self.save_recipe)
        self.del_btn = Button(text="Eliminar Receta", background_color=(0.8, 0.2, 0.2, 1))
        self.del_btn.bind(on_release=self.delete_recipe)
        
        actions.add_widget(self.save_btn)
        self.add_widget(actions)
        
        self.add_ingredient_row()

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def add_ingredient_row(self, init_data=None):
        row = IngredientRow(self.remove_ingredient_row, init_data)
        self.ings_layout.add_widget(row)

    def remove_ingredient_row(self, row):
        self.ings_layout.remove_widget(row)

    def change_mode(self, mode):
        self.mode = mode
        if mode == "add":
            self.add_tab_btn.background_color = (0.2, 0.6, 1, 1)
            self.edit_tab_btn.background_color = (0.3, 0.3, 0.3, 1)
            if self.edit_frame in self.children:
                self.remove_widget(self.edit_frame)
            if self.del_btn.parent:
                self.save_btn.parent.remove_widget(self.del_btn)
            self.form_cat.disabled = False
            self.clear_form()
        else:
            self.edit_tab_btn.background_color = (0.2, 0.6, 1, 1)
            self.add_tab_btn.background_color = (0.3, 0.3, 0.3, 1)
            if self.edit_frame not in self.children:
                self.add_widget(self.edit_frame, index=2)
            if not self.del_btn.parent:
                self.save_btn.parent.add_widget(self.del_btn)
            self.form_cat.disabled = True
            self.clear_form()

    def clear_form(self):
        self.name_input.text = ""
        self.page_input.text = ""
        self.veg_chk.active = False
        self.gf_chk.active = False
        self.elab_input.text = ""
        self.ings_layout.clear_widgets()
        self.current_edit_index = -1
        self.add_ingredient_row()

    def on_edit_category_change(self, spinner, text):
        if text in self.logic.categories:
            recipes = self.logic.db.get(text, [])
            names = [r.get("nombre", f"Receta {i}") for i, r in enumerate(recipes)]
            self.recipe_spinner.values = names
            if names:
                self.recipe_spinner.text = names[0]
            else:
                self.recipe_spinner.text = "--No hay recetas--"
                self.clear_form()

    def on_edit_recipe_change(self, spinner, text):
        cat = self.cat_spinner.text
        if cat not in self.logic.categories: return
        recipes = self.logic.db.get(cat, [])
        try:
            idx = spinner.values.index(text)
            self.current_edit_index = idx
            r = recipes[idx]
            self.load_recipe_into_form(r, cat)
        except ValueError:
            pass

    def load_recipe_into_form(self, r, cat):
        self.clear_form()
        self.form_cat.text = cat
        self.name_input.text = r.get("nombre", "")
        self.page_input.text = str(r.get("pagina", ""))
        self.veg_chk.active = r.get("vegetariano", False)
        self.gf_chk.active = r.get("gluten_free", False)
        self.elab_input.text = r.get("elaboracion", "")
        self.ings_layout.clear_widgets()
        for ing in r.get("ingredientes", []):
            self.add_ingredient_row(ing)
        if not self.ings_layout.children:
            self.add_ingredient_row()

    def on_token_change(self, instance, value):
        self.logic.save_token(value)

    def save_recipe(self, instance):
        name = self.name_input.text.strip()
        if not name:
            InfoPopup("Error", "El nombre del plato no puede estar vacío.").open()
            return
            
        cat = self.form_cat.text
        if cat not in self.logic.categories:
            InfoPopup("Error", "Categoría inválida.").open()
            return
            
        token = self.token_input.text.strip()
        if not token:
            InfoPopup("Error", "Debes configurar un GitHub Token para poder guardar recetas.").open()
            return

        ings = []
        for row in self.ings_layout.children:
            if isinstance(row, IngredientRow):
                data = row.get_data()
                if data["nombre"]:
                    ings.append(data)
        ings.reverse()

        recipe_data = {
            "nombre": name,
            "pagina": self.page_input.text.strip(),
            "vegetariano": self.veg_chk.active,
            "gluten_free": self.gf_chk.active,
            "elaboracion": self.elab_input.text.strip(),
            "ingredientes": ings
        }

        if self.mode == "add":
            self.logic.db[cat].append(recipe_data)
        else:
            if self.current_edit_index >= 0 and self.current_edit_index < len(self.logic.db[cat]):
                self.logic.db[cat][self.current_edit_index] = recipe_data
            else:
                InfoPopup("Error", "Selecciona una receta válida para editar.").open()
                return

        # Intentamos subir a GitHub
        success, msg = self.logic.save_db_to_github(token)
        if success:
            InfoPopup("Éxito", msg).open()
            if self.mode == "edit":
                self.on_edit_category_change(self.cat_spinner, cat)
            else:
                self.clear_form()
        else:
            InfoPopup("Error", msg).open()

    def delete_recipe(self, instance):
        if self.mode != "edit" or self.current_edit_index < 0: return
        cat = self.cat_spinner.text
        token = self.token_input.text.strip()
        if not token:
            InfoPopup("Error", "Debes configurar un GitHub Token para poder eliminar recetas.").open()
            return
            
        if cat in self.logic.categories:
            del self.logic.db[cat][self.current_edit_index]
            success, msg = self.logic.save_db_to_github(token)
            if success:
                InfoPopup("Eliminada", "Receta eliminada y cambios subidos a GitHub.").open()
                self.on_edit_category_change(self.cat_spinner, cat)
            else:
                InfoPopup("Error", msg).open()


class MvRecipeApp(App):
    def build(self):
        self.title = "Gestor de Recetas (Móvil)"
        logic = ManagerLogic()
        return ManagerScreen(logic)

if __name__ == "__main__":
    MvRecipeApp().run()
