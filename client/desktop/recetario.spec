# -*- mode: python ; coding: utf-8 -*-
# Recetario de escritorio (.exe).  Desde la raíz del repo:
#   pyinstaller client/desktop/recetario.spec --distpath apk --workpath build/pyinstaller
import os

SHARED = os.path.abspath(os.path.join(SPECPATH, "..", "..", "shared"))

a = Analysis(
    [os.path.join(SPECPATH, "recetario_desktop.py")],
    pathex=[SHARED],
    datas=[(os.path.join(SHARED, "assets", "main_logo.ico"), "."),
           (os.path.join(SHARED, "data", "CocinaArguinyano.json"), "data")],
    hiddenimports=["functions", "desktop_theme"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="CocinaRapida-Recetario",
    console=False,
    upx=True,
    icon=[os.path.join(SHARED, "assets", "main_logo.ico")],
)
