import pandas as pd
import json
import math
import os

EXCEL_FILE = "CocinaArguinyano.xlsx"
JSON_FILE = "CocinaArguinyano.json"

def clean_val(val):
    if pd.isna(val):
        return ""
    if isinstance(val, float) and math.isnan(val):
        return ""
    # Ensure strings without leading/trailing whitespace
    return str(val).strip() if str(val).strip() != "None" else ""

def clean_bool(val):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return False
    str_val = str(val).lower().strip()
    if str_val in ["true", "1", "sí", "si", "yes"]:
        return True
    return False

def migrate_excel_to_json():
    print(f"Leyendo archivo Excel: {EXCEL_FILE}...")
    
    # Check sheets
    xl = pd.ExcelFile(EXCEL_FILE)
    sheet_names = xl.sheet_names
    
    skip_sheets = ['Otros', 'Ingredientes', 'Unidades']
    
    recipes_db = {}
    
    for sheet in sheet_names:
        if sheet in skip_sheets:
            continue
            
        print(f"Procesando hoja: {sheet}")
        recipes_db[sheet] = []
        
        # Read the sheet
        df = xl.parse(sheet)
        
        # Determine actual column names based on position to avoid case-sensitivity issues
        # 0: Plato, 1: Página, 2: Elaboración, 3: Ingredientes, 4: Cantidades, 5: Unidades, 6: Todo, 7: Vegetariano, 8: Gluten Free
        cols = df.columns.tolist()
        if len(cols) < 9:
            print(f"La hoja {sheet} tiene menos columnas de las esperadas. Saltando...")
            continue
            
        current_recipe = None
        
        for index, row in df.iterrows():
            plato = clean_val(row.iloc[0])
            
            # Si la fila tiene un nombre de plato, empezamos una receta nueva
            if plato != "":
                if current_recipe is not None:
                    recipes_db[sheet].append(current_recipe)
                
                current_recipe = {
                    "nombre": plato,
                    "pagina": clean_val(row.iloc[1]),
                    "elaboracion": clean_val(row.iloc[2]),
                    "filtros": {
                        "vegetariano": clean_bool(row.iloc[7]),
                        "gluten_free": clean_bool(row.iloc[8])
                    },
                    "ingredientes": []
                }
                
                # Add the first ingredient
                ingrediente = clean_val(row.iloc[3])
                if ingrediente != "":
                    current_recipe["ingredientes"].append({
                        "nombre": ingrediente,
                        "cantidad": clean_val(row.iloc[4]),
                        "unidad": clean_val(row.iloc[5])
                    })
            else:
                # Si el plato está vacío, es un ingrediente de la receta actual
                if current_recipe is not None:
                    ingrediente = clean_val(row.iloc[3])
                    if ingrediente != "":
                        current_recipe["ingredientes"].append({
                            "nombre": ingrediente,
                            "cantidad": clean_val(row.iloc[4]),
                            "unidad": clean_val(row.iloc[5])
                        })
                        
        # Append the last recipe of the sheet
        if current_recipe is not None:
            recipes_db[sheet].append(current_recipe)

    # Convertir a JSON
    print(f"Guardando en {JSON_FILE}...")
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes_db, f, indent=4, ensure_ascii=False)
        
    print("Migración completada con éxito.")

if __name__ == "__main__":
    if not os.path.exists(EXCEL_FILE):
        print(f"No se encuentra el archivo {EXCEL_FILE}.")
    else:
        migrate_excel_to_json()
