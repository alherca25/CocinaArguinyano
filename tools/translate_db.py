"""Mantiene las traducciones de las recetas (CocinaArguinyano.<idioma>.json).

La BD en español es la referencia. Cada receta traducida guarda un «hash» de su nombre
y elaboración en español: si la receta cambia en el Gestor, aparece como desfasada y
la app la muestra en español hasta que se vuelva a traducir.

Uso (desde la raíz del repo):
    python tools/translate_db.py check en
        Lista recetas sin traducir o desfasadas e ingredientes sin traducir.
    python tools/translate_db.py export en pendientes.json
        Escribe lo que falta por traducir:
        {"recetas": {"<nombre ES>": {"nombre": "...", "elaboracion": "..."}},
         "ingredientes": ["Tomate pera", ...]}
    python tools/translate_db.py import en traducido.json [más.json ...]
        Incorpora traducciones con el mismo formato, pero en el idioma destino:
        {"recetas": {"<nombre ES>": {"nombre": "<EN>", "elaboracion": "<EN>"}},
         "ingredientes": {"Tomate pera": "Plum tomato", ...}}
        Calcula el hash con la receta española actual, guarda el archivo en
        BaseDatosRecetas y copia el resultado en shared/data (copia offline de la app).

Opciones: --db RUTA  (por defecto ../BaseDatosRecetas/CocinaArguinyano.json)
"""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shared"))

import functions  # noqa: E402
import recipe_translation as rt  # noqa: E402

DEFAULT_DB = os.path.join(os.path.dirname(ROOT), "BaseDatosRecetas", "CocinaArguinyano.json")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def load_db(path):
    db = load_json(path)
    if db is None:
        sys.exit(f"No se encontró la BD: {path}")
    return {cat: [functions.normalize_recipe(r) for r in recipes] for cat, recipes in db.items()}


def tr_path(db_path, lang):
    return os.path.join(os.path.dirname(db_path), rt.translation_file(lang))


def cmd_check(args):
    db = load_db(args.db)
    tr = load_json(tr_path(args.db, args.lang), {})
    recipes, ings = rt.stale_entries(db, tr)
    total = sum(len(v) for v in db.values())
    print(f"[{args.lang}] recetas al día: {total - len(recipes)}/{total} · ingredientes sin traducir: {len(ings)}")
    for r in recipes:
        state = "desfasada" if r["nombre"] in (tr.get("recetas") or {}) else "sin traducir"
        print(f"  - {r['nombre']} ({state})")
    for name in ings:
        print(f"  · ingrediente: {name}")
    return 1 if recipes or ings else 0


def cmd_export(args):
    db = load_db(args.db)
    tr = load_json(tr_path(args.db, args.lang), {})
    recipes, ings = rt.stale_entries(db, tr)
    out = {"recetas": {r["nombre"]: {"nombre": r["nombre"], "elaboracion": r["elaboracion"]}
                       for r in recipes},
           "ingredientes": ings}
    save_json(args.output, out)
    print(f"Exportado: {len(recipes)} recetas y {len(ings)} ingredientes -> {args.output}")


def cmd_import(args):
    db = load_db(args.db)
    by_name = {r["nombre"]: r for recipes in db.values() for r in recipes}
    path = tr_path(args.db, args.lang)
    tr = load_json(path, {}) or {}
    tr.setdefault("lang", args.lang)
    tr.setdefault("ingredientes", {})
    tr.setdefault("recetas", {})
    unknown = []
    for src in args.inputs:
        data = load_json(src, {})
        for es_name, en in (data.get("ingredientes") or {}).items():
            if en and str(en).strip():
                tr["ingredientes"][es_name] = str(en).strip()
        for es_name, entry in (data.get("recetas") or {}).items():
            recipe = by_name.get(es_name)
            if recipe is None:
                unknown.append(es_name)
                continue
            tr["recetas"][es_name] = {"hash": rt.recipe_hash(recipe),
                                      "nombre": str(entry.get("nombre", "")).strip(),
                                      "elaboracion": str(entry.get("elaboracion", "")).strip()}
    # Orden estable (el de la BD) para que los diffs sean legibles; se quitan recetas borradas.
    order = [r["nombre"] for recipes in db.values() for r in recipes]
    tr["recetas"] = {n: tr["recetas"][n] for n in order if n in tr["recetas"]}
    tr["ingredientes"] = dict(sorted(tr["ingredientes"].items(), key=lambda kv: kv[0].lower()))
    save_json(path, tr)
    local = os.path.join(ROOT, "shared", "data", rt.translation_file(args.lang))
    shutil.copy2(path, local)
    print(f"Guardado: {path}\nCopia offline: {local}")
    if unknown:
        print("Recetas que no existen en la BD (ignoradas): " + ", ".join(unknown))
    return cmd_check(args)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=DEFAULT_DB)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("lang")
    p = sub.add_parser("export")
    p.add_argument("lang")
    p.add_argument("output")
    p = sub.add_parser("import")
    p.add_argument("lang")
    p.add_argument("inputs", nargs="+")
    args = ap.parse_args()
    return {"check": cmd_check, "export": cmd_export, "import": cmd_import}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
