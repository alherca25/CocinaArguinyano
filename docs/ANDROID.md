# 📱 Compilar los APK

| App | Spec | Código | Se publica |
|---|---|---|---|
| Recetario | `client/buildozer.spec` | `client/mobile/recetario_app.py` | Sí (Release pública) |
| Gestor de Recetas | `manager/buildozer.spec` | `manager/mobile/gestor_app.py` | No (uso privado) |

Buildozer sólo funciona en Linux. En Windows se usa **WSL** (Ubuntu 22.04).

## Pasos (Windows + WSL)

**1. Preparar las apps** (PowerShell, en la raíz del repo):
```powershell
.\venvArguinyano\Scripts\python.exe tools\stage_android.py        # o: ... client / ... manager
```
Crea `build/android/client` y `build/android/manager` con `main.py`, los módulos de `shared/`, los iconos y el `buildozer.spec`.

**2. Compilar** (terminal de WSL):
```bash
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client
bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" manager
```
El script compila en `~/cocina_build/<app>` (en el disco de Linux, mucho más rápido), guarda el log en `~/cocina_build/<app>.log` y copia el APK a `apk/` en el repo.

- Primera compilación: 25-40 min (descarga el SDK/NDK y compila Python). Las siguientes, pocos minutos.
- **Instalar en el móvil:** copia el `.apk` al teléfono y ábrelo (permite «instalar apps desconocidas»), o usa `adb install -r apk/<archivo>.apk`.

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

## Notas

- **Permisos:** sólo `INTERNET`. Para exportar se usa el menú **Compartir** de Android, sin escribir archivos.
- **HTTPS:** se incluye `certifi`.
- **Iconos:** si cambias los logos de `shared/assets/`, regenera los PNG con `python tools/make_icons.py`.
- **GitHub Actions:** los workflows `Recetario APK` y `Gestor APK` hacen lo mismo en la nube, pero necesitan que la cuenta no tenga Actions bloqueado por facturación.
- **Release firmada (Google Play):** `buildozer android release`; la primera vez pide crear un *keystore*.
