# 🍳 Cocina Rápida

Planificador de menús semanales con lista de la compra. Eliges cuántos platos quieres de cada tipo, la app escoge recetas al azar del recetario, te enseña cada receta y junta los ingredientes de todas en una sola lista de la compra.

El proyecto tiene dos programas:

| | Para quién | Android | Escritorio |
|---|---|---|---|
| **Recetario** (`client/`) | Cualquier usuario: **descarga libre** | `client/mobile/recetario_app.py` | `client/desktop/recetario_desktop.py` |
| **Gestor de Recetas** (`manager/`) | Sólo el administrador: **bloqueado** | `manager/mobile/gestor_app.py` | `manager/desktop/gestor_desktop.py` |

### ¿Cómo queda bloqueado el Gestor?
- La app móvil arranca en una **pantalla de bloqueo**. Sólo deja entrar con un token de GitHub cuyo usuario tenga **permiso de escritura** sobre `alherca25/BaseDatosRecetas`, y lo comprueba con GitHub en cada arranque. «Salir» borra el token del móvil.
- Su APK **no se publica**: se compila a mano (en local o con el workflow manual `Gestor APK`).
- Aunque alguien consiguiera el APK, sin ese token no puede modificar nada: GitHub rechaza cualquier escritura.

El Gestor de escritorio no tiene bloqueo propio. Edita el clon local de `BaseDatosRecetas`, y para publicar los cambios hace falta poder hacer *push* a ese repositorio.

## Estructura

```
client/                Recetario (público)
  mobile/recetario_app.py     app Kivy → APK
  desktop/recetario_desktop.py  app customtkinter (PDF) → .exe (recetario.spec)
  buildozer.spec
manager/               Gestor de Recetas (privado)
  mobile/gestor_app.py        app Kivy con pantalla de bloqueo → APK
  desktop/gestor_desktop.py   edita ../BaseDatosRecetas → .exe (gestor.spec)
  buildozer.spec
shared/                código y recursos comunes
  functions.py          lógica: descarga, caché, filtros, menú, lista de la compra, API de GitHub
  mobile_ui.py          componentes visuales Kivy (paleta de los logos)
  desktop_theme.py      tema customtkinter
  assets/               logos (.ico/.jpg) e iconos PNG para Android
  data/                 copia de la base de datos (para arrancar sin conexión)
tools/                 stage_android.py · wsl_build.sh · make_icons.py · screenshot_app.py
tests/                 tests de la lógica
docs/                  ANDROID.md (compilar APK) · CHECKLIST.md (estado del proyecto)
.github/workflows/     client.yml (tests + APK + Release) · manager.yml (manual) · build-apk.yml
```

## Base de datos

Las recetas están en el repositorio [`alherca25/BaseDatosRecetas`](https://github.com/alherca25/BaseDatosRecetas) (`CocinaArguinyano.json`):

```json
{ "Sopas": [ { "nombre": "...", "pagina": "185", "elaboracion": "...",
               "filtros": { "vegetariano": false, "gluten_free": false },
               "ingredientes": [ { "nombre": "Tomate", "cantidad": "2", "unidad": "uds" } ] } ] }
```

Unidades: `uds`, `g`, `mL`, `cuch`.

## Ejecutar en el ordenador

```powershell
python -m venv venvArguinyano
venvArguinyano\Scripts\activate
pip install -r requirements_desktop.txt -r requirements_mobile.txt

python client\desktop\recetario_desktop.py    # Recetario escritorio (PDF en Documentos\Cocina Rápida)
python client\mobile\recetario_app.py         # Recetario móvil en una ventana
python manager\desktop\gestor_desktop.py      # Gestor escritorio
python manager\mobile\gestor_app.py           # Gestor móvil en una ventana
```

Tests: `python -m unittest discover -s tests`

## Compilar

- **APK (Android):** ver [docs/ANDROID.md](docs/ANDROID.md). En resumen: `python tools\stage_android.py` en Windows y luego `bash tools/wsl_build.sh client` (o `manager`) en WSL. Los APK quedan en `apk/`.
- **.exe (Windows):** `pip install pyinstaller`, y después `pyinstaller client/desktop/recetario.spec --distpath apk --workpath build/pyinstaller` (y lo mismo con `manager/desktop/gestor.spec`).
- **Publicar el Recetario:** crea una etiqueta (`git tag v1.1.0 && git push --tags`) y el workflow `Recetario APK` lo publica como *Release*. Necesita GitHub Actions activo en la cuenta.

## Licencia

Proyecto de uso personal y educativo. Las recetas pertenecen a sus autores.
