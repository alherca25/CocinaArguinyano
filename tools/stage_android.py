"""Prepara una carpeta limpia para compilar cada APK con Buildozer.

Uso:
    python tools/stage_android.py client      # Recetario (usuarios)
    python tools/stage_android.py manager     # Gestor de Recetas (administrador)

Crea build/android/<app>/ con:
    main.py                       <- client/mobile/recetario_app.py o manager/mobile/gestor_app.py
    functions.py, mobile_ui.py    <- shared/
    assets/icon_*.png, assets/presplash_*.png
    data/CocinaArguinyano.json    (sólo cliente: copia para el primer arranque sin conexión)
    buildozer.spec                <- <app>/buildozer.spec

Después (Linux/WSL):  tools/wsl_build.sh <app>
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "shared")

APPS = {
    "client": {"main": "client/mobile/recetario_app.py", "logo": "main", "data": True},
    "manager": {"main": "manager/mobile/gestor_app.py", "logo": "edit", "data": False},
}
SHARED_MODULES = ["functions.py", "mobile_ui.py"]


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
    if cfg["data"]:
        os.makedirs(os.path.join(out, "data"))
        shutil.copy2(os.path.join(SHARED, "data", "CocinaArguinyano.json"),
                     os.path.join(out, "data", "CocinaArguinyano.json"))
    shutil.copy2(os.path.join(ROOT, app, "buildozer.spec"), os.path.join(out, "buildozer.spec"))
    print(f"Preparado: {os.path.relpath(out, ROOT)}")
    return out


if __name__ == "__main__":
    targets = sys.argv[1:] or list(APPS)
    for target in targets:
        if target not in APPS:
            sys.exit(f"App desconocida: {target}. Usa: {', '.join(APPS)}")
        stage(target)
