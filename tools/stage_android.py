"""Prepara una carpeta limpia para compilar cada APK con Buildozer.

Uso:
    python tools/stage_android.py interface   # Recetario (usuarios)
    python tools/stage_android.py manager     # Gestor de Recetas (administrador)

Crea android_build/<app>/ con:
    main.py            <- src/MvInterface.py o src/MvRecipeManager.py
    functions.py, mobile_ui.py
    assets/icon_*.png, assets/presplash_*.png
    CocinaArguinyano.json (sólo Recetario: copia para el primer arranque sin conexión)
    buildozer.spec     <- buildozer_<app>.spec

Después:  cd android_build/<app> && buildozer android debug
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APPS = {
    "interface": {"main": "MvInterface.py", "logo": "main",
                  "extra": [("data/CocinaArguinyano.json", "CocinaArguinyano.json")]},
    "manager": {"main": "MvRecipeManager.py", "logo": "edit", "extra": []},
}
SHARED = ["functions.py", "mobile_ui.py"]


def stage(app):
    cfg = APPS[app]
    out = os.path.join(ROOT, "android_build", app)
    # Se conserva .buildozer/ y bin/ entre compilaciones (caché); el resto se regenera.
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):
        if name in (".buildozer", "bin"):
            continue
        path = os.path.join(out, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    src = os.path.join(ROOT, "src")
    shutil.copy2(os.path.join(src, cfg["main"]), os.path.join(out, "main.py"))
    for name in SHARED:
        shutil.copy2(os.path.join(src, name), os.path.join(out, name))
    os.makedirs(os.path.join(out, "assets"))
    for prefix in ("icon", "presplash"):
        name = f"{prefix}_{cfg['logo']}.png"
        shutil.copy2(os.path.join(ROOT, "assets", name), os.path.join(out, "assets", name))
    for rel_src, rel_dst in cfg["extra"]:
        shutil.copy2(os.path.join(ROOT, rel_src), os.path.join(out, rel_dst))
    shutil.copy2(os.path.join(ROOT, f"buildozer_{app}.spec"), os.path.join(out, "buildozer.spec"))
    print(f"Preparado: {os.path.relpath(out, ROOT)}")
    return out


if __name__ == "__main__":
    targets = sys.argv[1:] or list(APPS)
    for target in targets:
        if target not in APPS:
            sys.exit(f"App desconocida: {target}. Usa: {', '.join(APPS)}")
        stage(target)
