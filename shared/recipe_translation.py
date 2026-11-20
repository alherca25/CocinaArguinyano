"""Traducción de las recetas (contenido), separada de la interfaz (i18n.py).

La BD en español (CocinaArguinyano.json) es la única fuente de verdad: cantidades,
unidades, filtros y categorías salen siempre de ella. Cada idioma tiene un archivo
aparte en BaseDatosRecetas, p. ej. CocinaArguinyano.en.json:

    {
      "lang": "en",
      "ingredientes": {"Tomate pera": "Plum tomato", ...},
      "recetas": {
        "Gazpacho andaluz": {"hash": "3f9c...", "nombre": "Andalusian gazpacho",
                             "elaboracion": "Wash the tomatoes..."}
      }
    }

- Las recetas se buscan por su nombre en español.
- "hash" resume el nombre y la elaboración en español: si alguien edita la receta
  en el Gestor, el hash deja de coincidir y se muestra en español hasta que se
  vuelva a traducir (tools/translate_db.py).
- Los ingredientes se traducen con un diccionario común, así el mismo ingrediente
  se llama igual en todas las recetas y la lista de la compra los suma bien.

Cada receta e ingrediente traducido conserva su nombre original en "_id", que es
la clave estable para el menú guardado y para lo marcado en la lista de la compra.
"""
import hashlib


def translation_file(lang):
    return f"CocinaArguinyano.{lang}.json"


def recipe_hash(recipe):
    text = f"{str(recipe.get('nombre', '')).strip()}\n{str(recipe.get('elaboracion', '')).strip()}"
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def translate_recipe(recipe, tr):
    """Copia traducida de una receta normalizada (con "_id" en receta e ingredientes)."""
    tr = tr or {}
    src_name = recipe.get("_id", recipe.get("nombre", ""))
    out = dict(recipe)
    out["_id"] = src_name
    entry = (tr.get("recetas") or {}).get(src_name)
    if entry and entry.get("hash") == recipe_hash(recipe):
        out["nombre"] = entry.get("nombre") or recipe["nombre"]
        out["elaboracion"] = entry.get("elaboracion") or recipe.get("elaboracion", "")
    ing_names = tr.get("ingredientes") or {}
    out["ingredientes"] = []
    for ing in recipe.get("ingredientes", []):
        src = ing.get("_id", ing.get("nombre", ""))
        out["ingredientes"].append(dict(ing, _id=src, nombre=ing_names.get(src) or ing.get("nombre", "")))
    return out


def translate_db(db, tr):
    """Devuelve la BD traducida (misma estructura y categorías en español)."""
    return {cat: [translate_recipe(r, tr) for r in recipes] for cat, recipes in db.items()}


def stale_entries(db, tr):
    """(recetas_sin_traducir_o_desfasadas, ingredientes_sin_traducir) para el idioma tr."""
    recetas = (tr or {}).get("recetas") or {}
    ingredientes = (tr or {}).get("ingredientes") or {}
    todo_recipes, todo_ings = [], set()
    for recipes in db.values():
        for r in recipes:
            entry = recetas.get(r["nombre"])
            if not entry or entry.get("hash") != recipe_hash(r):
                todo_recipes.append(r)
            for ing in r.get("ingredientes", []):
                name = str(ing.get("nombre", "")).strip()
                if name and name not in ingredientes:
                    todo_ings.add(name)
    return todo_recipes, sorted(todo_ings)
