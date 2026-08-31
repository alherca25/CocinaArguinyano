[app]
title = Recetario Rápido
package.name = recetario
package.domain = org.alherca25
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ico,ttf,otf
version = 1.0
requirements = python3,kivy,requests,fpdf2,plyer,urllib3,certifi,chardet,idna
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
