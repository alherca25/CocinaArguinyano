"""Idiomas de la interfaz.

Las claves son el texto en español: _("Generar menú") devuelve la traducción del
idioma activo o el propio texto si no hay traducción (el español es el original,
así que una frase sin traducir nunca rompe la app).

Las recetas (nombres, pasos, ingredientes) se traducen aparte: recipe_translation.py.
Para añadir un idioma: crea su tabla aquí, añádelo a LANGUAGES y genera la traducción
de las recetas con tools/translate_db.py.
"""
import locale

LANGUAGES = {"es": "Español", "en": "English"}
DEFAULT = "es"
_current = DEFAULT

EN = {
    # Categorías (claves de la BD) y filtros
    "Sopas": "Soups",
    "Cremas": "Cream soups",
    "Verduras": "Vegetables",
    "Legumbres": "Legumes",
    "Huevos": "Eggs",
    "Arroces": "Rice dishes",
    "Pastas": "Pasta",
    "Carnes": "Meat",
    "Pescados": "Fish",
    "Postres": "Desserts",
    "Panes": "Breads",
    "Todas": "All",
    "Todo": "All",
    "Vegetariano": "Vegetarian",
    "Sin gluten": "Gluten-free",
    # Unidades
    "uds": "pcs",
    "g": "g",
    "mL": "mL",
    "cuch": "tbsp",
    # Comunes (mobile_ui / functions)
    "Aceptar": "OK",
    "Cancelar": "Cancel",
    "Sí": "Yes",
    "Cargando...": "Loading...",
    "Compartir": "Share",
    "Copiado al portapapeles.": "Copied to clipboard.",
    "pág. {page}": "p. {page}",
    "Ingredientes": "Ingredients",
    "Elaboración": "Method",
    # Planificar
    "Recetario": "Recipes",
    "Cargando recetas...": "Loading recipes...",
    "Generar menú": "Create menu",
    "Descargando el recetario...": "Downloading recipes...",
    "Reintentar": "Try again",
    "Tu último menú": "Your last menu",
    "{n} plato": "{n} dish",
    "{n} platos": "{n} dishes",
    "Abrir": "Open",
    "Tipo de dieta": "Diet",
    "¿Cuántos platos de cada tipo?": "How many dishes of each kind?",
    "{n} disponibles": "{n} available",
    "Ninguna con este filtro": "None with this filter",
    "Idioma": "Language",
    "Buscar actualizaciones": "Check for updates",
    "Versión {v}": "Version {v}",
    "{n} plato\nseleccionado": "{n} dish\nselected",
    "{n} platos\nseleccionados": "{n} dishes\nselected",
    "Elige al menos un plato.": "Choose at least one dish.",
    # Mi menú
    "Mi menú": "My menu",
    "Platos": "Dishes",
    "Compra": "Shopping",
    "Nuevo menú": "New menu",
    "Todavía no has generado ningún menú.": "You haven't created a menu yet.",
    "«Ver receta» muestra ingredientes y pasos. «Cambiar» elige otro plato de la misma categoría.":
        "“View recipe” shows ingredients and steps. “Swap” picks another dish from the same category.",
    "{n} ingredientes": "{n} ingredients",
    "Cambiar": "Swap",
    "Ver receta": "View recipe",
    "Plato cambiado": "Dish swapped",
    "Sin alternativas": "No alternatives",
    "No hay más recetas de esta categoría con el filtro actual.":
        "There are no more recipes in this category with the current filter.",
    "{pending} por comprar · {done} en el carro. Marca lo que ya tengas.":
        "{pending} to buy · {done} in the cart. Tick what you already have.",
    "Desmarcar todo": "Untick all",
    "Menú {date}": "Menu {date}",
    "Compra {date}": "Shopping {date}",
    "No se pudo compartir": "Couldn't share",
    # Receta
    "Receta": "Recipe",
    "Compartir receta": "Share recipe",
    "Recetario Cocina Rápida": "Cocina Rápida recipes",
    "Sin elaboración registrada.": "No method recorded.",
    # Recetario
    "Buscar receta o ingrediente...": "Search recipe or ingredient...",
    "{n} recetas · filtro: {f}": "{n} recipes · filter: {f}",
    "No hay recetas que coincidan.": "No matching recipes.",
    # Carga de datos
    "Buscando novedades...": "Checking for news...",
    "actualizado": "up to date",
    "sin conexión (copia guardada)": "offline (saved copy)",
    "copia incluida": "built-in copy",
    "{n} recetas · {origin}": "{n} recipes · {origin}",
    "Sin conexión: usando la última copia guardada": "Offline: using the last saved copy",
    "Recetario actualizado: {n} recetas": "Recipes updated: {n} recipes",
    "{n} recetas · sin conexión": "{n} recipes · offline",
    "No se pudo actualizar el recetario": "Couldn't update the recipes",
    "Sin recetas": "No recipes",
    "No se pudieron cargar las recetas.": "Couldn't load the recipes.",
    # Actualización de la app
    "No se pudo comprobar si hay una versión nueva.": "Couldn't check for a new version.",
    "Tienes la última versión ({v}).": "You have the latest version ({v}).",
    "Se descargará la nueva versión{size} y Android te pedirá confirmar la instalación. "
    "Tu menú y tu lista de la compra se conservan.":
        "The new version{size} will be downloaded and Android will ask you to confirm the "
        "installation. Your menu and shopping list are kept.",
    "Nueva versión {v}": "New version {v}",
    "Actualizar": "Update",
    "Más tarde": "Later",
    "Un permiso más": "One more permission",
    "Para instalar la nueva versión, Android necesita que permitas a Cocina Rápida instalar "
    "aplicaciones. Activa «Permitir de esta fuente» y vuelve a la app: la descarga empezará sola.":
        "To install the new version, Android needs you to allow Cocina Rápida to install apps. "
        "Turn on “Allow from this source” and come back to the app: the download will start "
        "by itself.",
    "Abrir ajustes": "Open settings",
    "Descargando... 0 %": "Downloading... 0 %",
    "Descargando... {p} %": "Downloading... {p} %",
    "No se pudo descargar": "Download failed",
    "No se pudo abrir el instalador": "Couldn't open the installer",
    # Acciones
    "Cantidades ajustadas: ": "Amounts adjusted: ",
    "¿Nuevo menú?": "New menu?",
    "Se sustituirá el menú actual y su lista de la compra.":
        "The current menu and its shopping list will be replaced.",
    "Generar": "Create",
}

_TABLES = {"en": EN}


def set_language(code):
    global _current
    _current = code if code in LANGUAGES else DEFAULT


def get_language():
    return _current


def _(text):
    """Traduce un texto de la interfaz al idioma activo."""
    return _TABLES.get(_current, {}).get(text, text)


def device_language():
    """Idioma del móvil/PC: "es" para español (y catalán, euskera, gallego), si no "en"."""
    code = ""
    try:
        from kivy.utils import platform
        if platform == "android":
            from jnius import autoclass
            code = autoclass("java.util.Locale").getDefault().getLanguage()
    except Exception:
        code = ""
    if not code:
        try:
            code = locale.getlocale()[0] or ""
        except Exception:
            code = ""
    code = code.lower()
    if code.startswith(("es", "ca", "eu", "gl", "spanish", "catalan", "basque", "galician")):
        return "es"
    if not code:
        return DEFAULT
    return "en"
