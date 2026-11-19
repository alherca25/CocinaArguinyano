"""Ejecuta una app Kivy en tamaño móvil, recorre sus pantallas y guarda capturas.

Uso: python tools/screenshot_app.py client|manager <carpeta_salida>
Sirve para revisar el diseño sin un móvil. No modifica datos remotos.
"""
import os
import sys

os.environ.setdefault("KIVY_NO_ARGS", "1")
from kivy.config import Config  # noqa: E402

Config.set("graphics", "width", "412")
Config.set("graphics", "height", "860")
Config.set("graphics", "resizable", "0")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("shared", os.path.join("client", "mobile"), os.path.join("manager", "mobile")):
    sys.path.insert(0, os.path.join(ROOT, sub))

from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402

which, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
steps = []


def shot(name):
    def _do(*_):
        Window.screenshot(os.path.join(out_dir, f"{name}.png"))
    return _do


def run_steps(app, plan):
    t = 0
    for delay, action in plan:
        t += delay
        Clock.schedule_once(lambda *_, a=action: a(app), t)
    Clock.schedule_once(lambda *_: app.stop(), t + 1)


if which == "client":
    from recetario_app import CocinaApp as AppClass

    def pick(app):
        cats = app.logic.categories
        for c, n in zip(cats[:4], (1, 2, 1, 1)):
            app.planner.steppers[c].set(n)

    plan = [
        (6, lambda a: shot("1_planner")()),
        (0.5, pick),
        (0.5, lambda a: shot("2_planner_selected")()),
        (0.3, lambda a: (a.logic.checked.clear(), a.generate_menu())),
        (1.0, lambda a: shot("3_menu")()),
        (0.3, lambda a: a.menu_screen.select_tab("Compra")),
        (0.8, lambda a: shot("4_compra")()),
        (0.3, lambda a: a.open_recipe(a.logic.menu[0])),
        (0.8, lambda a: shot("5_receta")()),
        (0.3, lambda a: a.go_home() or a.open_browse()),
        (0.8, lambda a: shot("6_recetario")()),
    ]
else:
    import functions
    from gestor_app import MvRecipeApp as AppClass

    # Sin token real: se simula el acceso y se lee la BD pública sin autenticar.
    _real_get = functions.github_get_json
    functions.github_check_access = lambda token, repo=None: "demo"
    functions.github_get_json = lambda token=None, **kw: _real_get(None, **kw)

    def edit(app):
        s = app.screen
        s.change_mode("edit")
        s.load_recipe(app.logic.categories[0], 0)

    plan = [
        (4, lambda a: shot("0_lock")()),
        (0.2, lambda a: a.try_unlock("demo", on_fail=print, busy=False)),
        (5, lambda a: shot("1_add")()),
        (0.3, edit),
        (1.0, lambda a: shot("2_edit")()),
        (0.3, lambda a: a.logic.delete_token()),  # no dejar el token simulado guardado
    ]

app = AppClass()
Clock.schedule_once(lambda *_: run_steps(app, plan), 0)
app.run()
