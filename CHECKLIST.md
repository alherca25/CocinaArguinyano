# Checklist de correcciones y rediseño

Objetivo final: **dos APK**:
- **Recetario** (`MvInterface.py`): para los usuarios. Planifican el menú, consultan las recetas y la lista de la compra.
- **Gestor de Recetas** (`MvRecipeManager.py`): para el administrador. Añade, edita y borra recetas en `alherca25/BaseDatosRecetas`.

Leyenda: `[ ]` pendiente · `[x]` hecho y probado en escritorio · `[~]` hecho, pero sin verificar en Android/CI

## A. Compilación Android (bloqueante)

- [~] A1. **El CI fallaba en todas las ejecuciones** (las 5 últimas de `_dev`). python-for-android compilaba con Python 3.14 e intentaba instalar `charset_normalizer-…-cp314-android_24_arm64_v8a.whl`, y pip la rechazaba. → Python fijado a 3.11.9 en los `.spec`. *Hay que verificarlo con un push.*
- [x] A2. **El APK del Recetario habría fallado al arrancar.** El CI copiaba `MvInterface.py` a la raíz, pero `functions.py` se quedaba en `src/`. → `tools/stage_android.py` monta `android_build/<app>/` con todo lo necesario (comprobado: las dos apps importan bien y el Recetario carga la copia incluida sin conexión).
- [x] A3. Iconos y pantalla de carga generados a partir de los logos (`assets/icon_*.png`, `assets/presplash_*.png`, `tools/make_icons.py`) y declarados en los `.spec`.
- [x] A4. Permisos reducidos a `INTERNET`.
- [x] A5. HTTPS con `certifi` y timeout de 20 s.
- [ ] A6. Compilación local en WSL: **no es posible en este equipo** (WSL Ubuntu 22.04 no tiene salida a internet). Se verificará en GitHub Actions.
- [~] A7. Workflow nuevo: job de tests, matriz con las dos apps, staging y caché de `~/.buildozer`.

## B. Recetario móvil (`MvInterface.py`)

- [x] B1. **Compartir no funcionaba:** `plyer` 2.1 no tiene `share`, así que los TXT se quedaban en la carpeta privada de la app. → Menú nativo «Compartir» de Android mediante `Intent` (pyjnius); en escritorio se copia al portapapeles. *[~] Falta probarlo en el móvil.*
- [x] B2. Recetas y lista de la compra visibles dentro de la app (pantallas Mi menú → Platos / Compra, y Receta).
- [x] B3. Lista de la compra con casillas: lo marcado se tacha, baja al final y se recuerda.
- [x] B4. El último menú se guarda (`estado.json`) y se puede abrir sin conexión.
- [x] B5. Al cambiar el filtro se ajustan las cantidades al máximo disponible y se avisa.
- [x] B6. Rediseño: paleta de los logos, cabecera con logo, selector −/+ por categoría, filtros tipo chip, botón «Cambiar» plato, buscador «Recetario» por nombre o ingrediente, botón atrás de Android.
- [x] B7. Eliminadas las referencias a «PDF» en móvil.

## C. Gestor móvil (`MvRecipeManager.py`)

- [x] C1. **Riesgo de borrar la BD:** si fallaba la descarga, guardaba una BD vacía. → No se puede guardar hasta haber cargado la BD (test incluido).
- [x] C2. **Filtros guardados con formato incorrecto** (`vegetariano` en la raíz en vez de `filtros`). → Formato correcto, y lectura compatible con el antiguo.
- [x] C3. Guardado con el `sha` cargado: si hubo cambios en GitHub se pide recargar (test incluido).
- [x] C4. Si la subida falla, la BD en memoria no cambia (test incluido).
- [x] C5. Red en segundo plano con indicador «Conectando con GitHub…».
- [x] C6. Confirmación antes de eliminar y antes de limpiar el formulario.
- [x] C7. El token se guarda al pulsar «Guardar», en la carpeta privada de la app; `token.txt` añadido a `.gitignore`.
- [x] C8. Al editar se puede cambiar la categoría (mueve la receta).
- [x] C9. Validación: nombre obligatorio, página numérica, cantidades numéricas (acepta coma), sin nombres repetidos en la categoría; las unidades se eligen pulsando (uds/g/mL/cuch).
- [x] C10. Rediseño con el logo `edit_logo` y buscador de recetas para editar.

## D. Código compartido (`functions.py`)

- [x] D1. La agregación de ingredientes está unificada (antes duplicada); ingredientes con texto no numérico ya no se pierden.
- [x] D2. Páginas y cantidades «185.0» se muestran como «185».
- [x] D3. Descarga con caché y respaldo, API de GitHub (leer/guardar con `sha`), textos para compartir.
- [x] D4. `tests/test_logic.py`: 14 tests (lógica + gestor con GitHub simulado). Todos pasan.

## E. Escritorio

- [x] E1. `PyInterface.py` rediseñado (mismo esquema que el móvil). **Bug corregido:** «Recetas» y «Compra» por separado elegían menús aleatorios distintos; ahora usan el mismo menú. PDF en `Documentos\Cocina Rápida` y se abren solos; si no hay Calibri se usa Helvetica (antes fallaba). Eliminado el respaldo a la rama `_dev` inexistente.
- [x] E2. `RecipeManager.py`: tema y logo nuevos. **Bug corregido:** tras guardar una edición se quedaba cargada la primera receta de la categoría y el siguiente guardado pisaba la receta equivocada. Además: escritura atómica, no se guarda si el JSON no se pudo leer, se deshace el cambio si falla el guardado, validación y control de nombres repetidos.
- [x] E3. `requirements_desktop.txt` (añade pillow y certifi) y nuevo `requirements_mobile.txt`.

## F. Repositorio y documentación

- [x] F1. `.gitignore` limpio (`android_build/`, `token.txt`, excepción `!buildozer_*.spec`; quitado `RecipeManager.py`).
- [ ] F2. `dist/PyInterface.exe` (25 MB) sigue versionado. **Decisión tuya:** sacarlo del repo y publicarlo como *Release*. Además el .exe está desactualizado: hay que regenerarlo con PyInstaller.
- [x] F3. README, README_android y RESUME reescritos (RESUME tenía la codificación rota).
- [x] F4. Prototipo pandas/Excel y script de migración movidos a `legacy/`.

## G. Datos y verificación pendientes

- [ ] G1. **Ninguna receta está marcada como vegetariana o sin gluten** (tampoco en el Excel original: todo 0). Los filtros funcionan, pero devuelven 0 recetas hasta que se marquen con el Gestor.
- [ ] G2. Push para que GitHub Actions compile los APK (A1/A7). **Pendiente de tu autorización.**
- [ ] G3. Probar los dos APK en un móvil real: instalación, descarga, Compartir, guardar en GitHub con token.
- [ ] G4. Regenerar los `.exe` de escritorio con PyInstaller.
