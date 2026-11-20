# Recetario «Cocina Rápida» (app para usuarios).
# No compilar desde la raíz: usar  python tools/stage_android.py interface
# y ejecutar buildozer dentro de android_build/interface/.
[app]
title = Cocina Rápida
package.name = recetario
package.domain = org.alherca25
source.dir = .
source.include_exts = py,png,json
version = 1.1.0

# Python fijado a 3.11: con 3.14, python-for-android intenta instalar wheels
# Android de PyPI (p. ej. charset_normalizer) y la compilación falla.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,certifi

icon.filename = %(source.dir)s/assets/icon_main.png
presplash.filename = %(source.dir)s/assets/presplash_main.png
android.presplash_color = #FBF7F1
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
# Solo arm64 (todos los móviles actuales). Con dos arquitecturas p4a recrea su venv
# encima del anterior y deja pip roto (ImportError: open_rich_spinner).
android.archs = arm64-v8a
android.api = 34
android.minapi = 24
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
