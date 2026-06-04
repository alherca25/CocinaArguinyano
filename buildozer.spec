[app]

# Nombre que aparece en el lanzador de Android
title = Cocina Rápida

# Nombre del paquete (sin espacios, minúsculas)
package.name = cocinarapida

# Dominio del paquete → el bundle ID final será com.arguinyano.cocinarapida
package.domain = com.arguinyano

# Directorio raíz con el código fuente (donde está main.py)
source.dir = .

# Extensiones de archivo que se incluirán en el APK
source.include_exts = py,png,jpg,jpeg,kv,atlas,xlsx,ttf

# Versión de la app
version = 1.0

# -----------------------------------------------------------------------
# Dependencias Python (python-for-android las compilará para ARM)
# -----------------------------------------------------------------------
# App adaptada a Kivy. Se eliminan tkinter y reportlab porque no encajan
# en este flujo Android con Buildozer/p4a.
#requirements = python3,kivy==2.3.0,pandas,numpy,requests,openpyxl,et_xmlfile,fpdf2
requirements = python3,kivy==2.3.0,requests,openpyxl,et_xmlfile,fpdf2

# -----------------------------------------------------------------------
# Icono y pantalla de carga
# -----------------------------------------------------------------------
icon.filename = %(source.dir)s/logo.png

# Orientación de la pantalla
orientation = portrait

# -----------------------------------------------------------------------
# Android
# -----------------------------------------------------------------------
# INTERNET es necesaria para descargar el Excel desde GitHub.
# Para la primera compilación estable, mejor evitar permisos de almacenamiento
# compartido si vas a guardar dentro del almacenamiento de la app.
android.permissions = INTERNET

# API objetivo y mínima
android.api = 33
android.minapi = 24

# NDK recomendado para Kivy 2.3 + python-for-android
android.ndk = 25b

# Arquitecturas a compilar (arm64 para dispositivos modernos + armeabi para compatibilidad)
#android.archs = arm64-v8a, armeabi-v7a
android.archs = arm64-v8a

# Habilitar AndroidX
android.enable_androidx = True

# Gradle versión compatible
android.gradle_dependencies =

# Permite depuración por ADB
android.logcat_filters = *:S python:D

# -----------------------------------------------------------------------
# Buildozer internals
# -----------------------------------------------------------------------
[buildozer]

# Directorio donde buildozer descarga el SDK/NDK y construye
# (puedes cambiarlo a una ruta con más espacio en disco)
# build_dir = ./.buildozer

# Nivel de log: 0 (silencioso) → 2 (verbose)
log_level = 2

# Advertencia: deja esto en 0 en producción
warn_on_root = 1