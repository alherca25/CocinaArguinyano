# 📱 Compilar los APK — Cocina Rápida

Hay dos APK, cada uno con su archivo de configuración:

| App | Spec | Código | Icono |
|---|---|---|---|
| Recetario (usuarios) | `buildozer_interface.spec` | `src/MvInterface.py` | `assets/icon_main.png` |
| Gestor de Recetas (admin) | `buildozer_manager.spec` | `src/MvRecipeManager.py` | `assets/icon_edit.png` |

Buildozer necesita una carpeta con un `main.py` y todos sus módulos. `tools/stage_android.py` la prepara en `android_build/<app>/` (esa carpeta está en `.gitignore`).

## Opción 1: GitHub Actions (recomendada)

Haz *push* a `main` o `_dev`, o lanza el workflow a mano (*Actions → Build Android APKs → Run workflow*). Al terminar, descarga los artefactos `Recetario_APK` y `GestorRecetas_APK`.

## Opción 2: en local (Linux o WSL con Ubuntu 22.04)

```bash
sudo apt update && sudo apt install -y build-essential git zip unzip autoconf automake libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev \
    libssl-dev libltdl-dev python3-pip python3-venv openjdk-17-jdk
# Buildozer con --user (NO en un virtualenv: buildozer usa «pip --user» internamente)
python3 -m pip install --user --upgrade Cython buildozer "virtualenv==20.21.0" setuptools

# PATH sin rutas de Windows (en WSL tienen espacios y rompen la compilación)
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

python3 tools/stage_android.py interface      # o: manager
# Compilar fuera de /mnt/c (mucho más rápido y sin problemas de permisos)
mkdir -p ~/cocina_build && cp -r android_build/interface ~/cocina_build/
cd ~/cocina_build/interface
buildozer -v android debug
```

En WSL además hace falta internet: si no hay conexión, añade `networkingMode=mirrored` en `%USERPROFILE%\.wslconfig` (sección `[wsl2]`) y ejecuta `wsl --shutdown`.

La primera compilación tarda entre 20 y 40 minutos (descarga el SDK/NDK). El APK queda en `android_build/<app>/bin/`.

Instalar en el móvil (con la depuración USB activada): `adb install -r bin/*.apk`
Ver los logs: `adb logcat | grep python`

## Notas

- **Python fijado a 3.11** en los `.spec`. Con 3.14, python-for-android intenta instalar wheels Android de PyPI (p. ej. `charset_normalizer`) y la compilación falla con *"is not a supported wheel on this platform"*.
- **Permisos**: solo `INTERNET`. Para exportar no se escriben archivos: la app usa el menú **Compartir** de Android (WhatsApp, Keep, correo...).
- **HTTPS**: se incluye `certifi` para que las descargas no fallen por certificados.
- **Iconos**: si cambias los logos de `assets/`, regenera los PNG con `python tools/make_icons.py`.
- **Release firmada** (Google Play): `buildozer android release`; la primera vez pide crear un *keystore*.
