import json
import urllib.request
import random
import os

def load_recipes(source_path, is_local=False):
    """
    Carga el recetario en formato JSON, ya sea desde un archivo local o una URL.
    """
    if is_local:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"No se encontró el archivo {source_path}")
        with open(source_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        req = urllib.request.Request(source_path)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

def filter_recipes(recipes_list, active_filter):
    """
    Filtra una lista de recetas según el filtro activo.
    active_filter puede ser "Todo", "Vegetariano" o "Gluten Free".
    """
    if active_filter == "Todo":
        return recipes_list
        
    filtered = []
    for recipe in recipes_list:
        filtros = recipe.get("filtros", {})
        if active_filter == "Vegetariano" and filtros.get("vegetariano", False):
            filtered.append(recipe)
        elif active_filter == "Gluten Free" and filtros.get("gluten_free", False):
            filtered.append(recipe)
            
    return filtered

def select_random_dishes(recipes_db, category, amount, active_filter):
    """
    Selecciona 'amount' recetas aleatorias de una 'category' que cumplan con 'active_filter'.
    Si no hay suficientes, devuelve todas las posibles y un booleano indicando si se limitó.
    """
    if category not in recipes_db:
        return [], False
        
    category_recipes = recipes_db[category]
    valid_recipes = filter_recipes(category_recipes, active_filter)
    
    limited = False
    if len(valid_recipes) < amount:
        amount = len(valid_recipes)
        limited = True
        
    if amount == 0:
        return [], limited
        
    selected = random.sample(valid_recipes, amount)
    return selected, limited

def format_ingredient(ing):
    """
    Convierte el diccionario de ingrediente a un string para mostrar.
    """
    nombre = ing.get('nombre', '')
    cantidad = str(ing.get('cantidad', '')).strip()
    unidad = str(ing.get('unidad', '')).strip()
    
    parts = []
    if cantidad and cantidad != "nan":
        parts.append(cantidad)
    if unidad and unidad != "nan":
        parts.append(unidad)
        
    prefix = " ".join(parts)
    if prefix:
        return f"{prefix} {nombre}"
    return nombre
