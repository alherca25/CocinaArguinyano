"""Tests de la lógica (sin red). Ejecutar desde la raíz:  python -m unittest discover tests"""
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shared"))
sys.path.insert(0, os.path.join(ROOT, "manager", "mobile"))
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

import functions  # noqa: E402


def recipe(name, veg=False, gf=False, ings=()):
    return {"nombre": name, "pagina": "12.0", "elaboracion": "x",
            "filtros": {"vegetariano": veg, "gluten_free": gf},
            "ingredientes": [{"nombre": n, "cantidad": c, "unidad": u} for n, c, u in ings]}


DB = {
    "Sopas": [recipe("A", veg=True, ings=[("Cebolla", "1", "uds"), ("Sal", "", "")]),
              recipe("B", ings=[("cebolla", "0.5", "uds"), ("Agua", "500", "mL")]),
              recipe("C", veg=True, gf=True)],
    "Postres": [recipe("D", gf=True, ings=[("Azúcar", "100", "g"), ("Cebolla", "2", "g")])],
}


class FunctionsTests(unittest.TestCase):
    def test_filter(self):
        self.assertEqual(len(functions.filter_recipes(DB["Sopas"], "Todo")), 3)
        self.assertEqual([r["nombre"] for r in functions.filter_recipes(DB["Sopas"], "Vegetariano")], ["A", "C"])
        self.assertEqual([r["nombre"] for r in functions.filter_recipes(DB["Sopas"], "Gluten Free")], ["C"])

    def test_filter_legacy_flat_format(self):
        legacy = [{"nombre": "X", "vegetariano": True}]
        self.assertEqual(len(functions.filter_recipes(legacy, "Vegetariano")), 1)

    def test_select_limited(self):
        dishes, limited = functions.select_random_dishes(DB, "Sopas", 5, "Vegetariano")
        self.assertEqual(len(dishes), 2)
        self.assertTrue(limited)
        self.assertEqual(functions.select_random_dishes(DB, "Nope", 2, "Todo"), ([], False))

    def test_build_menu_unique(self):
        menu = functions.build_menu(DB, {"Sopas": 3, "Postres": 1}, "Todo")
        self.assertEqual(len(menu), 4)
        self.assertEqual(len({d["nombre"] for d in menu}), 4)
        self.assertTrue(all("Tipo" in d for d in menu))

    def test_aggregate(self):
        items = functions.aggregate_ingredients(DB["Sopas"] + DB["Postres"])
        as_map = {(i["nombre"].lower(), i["unidad"]): i["cantidad"] for i in items}
        self.assertEqual(as_map[("cebolla", "uds")], "1.5")   # 1 + 0.5, sin distinguir mayúsculas
        self.assertEqual(as_map[("cebolla", "g")], "2")       # otra unidad: línea aparte
        self.assertEqual(as_map[("sal", "")], "")
        self.assertEqual([i["nombre"] for i in items], sorted([i["nombre"] for i in items], key=str.lower))

    def test_format(self):
        self.assertEqual(functions.format_quantity("1.0"), "1")
        self.assertEqual(functions.format_quantity("0,25"), "0.25")
        self.assertEqual(functions.format_quantity("nan"), "")
        self.assertEqual(functions.format_page("185.0"), "185")
        self.assertEqual(functions.format_ingredient({"nombre": "Sal", "cantidad": "", "unidad": ""}), "Sal")
        self.assertEqual(functions.format_ingredient({"nombre": "Ajo", "cantidad": "2.0", "unidad": "uds"}), "2 uds Ajo")

    def test_normalize_legacy(self):
        r = functions.normalize_recipe({"nombre": " X ", "vegetariano": True, "pagina": "3.0",
                                        "ingredientes": [{"nombre": ""}, {"nombre": "Ajo", "cantidad": 1}]})
        self.assertEqual(r["nombre"], "X")
        self.assertEqual(r["filtros"], {"vegetariano": True, "gluten_free": False})
        self.assertEqual(r["pagina"], "3")
        self.assertEqual(r["ingredientes"], [{"nombre": "Ajo", "cantidad": "1", "unidad": ""}])
        self.assertNotIn("vegetariano", r)

    def test_texts(self):
        items = functions.aggregate_ingredients(DB["Sopas"])
        checked = {functions.item_key(items[0])}
        text = functions.shopping_to_text(items, checked=checked)
        self.assertNotIn(items[0]["nombre"], text)
        self.assertIn("ELABORACIÓN", functions.menu_to_text([dict(DB["Sopas"][0], Tipo="Sopas")]).upper())

    def test_cache_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            cache = os.path.join(d, "c.json")
            with mock.patch.object(functions, "load_recipes", side_effect=[DB]):
                db, origin = functions.load_recipes_with_cache(cache)
            self.assertEqual(origin, "online")
            with mock.patch.object(functions, "http_request", side_effect=OSError("offline")):
                db, origin = functions.load_recipes_with_cache(cache)
            self.assertEqual((db, origin), (DB, "cache"))
            with mock.patch.object(functions, "http_request", side_effect=OSError("offline")):
                with self.assertRaises(RuntimeError):
                    functions.load_recipes_with_cache(os.path.join(d, "missing.json"))


class AccessTests(unittest.TestCase):
    def _resp(self, payload):
        import json as _j
        return (200, _j.dumps(payload).encode())

    def test_access_ok(self):
        with mock.patch.object(functions, "http_request",
                               side_effect=[self._resp({"permissions": {"push": True}}),
                                            self._resp({"login": "alherca25"})]):
            self.assertEqual(functions.github_check_access("tok"), "alherca25")

    def test_access_read_only_rejected(self):
        with mock.patch.object(functions, "http_request",
                               return_value=self._resp({"permissions": {"push": False, "pull": True}})):
            with self.assertRaises(functions.GitHubError):
                functions.github_check_access("tok")

    def test_access_bad_token(self):
        import urllib.error
        err = urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)
        with mock.patch.object(functions, "http_request", side_effect=err):
            with self.assertRaisesRegex(functions.GitHubError, "inválido"):
                functions.github_check_access("tok")

    def test_empty_token(self):
        with self.assertRaises(functions.GitHubError):
            functions.github_check_access("")

    def test_bundled_db_exists(self):
        db = functions.load_recipes(functions.LOCAL_DB, is_local=True)
        self.assertGreater(sum(len(v) for v in db.values()), 0)


try:
    import kivy  # noqa: F401
    HAS_KIVY = True
except ImportError:
    HAS_KIVY = False


@unittest.skipUnless(HAS_KIVY, "kivy no instalado")
class ManagerLogicTests(unittest.TestCase):
    def setUp(self):
        import gestor_app
        self.mod = gestor_app
        self.tmp = tempfile.TemporaryDirectory()
        self.logic = gestor_app.ManagerLogic(self.tmp.name)
        self.logic.save_token("tok")

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        with mock.patch.object(functions, "github_get_json", return_value=(DB, "sha1")):
            self.logic.load()

    def test_cannot_save_before_load(self):
        with mock.patch.object(functions, "github_put_json") as put:
            with self.assertRaises(functions.GitHubError):
                self.logic.add("Sopas", recipe("Z"))
            put.assert_not_called()

    def test_add_uses_sha_and_updates(self):
        self.load()
        with mock.patch.object(functions, "github_put_json", return_value="sha2") as put:
            self.logic.add("Sopas", recipe("Z"))
        args = put.call_args[0]
        self.assertEqual(args[0], "tok")
        self.assertEqual(args[2], "sha1")
        self.assertEqual(self.logic.sha, "sha2")
        self.assertEqual(self.logic.db["Sopas"][-1]["nombre"], "Z")

    def test_failed_save_leaves_db_untouched(self):
        self.load()
        before = [r["nombre"] for r in self.logic.db["Sopas"]]
        with mock.patch.object(functions, "github_put_json", side_effect=functions.GitHubConflict("x")):
            with self.assertRaises(functions.GitHubConflict):
                self.logic.delete("Sopas", 0)
        self.assertEqual([r["nombre"] for r in self.logic.db["Sopas"]], before)
        self.assertEqual(self.logic.sha, "sha1")

    def test_move_category(self):
        self.load()
        with mock.patch.object(functions, "github_put_json", return_value="sha2"):
            self.logic.update("Sopas", 0, "Postres", recipe("A2"))
        self.assertNotIn("A", [r["nombre"] for r in self.logic.db["Sopas"]])
        self.assertEqual(self.logic.db["Postres"][-1]["nombre"], "A2")

    def test_validate(self):
        ok, errs = self.mod.validate_recipe("Plato", "12", [{"nombre": "Ajo", "cantidad": "1,5", "unidad": "uds"}])
        self.assertEqual(errs, [])
        self.assertEqual(ok[0]["cantidad"], "1.5")
        _, errs = self.mod.validate_recipe("", "x", [{"nombre": "Ajo", "cantidad": "mucho", "unidad": ""}])
        self.assertEqual(len(errs), 3)


if __name__ == "__main__":
    unittest.main()
