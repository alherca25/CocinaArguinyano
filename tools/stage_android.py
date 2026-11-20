"""Prepara una carpeta limpia para compilar cada APK con Buildozer.

Uso:
    python tools/stage_android.py client      # Recetario (usuarios)
    python tools/stage_android.py manager     # Gestor de Recetas (administrador)

Crea build/android/<app>/ con:
    main.py                       <- client/mobile/recetario_app.py o manager/mobile/gestor_app.py
    functions.py, mobile_ui.py, i18n.py, recipe_translation.py, updater.py  <- shared/
    assets/icon_*.png, assets/presplash_*.png
    data/*.json                   (sólo cliente: BD y traducciones para arrancar sin conexión)
    build_hooks/p4a_hook.py       (sólo cliente: añade el FileProvider para actualizar la app)
    buildozer.spec                <- <app>/buildozer.spec

Después (Linux/WSL):  tools/wsl_build.sh <app> [release]
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "shared")

APPS = {
    "client": {"main": "client/mobile/recetario_app.py", "logo": "main", "data": True,
               "hook": "client/android/p4a_hook.py"},
    "manager": {"main": "manager/mobile/gestor_app.py", "logo": "edit", "data": False,
                "hook": None},
}
SHARED_MODULES = ["functions.py", "mobile_ui.py", "i18n.py", "recipe_translation.py", "updater.py"]


def stage(app):
    cfg = APPS[app]
    out = os.path.join(ROOT, "build", "android", app)
    os.makedirs(out, exist_ok=True)
    # Se conservan .buildozer/ y bin/ (caché de compilación); el resto se regenera.
    for name in os.listdir(out):
        if name in (".buildozer", "bin"):
            continue
        path = os.path.join(out, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    shutil.copy2(os.path.join(ROOT, cfg["main"]), os.path.join(out, "main.py"))
    for name in SHARED_MODULES:
        shutil.copy2(os.path.join(SHARED, name), os.path.join(out, name))
    os.makedirs(os.path.join(out, "assets"))
    for prefix in ("icon", "presplash"):
        name = f"{prefix}_{cfg['logo']}.png"
        shutil.copy2(os.path.join(SHARED, "assets", name), os.path.join(out, "assets", name))
    if cfg["data"]:  # BD y traducciones para el primer arranque sin conexión
        os.makedirs(os.path.join(out, "data"))
        for name in os.listdir(os.path.join(SHARED, "data")):
            if name.endswith(".json"):
                shutil.copy2(os.path.join(SHARED, "data", name), os.path.join(out, "data", name))
    if cfg["hook"]:  # fuera del código de la app (source.exclude_dirs = build_hooks)
        os.makedirs(os.path.join(out, "build_hooks"))
        shutil.copy2(os.path.join(ROOT, cfg["hook"]), os.path.join(out, "build_hooks", "p4a_hook.py"))
    shutil.copy2(os.path.join(ROOT, app, "buildozer.spec"), os.path.join(out, "buildozer.spec"))
    print(f"Preparado: {os.path.relpath(out, ROOT)}")
    return out


if __name__ == "__main__":
    targets = sys.argv[1:] or list(APPS)
    for target in targets:
        if target not in APPS:
            sys.exit(f"App desconocida: {target}. Usa: {', '.join(APPS)}")
        stage(target)
