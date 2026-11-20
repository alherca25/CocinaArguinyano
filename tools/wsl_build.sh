#!/bin/bash
# Compila un APK en Linux/WSL.
#
# Uso (desde WSL):  bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client|manager
#
# Antes, en Windows:  python tools/stage_android.py
# El APK resultante se copia a <repo>/apk/ y el log queda en ~/cocina_build/<app>.log
set -o pipefail
APP="${1:?Uso: wsl_build.sh client|manager}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/build/android/$APP"
DST="$HOME/cocina_build/$APP"

if [ ! -f "$SRC/main.py" ]; then
  echo "No existe $SRC. Ejecuta antes en Windows: python tools/stage_android.py $APP" >&2
  exit 1
fi

# Se compila en el disco de Linux (mucho más rápido que /mnt/c), conservando la caché.
mkdir -p "$DST"
find "$DST" -mindepth 1 -maxdepth 1 ! -name .buildozer ! -name bin -exec rm -rf {} +
cp -r "$SRC"/. "$DST"/
cd "$DST" || exit 1

# PATH sin rutas de Windows: tienen espacios y rompen las herramientas de compilación.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# Versiones Python puras: las wheels compiladas de estos paquetes son para PC (x86_64).
export PIP_NO_BINARY="charset-normalizer,chardet"

buildozer -v android debug 2>&1 | tee "$HOME/cocina_build/$APP.log"
RC=$?
if [ $RC -eq 0 ]; then
  mkdir -p "$REPO/apk"
  cp "$DST"/bin/*.apk "$REPO/apk/"
  echo "APK copiado a: $REPO/apk/"
  ls -la "$REPO/apk/"
else
  echo "La compilación falló (código $RC). Log: ~/cocina_build/$APP.log"
fi
exit $RC
