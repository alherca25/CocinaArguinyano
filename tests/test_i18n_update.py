"""Tests de idiomas, traducción de recetas y actualización de la app (sin red)."""
import ast
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shared"))
sys.path.insert(0, os.path.join(ROOT, "client", "mobile"))
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

import functions  # noqa: E402
import i18n  # noqa: E402
import recipe_translation as rt  # noqa: E402
import updater  # noqa: E402


def recipe(name, ings=(), elab="Paso 1.\n\nPaso 2."):
    return functions.normalize_recipe({
        "nombre": name, "pagina": "", "elaboracion": elab, "filtros": {},
        "ingredientes": [{"nombre": n, "cantidad": c, "unidad": u} for n, c, u in ings]})


DB = {"Sopas": [recipe("Gazpacho", [("Tomate", "1000", "g"), ("Sal", "1", "uds")]),
                recipe("Sopa de ajo", [("Tomate", "1", "uds")])]}
TR = {"lang": "en",
      "ingredientes": {"Tomate": "Tomato", "Sal": "Salt"},
      "recetas": {"Gazpacho": {"hash": rt.recipe_hash(DB["Sopas"][0]), "nombre": "Gazpacho EN",
                               "elaboracion": "Step 1.\n\nStep 2."},
                  "Sopa de ajo": {"hash": "desfasado", "nombre": "Garlic soup", "elaboracion": "x"}}}


def ui_strings(path):
    """Literales pasados a _() en un archivo .py (las f-strings no cuentan)."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_"
                and node.args and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            found.add(node.args[0].value)
    return found


class I18nTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("es")

    def test_every_ui_string_has_english(self):
        files = ["client/mobile/recetario_app.py", "shared/mobile_ui.py", "shared/functions.py"]
        missing = set()
        for f in files:
            missing |= ui_strings(os.path.join(ROOT, f)) - set(i18n.EN)
        self.assertEqual(missing, set(), "Faltan en i18n.EN")

    def test_placeholders_match(self):
        import string
        fields = lambda s: {f for _t, f, _s, _c in string.Formatter().parse(s) if f}
        for es, en in i18n.EN.items():
            self.assertEqual(fields(es), fields(en), es)

    def test_categories_and_units(self):
        i18n.set_language("en")
        self.assertEqual(i18n._("Postres"), "Desserts")
        self.assertEqual(functions.format_ingredient({"nombre": "Salt", "cantidad": "2", "unidad": "cuch"}),
                         "2 tbsp Salt")
        self.assertEqual(i18n._("texto sin traducir"), "texto sin traducir")
        i18n.set_language("xx")
        self.assertEqual(i18n.get_language(), "es")

    def test_device_language(self):
        with mock.patch("locale.getlocale", return_value=("Spanish_Spain", "1252")):
            self.assertEqual(i18n.device_language(), "es")
        with mock.patch("locale.getlocale", return_value=("en_GB", "UTF-8")):
            self.assertEqual(i18n.device_language(), "en")
        with mock.patch("locale.getlocale", return_value=("ca_ES", "UTF-8")):
            self.assertEqual(i18n.device_language(), "es")


class RecipeTranslationTests(unittest.TestCase):
    def test_translate_and_fallback(self):
        out = rt.translate_db(DB, TR)
        gaz, ajo = out["Sopas"]
        self.assertEqual((gaz["nombre"], gaz["_id"]), ("Gazpacho EN", "Gazpacho"))
        self.assertEqual(gaz["elaboracion"], "Step 1.\n\nStep 2.")
        self.assertEqual([i["nombre"] for i in gaz["ingredientes"]], ["Tomato", "Salt"])
        self.assertEqual(gaz["ingredientes"][0]["_id"], "Tomate")
        # hash desfasado: la receta se ve en español, pero los ingredientes sí se traducen
        self.assertEqual(ajo["nombre"], "Sopa de ajo")
        self.assertEqual(ajo["ingredientes"][0]["nombre"], "Tomato")
        # sin traducción: igual que el original (con _id)
        self.assertEqual(rt.translate_db(DB, {})["Sopas"][0]["nombre"], "Gazpacho")

    def test_shopping_keys_survive_language_change(self):
        es = functions.aggregate_ingredients(rt.translate_db(DB, {})["Sopas"])
        en = functions.aggregate_ingredients(rt.translate_db(DB, TR)["Sopas"])
        self.assertEqual({functions.item_key(i) for i in es}, {functions.item_key(i) for i in en})
        # sin "_id" (menús guardados antes de los idiomas) la clave es la de siempre
        self.assertEqual(functions.item_key({"nombre": "Tomate", "unidad": "g"}), "tomate|g")

    def test_stale_entries(self):
        recipes, ings = rt.stale_entries(DB, TR)
        self.assertEqual([r["nombre"] for r in recipes], ["Sopa de ajo"])
        self.assertEqual(ings, [])
        recipes, ings = rt.stale_entries(DB, {})
        self.assertEqual((len(recipes), ings), (2, ["Sal", "Tomate"]))

    def test_bundled_translation_matches_db(self):
        path = os.path.join(ROOT, "shared", "data", rt.translation_file("en"))
        if not os.path.exists(path):
            self.skipTest("todavía no hay traducción incluida")
        with open(functions.LOCAL_DB, encoding="utf-8") as f:
            db = {c: [functions.normalize_recipe(r) for r in v] for c, v in json.load(f).items()}
        with open(path, encoding="utf-8") as f:
            tr = json.load(f)
        recipes, ings = rt.stale_entries(db, tr)
        self.assertEqual(([r["nombre"] for r in recipes], ings), ([], []))


class FakeResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def release(tag, assets):
    return json.dumps({"tag_name": tag, "body": "Novedades", "html_url": "https://x/rel",
                       "assets": assets}).encode("utf-8")


class UpdaterTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(updater.parse_version("v1.3.0"), (1, 3, 0))
        self.assertEqual(updater.parse_version("1.4"), (1, 4, 0))
        self.assertTrue(updater.is_newer("v1.10.0", "1.9.9"))
        self.assertFalse(updater.is_newer("v1.3.0", "1.3.0"))

    def test_check_latest(self):
        assets = [{"name": "recipemanager-1.4.0.apk", "browser_download_url": "m"},
                  {"name": "recetario-1.4.0-arm64-v8a-release.apk", "browser_download_url": "u",
                   "size": 21000000, "digest": "sha256:abc"}]
        with mock.patch.object(functions, "http_request", return_value=(200, release("v1.4.0", assets))):
            info = updater.check_latest("1.3.0", "recetario-")
        self.assertEqual((info["version"], info["url"], info["sha256"], info["size"]),
                         ("1.4.0", "u", "abc", 21000000))
        with mock.patch.object(functions, "http_request", return_value=(200, release("v1.3.0", assets))):
            self.assertIsNone(updater.check_latest("1.3.0", "recetario-"))
        with mock.patch.object(functions, "http_request", return_value=(200, release("v2.0.0", []))):
            info = updater.check_latest("1.3.0", "recetario-")
        self.assertIsNone(info["url"])  # Release sin APK: la app abre la página
        self.assertEqual(info["page"], "https://x/rel")

    def test_download_checks_sha256(self):
        data = b"apk" * 1000
        good = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "up", "a.apk")
            seen = []
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse(data)):
                updater.download("https://x/a.apk", dest, good, lambda done, total: seen.append((done, total)))
            self.assertEqual(open(dest, "rb").read(), data)
            self.assertEqual(seen[-1], (len(data), len(data)))
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse(data)):
                with self.assertRaises(ValueError):
                    updater.download("https://x/a.apk", dest + "2", "0" * 64)
            self.assertFalse(os.path.exists(dest + "2") or os.path.exists(dest + "2.part"))


try:
    import kivy  # noqa: F401
    HAS_KIVY = True
except ImportError:
    HAS_KIVY = False


@unittest.skipUnless(HAS_KIVY, "kivy no instalado")
class ClientLanguageTests(unittest.TestCase):
    def setUp(self):
        import recetario_app
        self.tmp = tempfile.TemporaryDirectory()
        self.logic = recetario_app.PlannerLogic(self.tmp.name)
        self.logic.db_es = DB

    def tearDown(self):
        i18n.set_language("es")
        self.tmp.cleanup()

    def test_menu_follows_language(self):
        logic = self.logic
        logic.apply_language()
        logic.selection = {"Sopas": 2}
        logic.generate_menu()
        logic.checked = {functions.item_key(i) for i in logic.shopping_list()}
        i18n.set_language("en")
        logic.translation = TR
        logic.apply_language()
        names = {d["nombre"] for d in logic.menu}
        self.assertEqual(names, {"Gazpacho EN", "Sopa de ajo"})
        self.assertTrue(all(functions.item_key(i) in logic.checked for i in logic.shopping_list()))
        self.assertFalse(logic.reroll(0))  # no hay más sopas: no se repite ninguna

    def test_version_is_readable_by_buildozer(self):
        import re
        import recetario_app
        src = open(os.path.join(ROOT, "client", "mobile", "recetario_app.py"), encoding="utf-8").read()
        m = re.search(r"""__version__ = ['"](.*)['"]""", src)  # = version.regex del .spec
        self.assertEqual(m.group(1), recetario_app.__version__)


if __name__ == "__main__":
    unittest.main()
