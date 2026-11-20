# Recetario «Cocina Rápida» (app para usuarios).
# No compilar desde aquí: usar  python tools/stage_android.py client
# y después  bash tools/wsl_build.sh client [release]  (ver docs/ANDROID.md).
[app]
title = Cocina Rápida
package.name = recetario
package.domain = org.alherca25
source.dir = .
source.include_exts = py,png,json
source.exclude_dirs = build_hooks, bin

# La versión sale de __version__ en main.py (recetario_app.py): así la app sabe
# qué versión es para buscar actualizaciones, y sólo hay que cambiarla en un sitio.
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

# Python fijado a 3.11: con 3.14, python-for-android intenta instalar wheels
# Android de PyPI (p. ej. charset_normalizer) y la compilación falla.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,certifi

icon.filename = %(source.dir)s/assets/icon_main.png
presplash.filename = %(source.dir)s/assets/presplash_main.png
android.presplash_color = #FBF7F1
orientation = portrait
fullscreen = 0

# INTERNET: recetas y actualizaciones. REQUEST_INSTALL_PACKAGES: abrir el instalador
# con la versión nueva (Android pide al usuario que lo permita la primera vez).
android.permissions = INTERNET, REQUEST_INSTALL_PACKAGES

# FileProvider (androidx) para pasar el APK descargado al instalador.
android.enable_androidx = True
android.gradle_dependencies = androidx.core:core:1.12.0
p4a.hook = build_hooks/p4a_hook.py

# «buildozer android release» genera un APK (no un AAB de Google Play), firmado con
# la clave de ~/.cocina_keys (tools/create_keystore.sh).
android.release_artifact = apk

# Solo arm64 (todos los móviles actuales). Con dos arquitecturas p4a recrea su venv
# encima del anterior y deja pip roto (ImportError: open_rich_spinner).
android.archs = arm64-v8a
android.api = 34
android.minapi = 24
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
