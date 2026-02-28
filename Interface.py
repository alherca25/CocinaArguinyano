import tkinter as tk
from tkinter import ttk

class CocinaArguinyano:
    def __init__(self, master):
        self.master = master
        master.title("Cocina Arguinyano")

        self.label = tk.Label(master, text="¡Bienvenido a la Cocina Arguinyano!")
        self.label.pack()

        self.load_button = tk.Button(master, text="Cargar Recetas", command=self.load_recipes)
        self.load_button.pack()

        # Create frame for table
        self.frame = tk.Frame(master)
        self.frame.pack(pady=10)

        # Create table with columns
        self.tree = ttk.Treeview(self.frame, columns=("Nombre", "Ingredientes", "Instrucciones"), height=10)
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("Nombre", anchor=tk.W, width=150)
        self.tree.column("Ingredientes", anchor=tk.W, width=200)
        self.tree.column("Instrucciones", anchor=tk.W, width=200)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("Nombre", text="Nombre", anchor=tk.W)
        self.tree.heading("Ingredientes", text="Ingredientes", anchor=tk.W)
        self.tree.heading("Instrucciones", text="Instrucciones", anchor=tk.W)
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
        pass
    
    def add_recipe(self):
        print("Añadiendo receta...")
        pass

    def edit_recipe(self):
        print("Editando receta...")
        pass

    def delete_recipe(self):
        print("Eliminando receta...")
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = CocinaArguinyano(root)
    root.mainloop()