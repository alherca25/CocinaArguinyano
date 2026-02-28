# -*- coding: utf-8 -*-
#%%
# Importamos las librerías necesarias
import numpy as np
import pandas as pd
import requests
from io import BytesIO

# Configuración de rutas
EXCEL_URL = "https://raw.githubusercontent.com/alherca25/CocinaArguinyano/main/CocinaArguinyano.xlsx"

response = requests.get(EXCEL_URL)
print(f"Status: {response.status_code}")
print(f"URL probada: {EXCEL_URL}")
print(f"Primeros 100 bytes: {response.content[:100]}")

# Generamos el diccionario de platos deseados
DESIRED_PLATES = {
    'Sopas': 5,
    'Cremas': 0,
    'Verduras': 3,
}

def load_excel_github():
    """Lee XLSX directamente desde GitHub raw URL"""
    try:
        # Método 1: directo con pandas (funciona muchas veces)
        return pd.read_excel(EXCEL_URL, sheet_name=None)
    except:
        # Método 2: requests + BytesIO (100% fiable para XLSX)
        response = requests.get(EXCEL_URL)
        response.raise_for_status()  # Lanza error si falla
        return pd.read_excel(BytesIO(response.content), sheet_name=None)
    
# Definimos la función principal
def main():
    # Cargamos el excel
    #df_excel = pd.read_excel(EXCEL_PATH, sheet_name=None)
    df_excel = load_excel_github()

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
    for plate_type, desired_num in DESIRED_PLATES.items():
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

if __name__ == '__main__':
    Ingr_cant, platos_seleccionados = main()
    print('\n=== INGREDIENTES NECESARIOS ===')
    print(Ingr_cant)
    print('\n=== PLATOS SELECCIONADOS ===')
    print(platos_seleccionados)

#%%