#!/bin/bash
# Crea (una sola vez) la clave con la que se firman los APK «release» de una app.
#
# Uso (desde WSL):  bash "/mnt/c/Disco D/GitHub/CocinaArguinyano/tools/create_keystore.sh" client
#
# IMPORTANTE: Android sólo instala una actualización si está firmada con la MISMA clave
# que la app instalada. Si pierdes la clave o su contraseña, los usuarios tendrán que
# desinstalar la app para instalar versiones nuevas. Guarda la copia de seguridad.
#
# Deja:
#   ~/.cocina_keys/<app>.jks   la clave (válida 30 años)
#   ~/.cocina_keys/<app>.env   rutas y contraseña para wsl_build.sh (sólo legible por ti)
#   C:\Users\<tú>\CocinaRapida-claves\   copia de seguridad de ambos archivos
set -e
APP="${1:?Uso: create_keystore.sh client|manager}"
DIR="$HOME/.cocina_keys"
KS="$DIR/$APP.jks"
ENV="$DIR/$APP.env"
ALIAS="cocinarapida-$APP"

if [ -f "$KS" ]; then
  echo "Ya existe $KS. No se sobrescribe (cambiar la clave rompería las actualizaciones)." >&2
  exit 1
fi
command -v keytool >/dev/null || { echo "Falta keytool: sudo apt install -y openjdk-17-jdk" >&2; exit 1; }

mkdir -p "$DIR"
chmod 700 "$DIR"
while true; do
  read -r -s -p "Contraseña para la clave (mínimo 6 caracteres): " PW; echo
  read -r -s -p "Repítela: " PW2; echo
  [ "$PW" = "$PW2" ] && [ ${#PW} -ge 6 ] && [[ "$PW" != *"'"* ]] && break
  echo "No coinciden, es demasiado corta o lleva comillas simples ('). Otra vez."
done

keytool -genkeypair -keystore "$KS" -storetype PKCS12 -alias "$ALIAS" \
  -keyalg RSA -keysize 4096 -validity 10950 \
  -storepass "$PW" -keypass "$PW" -dname "CN=Cocina Rapida, O=alherca25, C=ES"

umask 077
cat > "$ENV" <<EOF
P4A_RELEASE_KEYSTORE='$KS'
P4A_RELEASE_KEYALIAS='$ALIAS'
P4A_RELEASE_KEYSTORE_PASSWD='$PW'
P4A_RELEASE_KEYALIAS_PASSWD='$PW'
EOF
chmod 600 "$KS" "$ENV"
unset PW PW2

# Copia de seguridad fuera de WSL y fuera del repositorio.
WINUSER="$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')"
if [ -n "$WINUSER" ] && [ -d "/mnt/c/Users/$WINUSER" ]; then
  BACKUP="/mnt/c/Users/$WINUSER/CocinaRapida-claves"
  mkdir -p "$BACKUP"
  cp "$KS" "$ENV" "$BACKUP/"
  echo "Copia de seguridad: C:\\Users\\$WINUSER\\CocinaRapida-claves\\"
fi
echo "Clave creada: $KS"
echo "Guarda la copia de seguridad en un sitio seguro (USB, gestor de contraseñas...). No la subas a GitHub."
