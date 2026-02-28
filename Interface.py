import tkinter as tk
from tkinter import ttk
import pandas as pd
import requests
from io import BytesIO
import warnings

class CocinaArguinyano:
    def __init__(self, master):
        # Configuración de rutas
        self.EXCEL_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/main/CocinaArguinyano.xlsx"
        response = requests.get(self.EXCEL_URL)
        print(f"Status: {response.status_code}")
        print(f"URL probada: {self.EXCEL_URL}")
        print(f"Primeros 100 bytes: {response.content[:100]}")

        self.recipes_table = self.load_recipes()
    
        self.master = master
        master.title("Cocina Arguinyano")

        self.label = tk.Label(master, text="¡Bienvenido a la Cocina Arguinyano!")
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
        print("Añadiendo receta...")
        # Abrimos una ventana para seleccionar receta y cantidad
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
        
        def save_recipe():
            recipe_type = recipe_combo.get()
            cantidad = cantidad_entry.get()
            
            if recipe_type and cantidad:
                try:
                    cantidad = int(cantidad)
                    self.tree.insert("", "end", values=(recipe_type, cantidad, ""))
                    add_window.destroy()
                except ValueError:
                    print("Por favor, ingresa un número válido")
            else:
                print("Por favor, completa todos los campos")
        
        save_button = tk.Button(add_window, text="Guardar", command=save_recipe)
        save_button.pack(pady=10)

    def edit_recipe(self):
        print("Editando receta...")
        # Editamos la receta seleccionada con una ventana idéntica a la generada en la función Añadir
        
        selected = self.tree.selection()
        if not selected:
            print("No hay receta seleccionada para editar")
            return

        item = self.tree.item(selected[0])
        values = item['values']

        edit_window = tk.Toplevel(self.master)
        edit_window.title("Editar Receta")
        edit_window.geometry("400x300")

        tk.Label(edit_window, text="Nombre:").pack(pady=5)
        nombre_entry = tk.Entry(edit_window, width=40)
        nombre_entry.pack(pady=5)
        nombre_entry.insert(0, values[0])

        tk.Label(edit_window, text="Ingredientes:").pack(pady=5)
        ingredientes_entry = tk.Entry(edit_window, width=40)
        ingredientes_entry.pack(pady=5)
        ingredientes_entry.insert(0, values[1])

        tk.Label(edit_window, text="Instrucciones:").pack(pady=5)
        instrucciones_entry = tk.Entry(edit_window, width=40)
        instrucciones_entry.pack(pady=5)
        instrucciones_entry.insert(0, values[2])

        def update_recipe():
            nombre = nombre_entry.get()
            ingredientes = ingredientes_entry.get()
            instrucciones = instrucciones_entry.get()

            if nombre and ingredientes and instrucciones:
                self.tree.delete(selected[0])
                self.tree.insert("", "end", values=(nombre, ingredientes, instrucciones))
                edit_window.destroy()
            else:
                print("Por favor, completa todos los campos")

        update_button = tk.Button(edit_window, text="Actualizar", command=update_recipe)
        update_button.pack(pady=10)

    def delete_recipe(self):
        print("Eliminando receta...")
        # Eliminamos la receta seleccionada
        selected = self.tree.selection()
        if not selected:
            print("No hay receta seleccionada para eliminar")
            return
        self.tree.delete(selected[0])
        
if __name__ == "__main__":
    root = tk.Tk()
    app = CocinaArguinyano(root)
    root.mainloop()