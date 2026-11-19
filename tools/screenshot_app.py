"""Ejecuta una app Kivy en tamaño móvil, recorre sus pantallas y guarda capturas.

Uso: python tools/screenshot_app.py interface|manager <carpeta_salida>
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
sys.path.insert(0, os.path.join(ROOT, "src"))

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


if which == "interface":
    from MvInterface import CocinaApp as AppClass

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
    from MvRecipeManager import MvRecipeApp as AppClass

    def edit(app):
        s = app.screen
        s.change_mode("edit")
        s.load_recipe(app.logic.categories[0], 0)

    plan = [
        (6, lambda a: shot("1_add")()),
        (0.3, edit),
        (1.0, lambda a: shot("2_edit")()),
        (0.3, lambda a: a.screen.show_settings()),
        (0.8, lambda a: shot("3_settings")()),
    ]

app = AppClass()
Clock.schedule_once(lambda *_: run_steps(app, plan), 0)
app.run()
