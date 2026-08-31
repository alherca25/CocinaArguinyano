# Resumen del Proyecto: CocinaArguinyano

Este documento proporciona un resumen detallado de la arquitectura, componentes y estado actual del repositorio de **Cocina Rápida**, basado en el análisis de los archivos del directorio de trabajo.

## 🎯 Objetivo General
Cocina Rápida es un sistema multiplataforma enfocado a automatizar la planificación de menús semanales y generar listas de la compra. Recientemente, se ha expandido para incluir la gestión remota e interactiva de las recetas, con una base de datos 100% en formato JSON.

### ⚙️ Flujo de Funcionamiento de la App (Generación de Menús)
1. **Carga y Sincronización:** Al iniciarse, la app intenta descargar la base de datos de recetas (`CocinaArguinyano.json`) más reciente desde GitHub. Si no hay conexión a internet, utiliza una copia persistente guardada en la caché local del dispositivo.
2. **Selección Inteligente:** El usuario especifica el número de recetas que desea cocinar esa semana y los filtros aplicables (por ejemplo, dietas vegetarianas o sin gluten). El algoritmo rastrea la base de datos y selecciona al azar platos únicos que cumplen con esos requisitos. Si hay menos recetas disponibles que las solicitadas, el sistema se ajusta al máximo posible y avisa al usuario.
3. **Generación de la Lista de la Compra:** Una vez establecidos los menús, la app analiza todos los ingredientes necesarios. Identifica ingredientes repetidos entre distintos platos, unifica sus unidades de medida (p. ej., gramos o unidades) y suma las cantidades automáticamente.
4. **Exportación:** Por último, presenta el listado final agrupado de la compra en la pantalla y, en la versión de escritorio, permite exportarlo directamente a formato PDF.

---

## 🏗️ Arquitectura de Software

El proyecto se divide principalmente en dos ecosistemas (Móvil y Escritorio) que interactúan con una base de datos centralizada.

### 📱 Ecosistema Móvil (Android / Kivy)
Aplicaciones diseñadas para uso táctil y portabilidad, compiladas a formato APK mediante Buildozer y GitHub Actions.

- **`src/MvInterface.py`**: Interfaz móvil para consultar recetas, generar menús aleatorios, aplicar filtros dietéticos y crear listas de la compra.
- **`src/MvRecipeManager.py`**: Gestor de recetas privado para Android. Incluye integración nativa con la API de GitHub mediante un *Token Personal*, permitiendo añadir, modificar o borrar recetas en la nube sin necesidad de PC.
- **`src/main.py`**: Punto de entrada utilizado por Buildozer para levantar la aplicación móvil.

### 💻 Ecosistema de Escritorio (Windows / Tkinter)
Aplicaciones diseñadas para su uso local en PC, compiladas a `.exe` mediante PyInstaller.

- **`src/PyInterface.py`**: Versión original de escritorio (Tkinter) para planificar los menús de la semana y exportar los resultados a PDF.
- **`src/RecipeManager.py`**: Herramienta de escritorio moderna (construida con `customtkinter`) que sirve para añadir o editar las recetas de la base de datos de manera intuitiva y con interfaz oscura (Dark Mode).

### ⚙️ Lógica y Utilidades
- **`src/functions.py`**: Archivo núcleo que contiene toda la lógica reutilizable de las aplicaciones (descarga del JSON, lectura/escritura de caché local, agrupación de ingredientes, etc.).
- **`src/migrate_excel_to_json.py`**: Script *legacy* utilizado para realizar la transición de la antigua base de datos en Excel `.xlsx` al moderno formato JSON.

---

## 🗄️ Base de Datos

- **`BaseDatosRecetas/CocinaArguinyano.json`**: (Repositorio secundario / Servidor). Contiene el catálogo completo de platos. Al estar separado en su propio repositorio o ruta, permite que la aplicación de interfaz (pública) lea los datos, pero asegura que solo el gestor de recetas con credenciales pueda modificarlos.

---

## 🚀 Integración Continua y Despliegue (CI/CD)

El proyecto cuenta con compilación automatizada en la nube a través de **GitHub Actions**.

- **`.github/workflows/build-android.yml`**: Define un *workflow* que instala Buildozer directamente sobre Ubuntu-22.04 para evitar conflictos de sistema. Genera dos *jobs* paralelos (`build-interface` y `build-manager`) para crear las dos APKs independientes cada vez que se hace un *push*.
- **`buildozer_interface.spec`**: Configuración de compilación para la app de recetario.
- **`buildozer_manager.spec`**: Configuración de compilación para la app de gestión privada.

---

## 📂 Otros Archivos Clave
- **`README.md` & `README_android.md`**: Documentación principal del proyecto y guía de instalación/compilación.
- **`Requirements.txt`**: Listado de dependencias de Python (kivy, fpdf2, customtkinter, requests, etc.) para instalar en un entorno local.
- **`.gitignore`**: Excluye cachés, entornos virtuales (`venvArguinyano`) y ejecutables temporales para mantener el repositorio limpio.
