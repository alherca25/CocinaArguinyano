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
        self.selected_dishes = {}
    
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

        tk.Label(master, text="Generar listas:").pack(pady=5)
        self.generate_button = tk.Button(master, text="Recetas", command=self.generate_list)
        self.generate_button.pack(side=tk.LEFT, pady=10, padx=5)
        self.generate_button = tk.Button(master, text="Compra", command=self.generate_list)
        self.generate_button.pack(side=tk.RIGHT, pady=10, padx=5)
        self.generate_button = tk.Button(master, text="Ambas", command=self.generate_list)
        self.generate_button.pack(pady=10)

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
        
        def save_recipe():
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
                print("Por favor, completa todos los campos")
        
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

        def update_recipe():
            nombre = recipe_combo.get()
            cantidad = cantidad_entry.get()

            if nombre and cantidad:
                self.tree.delete(selected[0])
                self.tree.insert("", "end", values=(nombre, cantidad, ""))
                self.selected_dishes[nombre] = cantidad
                edit_window.destroy()
            else:
                print("Por favor, completa todos los campos")

        update_button = tk.Button(edit_window, text="Actualizar", command=update_recipe)
        update_button.pack(pady=10)

    def delete_recipe(self):
        # Eliminamos la receta seleccionada
        selected = self.tree.selection()
        if not selected:
            print("No hay receta seleccionada para eliminar")
            return
        self.tree.delete(selected[0])

    def generate_list(self):
        df_excel = self.recipes_table

        # Mostramos el tipo de platos disponibles
        '''
        print('Tipos de platos disponibles:')
        for sheet in df_excel.keys():
            if sheet not in ('Ingredientes', 'Unidades'):
                print(f'- {sheet}')
        '''
        
        # Acumulador para todos los ingredientes y platos seleccionados
        all_ingredients = []
        selected_dishes = []

        # Recorremos el diccionario de platos deseados
        for plate_type, desired_num in self.selected_dishes.items():
            # Verificamos si el tipo de plato existe
            if plate_type not in df_excel:
                print(f'No se han encontrado recetas de {plate_type}')
                continue
            
            # Verificamos que se solicite al menos un plato
            if desired_num <= 0:
                print(f'No se han solicitado platos de tipo {plate_type}')
                continue

            # Cargamos el tipo de platos solicitado
            df_plate = df_excel[plate_type].copy()
            
            # Rellenamos valores NaN en la columna 'Plato' antes de procesar
            df_plate['Plato'] = df_plate['Plato'].ffill()
            
            # Extraemos platos únicos disponibles
            platos = df_plate['Plato'].drop_duplicates().dropna()

            # Ajustamos la cantidad de platos si es necesario
            plate_num = min(len(platos), desired_num)

            # Comprobamos si hay platos disponibles
            if plate_num == 0:
                print(f'No hay platos disponibles de tipo {plate_type}')
                continue

            print(f'\nSeleccionando {plate_num} platos de tipo {plate_type}...\n')

            # Extraemos platos al azar
            try:
                selected_plates = np.random.choice(platos.values, plate_num, replace=False)
            except ValueError as e:
                print(f'Error al seleccionar platos de {plate_type}: {e}')
                continue

            # Filtramos por platos seleccionados
            mask = df_plate['Plato'].isin(selected_plates)
            df_selected = df_plate[mask]
            
            # Obtenemos información única de cada plato seleccionado
            page_col = 'Página' if 'Página' in df_selected.columns else 'Pagina'
            plate_info = df_selected.groupby('Plato', as_index=False).first()
            
            # Almacenamos información de los platos seleccionados (más eficiente que iterrows)
            plate_info['Tipo'] = plate_type
            plate_info['Página'] = plate_info[page_col].astype('Int64')  # Int64 admite NaN
            selected_dishes.extend(plate_info[['Tipo', 'Plato', 'Página']].to_dict('records'))

            # Extraemos ingredientes
            ingredients_df = df_selected[['Ingredientes', 'Cantidades', 'Unidades']].copy()
            all_ingredients.append(ingredients_df)

        # Consolidamos todos los ingredientes
        if not all_ingredients:
            ingredients_result = pd.DataFrame(columns=['Ingredientes', 'Cantidades', 'Unidades'])
        else:
            combined_df = pd.concat(all_ingredients, ignore_index=True)
            # Agrupamos por ingrediente y sumamos cantidades
            ingredients_result = combined_df.groupby('Ingredientes', as_index=False).agg({
                'Cantidades': 'sum',
                'Unidades': 'first'  # Asumimos que las unidades son consistentes por ingrediente
            })

        # Creamos dataframe de platos seleccionados
        dishes_result = pd.DataFrame(selected_dishes)

        return ingredients_result, dishes_result

        
if __name__ == "__main__":
    root = tk.Tk()
    app = CocinaArguinyano(root)
    root.mainloop()