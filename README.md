# 🍳 Cocina Rápida — planificador de menús y lista de la compra

Elige cuántos platos quieres de cada tipo (sopas, legumbres, postres...). La app escoge recetas al azar del recetario, te muestra cada receta y junta los ingredientes en una sola lista de la compra, sumando las cantidades repetidas.

El proyecto tiene **dos apps para Android** (el objetivo principal) y sus equivalentes de escritorio:

| | Para quién | Android (Kivy) | Escritorio (customtkinter) |
|---|---|---|---|
| **Recetario** | Usuarios | `src/MvInterface.py` → APK *Cocina Rápida* | `src/PyInterface.py` (exporta PDF) |
| **Gestor de Recetas** | Administrador | `src/MvRecipeManager.py` → APK *Gestor de Recetas* | `src/RecipeManager.py` |

## Base de datos

Las recetas están en otro repositorio: [`alherca25/BaseDatosRecetas`](https://github.com/alherca25/BaseDatosRecetas), archivo `CocinaArguinyano.json`:

```json
{ "Sopas": [ { "nombre": "...", "pagina": "185", "elaboracion": "...",
               "filtros": { "vegetariano": false, "gluten_free": false },
               "ingredientes": [ { "nombre": "Tomate", "cantidad": "2", "unidad": "uds" } ] } ] }
```

- **Recetario**: descarga el JSON al arrancar y guarda una copia, así funciona sin conexión. El APK también lleva una copia (`data/CocinaArguinyano.json`) por si el primer arranque es sin internet.
- **Gestor móvil**: lee y guarda directamente en GitHub con un *token* personal (permiso *Contents: Read and write* sobre `BaseDatosRecetas`). Si alguien cambió el archivo mientras tanto, la app avisa y no pisa esos cambios.
- **Gestor de escritorio**: edita el clon local `../BaseDatosRecetas/CocinaArguinyano.json`. Después hay que hacer *commit* y *push* a mano.

Unidades admitidas: `uds`, `g`, `mL`, `cuch`.

## Estructura

```
src/
  functions.py         lógica común: descarga, caché, filtros, menú, agrupar ingredientes, API de GitHub
  mobile_ui.py         componentes visuales de las apps móviles (paleta de los logos)
  desktop_theme.py     tema de las apps de escritorio
  MvInterface.py       Recetario móvil         (main.py lo lanza en el ordenador)
  MvRecipeManager.py   Gestor móvil
  PyInterface.py       Recetario escritorio
  RecipeManager.py     Gestor escritorio
assets/                logos (.ico/.jpg) y PNG generados para Android (tools/make_icons.py)
data/                  copia de la BD y Excel original
tests/                 tests de la lógica (python -m unittest discover -s tests)
tools/                 stage_android.py, make_icons.py, screenshot_app.py
legacy/                prototipo con pandas/Excel y script de migración a JSON
buildozer_*.spec       configuración de cada APK
```

## Ejecutar en el ordenador

```bash
python -m venv venvArguinyano
venvArguinyano\Scripts\activate
pip install -r requirements_desktop.txt -r requirements_mobile.txt

cd src
python PyInterface.py        # Recetario escritorio (PDF en Documentos\Cocina Rápida)
python RecipeManager.py      # Gestor escritorio
python MvInterface.py        # Recetario móvil en una ventana
python MvRecipeManager.py    # Gestor móvil en una ventana
```

Tests: `python -m unittest discover -s tests`

## Compilar los APK

Cada *push* a `main` o `_dev` lanza **GitHub Actions** (`.github/workflows/build-android.yml`): pasa los tests y genera los artefactos `Recetario_APK` y `GestorRecetas_APK`. Para compilar en local (Linux/WSL) consulta [README_android.md](README_android.md).

## Licencia

Proyecto de uso personal y educativo. Las recetas pertenecen a sus autores.
