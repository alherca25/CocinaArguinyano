# Gestor de Recetas (app para el administrador).
# No compilar desde la raíz: usar  python tools/stage_android.py manager
# y ejecutar buildozer dentro de android_build/manager/.
[app]
title = Gestor de Recetas
package.name = recipemanager
package.domain = org.alherca25
source.dir = .
source.include_exts = py,png,json
version = 1.1.0

# Python fijado a 3.11: ver buildozer_interface.spec.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,certifi

icon.filename = %(source.dir)s/assets/icon_edit.png
presplash.filename = %(source.dir)s/assets/presplash_edit.png
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
