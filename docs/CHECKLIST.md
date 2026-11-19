# Checklist del proyecto

Objetivo: **Recetario** público (descarga libre) y **Gestor de Recetas** bloqueado para el administrador, con APK y versión de escritorio de cada uno.

Leyenda: `[x]` hecho y probado · `[~]` hecho, falta probar en el móvil · `[ ]` pendiente

## Estructura y limpieza
- [x] Proyecto dividido en `client/` (público), `manager/` (privado) y `shared/` (código, logos y BD comunes).
- [x] Eliminado lo que no servía: builds antiguos (`build/`, `dist/`, `bin/`, `.buildozer/`), `.exe` desactualizados, prototipo pandas/Excel, script de migración, Excel original, `RESUME.md`, cachés.
- [x] Docs reorganizadas: `README.md` + `docs/ANDROID.md` + este checklist.
- [x] Workflows separados: `client.yml` (tests + APK + Release al etiquetar) y `manager.yml` (sólo manual, sin publicar).
- [x] Specs de PyInstaller versionados (`client/desktop/recetario.spec`, `manager/desktop/gestor.spec`).

## Compilación Android
- [x] Los dos APK compilan en local (WSL): Python 3.11.9, solo arm64-v8a, `PIP_NO_BINARY` para charset-normalizer/chardet. Ver la tabla de problemas en `docs/ANDROID.md`.
- [x] `tools/stage_android.py` + `tools/wsl_build.sh` (deja los APK en `apk/`).
- [ ] GitHub Actions: la cuenta tiene Actions **bloqueado por facturación**. Mientras siga así, se compila en local.

## Recetario (client)
- [x] Planificar → Mi menú (Platos / Compra) → Receta → Recetario con buscador; cambiar un plato; lista de la compra marcable y persistente.
- [x] Funciona sin conexión (caché + copia de la BD incluida en el APK).
- [~] Compartir con el menú nativo de Android (Intent).
- [x] Escritorio: un mismo menú para Recetas y Compra; PDF en `Documentos\Cocina Rápida`.

## Gestor (manager)
- [x] **Pantalla de bloqueo:** sólo entra un token cuyo usuario tenga permiso de escritura sobre `BaseDatosRecetas`, comprobado en cada arranque; «Salir» borra el token.
- [x] Guardado seguro: no guarda sin BD cargada; usa `sha` (no pisa cambios ajenos); si falla, no cambia nada.
- [x] Validación (nombre, página, cantidades, duplicados); permite mover una receta de categoría; pide confirmación al borrar.
- [~] Probar en el móvil con un token real: entrar, añadir una receta de prueba y comprobar el commit en `BaseDatosRecetas`.
- [x] Escritorio: escritura atómica; no pisa la receta equivocada tras editar.

## Datos
- [ ] **Ninguna receta está marcada como vegetariana o sin gluten** (tampoco lo estaba en el Excel original). Hay que marcarlas con el Gestor; hasta entonces esos filtros devuelven 0 recetas.

## Pendiente
- [ ] Probar ambos APK en un móvil real (los puntos `[~]`).
- [ ] Generar los `.exe` con PyInstaller y publicarlos (Release) si se quieren distribuir.
- [ ] Publicar el APK del Recetario como Release cuando Actions funcione (o subirlo a mano en GitHub → Releases).
