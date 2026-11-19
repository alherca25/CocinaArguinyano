# Resumen del proyecto: Cocina Rápida

**Objetivo:** dos APK Android.
- **Recetario**: los usuarios planifican el menú semanal, consultan las recetas y tienen la lista de la compra.
- **Gestor de Recetas**: el administrador añade las recetas que piden los usuarios.

Las dos apps comparten la base de datos JSON del repositorio `alherca25/BaseDatosRecetas`.

## Flujo del Recetario
1. **Carga:** descarga el JSON de GitHub. Sin conexión, usa la última copia guardada o, si no la hay, la que va incluida en el APK.
2. **Planificar:** se elige un filtro (Todo / Vegetariano / Sin gluten) y cuántos platos de cada categoría. Cada categoría tiene un límite: las recetas que cumplen el filtro.
3. **Mi menú:** recetas al azar sin repetir; cualquier plato se puede cambiar por otro de su categoría.
4. **Compra:** los ingredientes se agrupan por nombre y unidad y se suman sus cantidades. La lista se puede ir marcando y se recuerda entre sesiones.
5. **Compartir:** el menú, una receta o la lista pendiente se envían como texto con el menú nativo de Android.

## Flujo del Gestor
1. Carga la BD con la API de GitHub y guarda su `sha`.
2. Añadir / editar (también se puede cambiar la categoría) / eliminar (pide confirmación).
3. Cada guardado se valida (nombre, cantidades numéricas, nombres repetidos) y se sube a GitHub como un *commit* que usa el `sha` cargado. Si hay un conflicto, la app pide recargar; si falla la subida, no se pierde nada.

## Piezas
- `src/functions.py`: lógica común, sin interfaz (cubierta por `tests/`).
- `src/mobile_ui.py` / `src/desktop_theme.py`: diseño compartido, con la paleta crema, marrón y terracota de los logos.
- `tools/stage_android.py` + `buildozer_*.spec` + `.github/workflows/build-android.yml`: compilación de los APK.

## Pendiente
Ver [CHECKLIST.md](CHECKLIST.md).
