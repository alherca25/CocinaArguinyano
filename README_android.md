# 📱 Guía de compilación Android — Cocina Rápida

## Archivos generados

| Archivo | Propósito |
|---|---|
| `MvInterface.py` | Toda la lógica e interfaz Kivy (ya existía) |
| `main.py` | Punto de entrada requerido por Buildozer |
| `buildozer.spec` | Configuración del build Android |
| `logo.png` | Icono de la app (ya existía) |

---

## ⚠️ Requisito previo: Linux o WSL

**Buildozer solo compila en Linux.** En Windows debes usar:
- **WSL 2** (Windows Subsystem for Linux) con Ubuntu 22.04 → opción recomendada
- Máquina virtual Linux
- CI/CD (GitHub Actions)

---

## 1. Instalar dependencias del sistema (Ubuntu/WSL)

```bash
sudo apt update && sudo apt install -y \
    git zip unzip python3-pip \
    build-essential libssl-dev libffi-dev \
    python3-dev libltdl-dev \
    autoconf libtool pkg-config \
    openjdk-17-jdk
```

## 2. Instalar Buildozer y Kivy

```bash
pip3 install --upgrade buildozer cython virtualenv
```

## 3. Copiar el proyecto a Linux

Desde PowerShell (Windows), copia el repositorio a WSL:

```powershell
# Ejemplo: copiar a tu home de WSL
wsl cp -r "D:\Proyectos\Repositorios\CocinaArguinyano" ~/CocinaArguinyano
```

O simplemente clona desde GitHub si tienes el repo subido.

## 4. Compilar el APK (modo debug)

```bash
cd ~/CocinaArguinyano
buildozer android debug
```

> La primera compilación tarda **20–40 minutos** porque descarga el Android SDK, NDK y compila todas las dependencias Python para ARM.

El APK resultante estará en:
```
~/CocinaArguinyano/bin/cocinarapida-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

## 5. Instalar en el dispositivo

Con el dispositivo Android conectado por USB (modo depuración USB activado):

```bash
buildozer android deploy run
```

O manualmente:
```bash
adb install bin/cocinarapida-*.apk
```

---

## 🚀 Build de producción (Release)

Para generar un APK firmado listo para Google Play:

```bash
buildozer android release
```

Necesitarás un keystore. Buildozer te pedirá los datos la primera vez.

---

## 🐛 Ver logs en tiempo real

```bash
buildozer android logcat | grep python
```

---

## ❓ Preguntas frecuentes

**¿Por qué no funciona `reportlab`?**  
`reportlab` no tiene soporte para python-for-android. `MvInterface.py` ya usa `fpdf2`, que sí es compatible.

**¿Los PDFs dónde se guardan en Android?**  
En la carpeta `Descargas/` del almacenamiento externo del dispositivo (`/storage/emulated/0/Download/`).

**¿Necesita internet?**  
Sí, la app descarga el Excel desde GitHub al arrancar. Se requiere conexión en el primer uso.
