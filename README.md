# 🍳 Cocina Rápida — Planificador de Recetas y Generador de Listas de Compra

**Cocina Rápida** es una solución interactiva multiplataforma (escritorio y móvil) diseñada para automatizar la planificación semanal de menús y la gestión de compras a partir de un recetario en formato JSON.

La herramienta selecciona platos de forma aleatoria a partir de una base de datos local o en red (organizada por categorías y etiquetas dietéticas), valida el inventario real de recetas, agrupa los ingredientes duplicados sumando sus cantidades, y exporta listas de cocina y de compra en formato **PDF**.

---

## ✨ Características Principales

*   **Migración a formato JSON y Ligereza**: La base de datos de recetas se gestiona ahora de manera íntegra en formato `.json` ([CocinaArguinyano.json](CocinaArguinyano.json)), sustituyendo a las hojas de Excel. Esto ha permitido eliminar la dependencia de librerías pesadas como `pandas` y `openpyxl`, haciendo la aplicación móvil dramáticamente más ligera y rápida de compilar/iniciar.
*   **Sincronización Dinámica y Caché Offline Persistente**: Al iniciar, las aplicaciones descargan la base de datos de recetas actualizada desde GitHub y guardan una copia local en la caché del dispositivo (directorio de usuario). Si inicias la app sin internet, recurrirá automáticamente a esta caché.
*   **Algoritmo de Selección Inteligente**:
    *   Selección aleatoria sin repetición de platos por categoría.
    *   Filtros dietéticos dinámicos (*Vegetariano*, *Gluten Free*).
    *   **Ajuste automático de límites**: Si se solicitan más platos de los existentes en una categoría con los filtros seleccionados, el sistema limita automáticamente la cantidad devuelta al máximo disponible y notifica al usuario.
*   **Consolidación de Lista de la Compra**: Agrupa ingredientes idénticos utilizados en diferentes recetas, sumando sus cantidades y normalizando las unidades de medida (p. ej., gramos, unidades, chorros) para generar una lista de la compra compacta y eficiente.
*   **Diseño Multiplataforma Integrado**:
    *   🖥️ **Escritorio (Tkinter)**: Interfaz clásica para interactuar y exportar listados de compra (`PyInterface.py`).
    *   📱 **Móvil (Kivy/Android)**: Interfaz táctil, responsiva y adaptable, lista para empaquetarse (`MvInterface.py`).
    *   📝 **Gestor de Recetas (CustomTkinter)**: Aplicación con estética premium y modo oscuro para la inserción y modificación automatizada y sin código de nuevas recetas en la base de datos JSON (`RecipeManager.py`).

---

## 📂 Estructura del Proyecto

*   **`main.py`**: Punto de entrada de la aplicación móvil (requerido para la compilación de Buildozer).
*   **`MvInterface.py`**: Interfaz de Kivy y motor lógico principal para Android. Emplea la librería `fpdf2` para generar PDFs de forma nativa.
*   **`PyInterface.py`**: Interfaz de escritorio desarrollada en Tkinter clásico. Emplea `reportlab` para la renderización de PDFs de compra y menús.
*   **`RecipeManager.py`**: Interfaz de escritorio desarrollada en `customtkinter`. Se utiliza para añadir nuevas recetas a la base de datos JSON y editar las ya existentes mediante una interfaz amigable.
*   **`functions.py`**: Módulo compartido que abstrae la lógica común (descarga de red, gestión de caché, validación de filtros, suma de ingredientes).
*   **`buildozer.spec`**: Archivo de especificaciones y dependencias para compilar la aplicación móvil a un paquete APK de Android.
*   **`CocinaArguinyano.json`**: Base de datos troncal de todas las recetas en formato ligero.
*   **`migrate_excel_to_json.py`**: Script de utilidad que permitió la transición inicial del viejo formato Excel al actual formato estructurado JSON.

---

## 🚀 Requisitos e Instalación

### 🖥️ Versiones de Escritorio (Gestor y Recetario)

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/alherca25/CocinaArguinyano.git
   cd CocinaArguinyano
   ```

2. **Instalar las dependencias**:
   ```bash
   pip install -r Requirements.txt
   ```
   *(Asegúrate de que incluya `customtkinter` y `reportlab`)*

3. **Ejecutar la Interfaz Clásica o el Gestor de Recetas**:
   ```bash
   python PyInterface.py
   # o
   python RecipeManager.py
   ```

### 📱 Versión Móvil (Prueba Local de Kivy)

Para probar la interfaz táctil directamente en tu ordenador:

1. **Instalar Kivy y librerías PDF**:
   ```bash
   pip install kivy==2.3.0 requests fpdf2
   ```

2. **Ejecutar la aplicación móvil**:
   ```bash
   python main.py
   ```

### 🤖 Compilación para Android (.APK)

Para compilar el archivo ejecutable de Android (`.apk`), consulta la [Guía de Compilación Android](README_android.md), que detalla el uso de **Buildozer** bajo Linux/WSL2. 

---

## 📊 Formato de la Base de Datos (JSON)

Al haber migrado a formato JSON, ya **no se recomienda editar el archivo a mano**. Para insertar nuevas recetas o rectificar cantidades e ingredientes de las ya existentes, utiliza la interfaz **`RecipeManager.py`**. 

El Gestor se encargará de mantener la integridad estructural del documento y guardarlo de forma local, listo para que hagas commit y actualices el repositorio de GitHub de forma segura.

---

## 📝 Licencia

Este proyecto está desarrollado para uso personal y educativo. Los contenidos de las recetas pertenecen a sus respectivos autores.
