#!/bin/bash
# Compila un APK en Linux/WSL (Ubuntu-22.04).
#
# Uso (desde WSL):
#   bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client release   # Recetario para publicar
#   bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" client           # Recetario de pruebas (debug)
#   bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/wsl_build.sh" manager          # Gestor (debug)
#
# Antes, en Windows:  python tools/stage_android.py
# «release» firma con la clave de ~/.cocina_keys/<app>.env (crearla una vez con
# tools/create_keystore.sh). El APK se copia a <repo>/apk/ y el log queda en ~/cocina_build/<app>.log
set -o pipefail
APP="${1:?Uso: wsl_build.sh client|manager [debug|release]}"
MODE="${2:-debug}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/build/android/$APP"
DST="$HOME/cocina_build/$APP"

if [ ! -f "$SRC/main.py" ]; then
  echo "No existe $SRC. Ejecuta antes en Windows: python tools/stage_android.py $APP" >&2
  exit 1
fi
if [ "$MODE" != "debug" ] && [ "$MODE" != "release" ]; then
  echo "Modo desconocido: $MODE (usa debug o release)" >&2
  exit 1
fi
if [ "$MODE" = "release" ]; then
  KEYS="$HOME/.cocina_keys/$APP.env"
  if [ ! -f "$KEYS" ]; then
    echo "Falta la clave de firma ($KEYS). Créala una vez con:" >&2
    echo "  bash \"$REPO/tools/create_keystore.sh\" $APP" >&2
    exit 1
  fi
  # Exporta P4A_RELEASE_KEYSTORE, _KEYSTORE_PASSWD, _KEYALIAS y _KEYALIAS_PASSWD.
  # shellcheck disable=SC1090
  set -a; . "$KEYS"; set +a
fi

# Se compila en el disco de Linux (mucho más rápido que /mnt/c), conservando la caché.
mkdir -p "$DST"
find "$DST" -mindepth 1 -maxdepth 1 ! -name .buildozer ! -name bin -exec rm -rf {} +
rm -f "$DST"/bin/*.apk
cp -r "$SRC"/. "$DST"/
cd "$DST" || exit 1

# PATH sin rutas de Windows: tienen espacios y rompen las herramientas de compilación.
export PATH="$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
# Versiones Python puras: las wheels compiladas de estos paquetes son para PC (x86_64).
export PIP_NO_BINARY="charset-normalizer,chardet"

buildozer -v android "$MODE" 2>&1 | tee "$HOME/cocina_build/$APP.log"
RC=$?
if [ $RC -eq 0 ] && ls "$DST"/bin/*.apk >/dev/null 2>&1; then
  mkdir -p "$REPO/apk"
  cp "$DST"/bin/*.apk "$REPO/apk/"
  echo "APK copiado a: $REPO/apk/"
  ls -la "$REPO/apk/"
else
  [ $RC -eq 0 ] && RC=1
  echo "La compilación falló (código $RC). Log: ~/cocina_build/$APP.log"
fi
exit $RC
