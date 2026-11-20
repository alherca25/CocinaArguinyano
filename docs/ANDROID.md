# 📱 Compilar y publicar los APK

| App | Spec | Código | Se publica |
|---|---|---|---|
| Recetario | `client/buildozer.spec` | `client/mobile/recetario_app.py` | Sí: GitHub Releases (la app se actualiza sola) |
| Gestor de Recetas | `manager/buildozer.spec` | `manager/mobile/gestor_app.py` | No (uso privado) |

Buildozer sólo funciona en Linux. En Windows se usa **WSL con Ubuntu‑22.04**. Es la distribución que tiene Buildozer, el SDK y la caché de compilación. Si tu WSL por defecto es otra (`wsl -l -v`), ábrela siempre con `wsl -d Ubuntu-22.04`.

## Compilar

**1. Preparar las apps** (PowerShell, en la raíz del repo):
```powershell
.\venvArguinyano\Scripts\python.exe tools\stage_android.py        # o: ... client / ... manager
```
Crea `build/android/<app>` con:
- `main.py` y los módulos de `shared/`;
- los iconos;
- las copias de la BD y de las traducciones;
- el hook de compilación;
- el `buildozer.spec`.

**2. Compilar** (WSL):
```powershell
wsl -d Ubuntu-22.04
```
```bash
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client release   # Recetario para publicar
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client           # Recetario de pruebas (debug)
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" manager          # Gestor (debug)
```
El script compila en `~/cocina_build/<app>` (en el disco de Linux, mucho más rápido), guarda el log en `~/cocina_build/<app>.log` y copia el APK a `apk/` en el repo.

- La primera compilación de cada app tarda 20-40 min. Las siguientes, pocos minutos.
- **Instalar en el móvil:** copia el `.apk` al teléfono y ábrelo (permite «instalar apps desconocidas»), o usa `adb install -r apk/<archivo>.apk`.

## Clave de firma (release)

Android sólo instala una actualización si el APK nuevo está **firmado con la misma clave** que la app instalada. Por eso el Recetario que se publica se firma con una clave propia y permanente, no con la de depuración de WSL.

Se crea **una sola vez**:
```bash
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/create_keystore.sh" client
```
- Pide una contraseña.
- Guarda la clave en `~/.cocina_keys/client.jks` y los datos que necesita `wsl_build.sh` en `~/.cocina_keys/client.env`.
- Hace una copia de seguridad en `C:\Users\<tú>\CocinaRapida-claves\`.

> ⚠️ **No pierdas la clave ni la contraseña, y no las subas a GitHub.** Sin ellas no se pueden publicar actualizaciones, y cada usuario tendría que desinstalar y volver a instalar la app.

Las versiones de depuración (`debug`) y las `release` tienen firmas distintas. Para pasar de una a otra en el móvil hay que desinstalar la app primero. Al hacerlo se pierden el menú y la lista guardados.

## Publicar una versión del Recetario

1. Sube `__version__` en `client/mobile/recetario_app.py`, por ejemplo `"1.3.0"` → `"1.3.1"`. Buildozer lee la versión de ahí, y Android exige que cada actualización tenga un número mayor.
2. Prepara y compila en modo `release` (ver los pasos de [Compilar](#compilar)).
3. Crea la Release en GitHub con la etiqueta `v` + la versión y el APK adjunto:
   ```powershell
   gh release create v1.3.1 apk\recetario-1.3.1-arm64-v8a-release.apk --title "Cocina Rápida 1.3.1" --notes "Qué hay de nuevo..."
   ```
   También se puede hacer desde la web: *Releases → Draft a new release*.

**Cómo se actualiza la app:**
- Al abrirse, como mucho una vez al día, y cuando el usuario pulsa **Buscar actualizaciones**, consulta la última Release.
- Si hay una versión mayor, ofrece descargarla y comprueba su SHA‑256.
- Después abre el instalador de Android: el usuario sólo pulsa **Instalar**, y se conservan su menú y su lista.
- La primera vez, Android pide permitir que «Cocina Rápida» instale aplicaciones.
- El texto de la Release (`--notes`) se muestra en el aviso de actualización.

## Traducciones

La interfaz y las recetas se traducen por separado:

- **Interfaz:** los textos están en `shared/i18n.py`; la clave es la frase en español. Un test (`tests/test_i18n_update.py`) avisa si una frase nueva no tiene traducción.
- **Recetas:** cada idioma tiene su archivo en BaseDatosRecetas, por ejemplo `CocinaArguinyano.en.json`, con una copia en `shared/data/` para arrancar sin conexión. Si una receta cambia en el Gestor, su traducción queda desfasada y la app la muestra en español hasta que se vuelva a traducir:
  ```powershell
  python tools\translate_db.py check en                      # qué falta o está desfasado
  python tools\translate_db.py export en pendientes.json     # textos en español para traducir
  python tools\translate_db.py import en traducido.json      # incorpora la traducción
  ```
  Después, haz commit y push en BaseDatosRecetas: la app descarga la traducción nueva sin recompilar.

## Preparación de WSL (sólo una vez)

```bash
sudo apt update && sudo apt install -y build-essential git zip unzip autoconf automake libtool \
  pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev \
  libssl-dev libltdl-dev python3-pip python3-venv openjdk-17-jdk
python3 -m pip install --user --upgrade Cython buildozer "virtualenv==20.21.0" setuptools
```

Si WSL no tiene internet, añade esto a `%USERPROFILE%\.wslconfig` y ejecuta `wsl --shutdown`:
```
[wsl2]
networkingMode=mirrored
```

## Problemas conocidos (ya resueltos en la configuración)

| Síntoma | Causa | Solución aplicada |
|---|---|---|
| `charset_normalizer-…-android…whl is not a supported wheel` | p4a con Python 3.14 intenta usar wheels Android de PyPI | Python fijado a **3.11.9** en los `.spec` |
| `Can not perform a '--user' install` | Buildozer instalado dentro de un virtualenv | Instalar Buildozer con `pip --user` |
| Fallos raros de compilación en WSL | El PATH de Windows tiene rutas con espacios | `wsl_build.sh` limpia el PATH |
| Archivo `…x86_64-linux-gnu.so` dentro del APK | pip instala wheels de PC para `charset-normalizer`/`chardet` | `PIP_NO_BINARY="charset-normalizer,chardet"` |
| `ImportError: open_rich_spinner` | Con 2 arquitecturas, p4a recrea su venv encima del anterior y rompe pip | Sólo **arm64-v8a** (todos los móviles actuales) |
| El instalador no puede abrir el APK descargado | Desde Android 7 no se permiten rutas `file://` | `client/android/p4a_hook.py` añade un FileProvider (androidx) al manifiesto |
| «La app no está instalada» al actualizar | El APK nuevo está firmado con otra clave | Publicar siempre con `release` y la misma clave |

## Notas

- **Permisos del Recetario:**
  - `INTERNET`;
  - `REQUEST_INSTALL_PACKAGES`, sólo para abrir el instalador con una versión nueva.
- **Exportar:** se usa el menú **Compartir** de Android, sin escribir archivos.
- **HTTPS:** se incluye `certifi`.
- **Iconos:** si cambias los logos de `shared/assets/`, regenera los PNG con `python tools/make_icons.py`.
- **GitHub Actions:** los workflows hacen lo mismo en la nube, pero necesitan que la cuenta no tenga Actions bloqueado por facturación. Las Releases se pueden crear igualmente con `gh`.
