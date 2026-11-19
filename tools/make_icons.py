"""Genera los PNG para Android (icono y pantalla de carga) a partir de los logos de assets/.

Uso:  python tools/make_icons.py      (requiere Pillow)
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

for src, name in (("main_logo", "main"), ("edit_logo", "edit")):
    image = Image.open(os.path.join(ASSETS, f"{src}.jpg")).convert("RGB")
    for prefix, size in (("icon", 512), ("presplash", 768)):
        out = os.path.join(ASSETS, f"{prefix}_{name}.png")
        image.resize((size, size), Image.LANCZOS).save(out, optimize=True)
        print("->", os.path.relpath(out, ROOT))
