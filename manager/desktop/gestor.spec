# -*- mode: python ; coding: utf-8 -*-
# Gestor de Recetas de escritorio (.exe).  Desde la raíz del repo:
#   pyinstaller manager/desktop/gestor.spec --distpath apk --workpath build/pyinstaller
# El .exe busca el clon ../BaseDatosRecetas/CocinaArguinyano.json junto a su carpeta.
import os

SHARED = os.path.abspath(os.path.join(SPECPATH, "..", "..", "shared"))

a = Analysis(
    [os.path.join(SPECPATH, "gestor_desktop.py")],
    pathex=[SHARED],
    datas=[(os.path.join(SHARED, "assets", "edit_logo.ico"), ".")],
    hiddenimports=["functions", "desktop_theme"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="CocinaRapida-Gestor",
    console=False,
    upx=True,
    icon=[os.path.join(SHARED, "assets", "edit_logo.ico")],
)
