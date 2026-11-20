# Checklist del proyecto

Objetivo: **Recetario** público (descarga libre) y **Gestor de Recetas** bloqueado para el administrador, con APK y versión de escritorio de cada uno.

Leyenda: `[x]` hecho y probado · `[ ]` pendiente

## Estructura y limpieza
- [x] Proyecto dividido en `client/` (público), `manager/` (privado) y `shared/` (código, logos y BD comunes).
- [x] Eliminado lo que no servía: builds antiguos (`build/`, `dist/`, `bin/`, `.buildozer/`), `.exe` desactualizados, prototipo pandas/Excel, script de migración, Excel original, `RESUME.md`, cachés.
- [x] Docs reorganizadas: `README.md` (formato estándar de GitHub, con capturas en `docs/screenshots/`) + `docs/ANDROID.md` + este checklist.
- [x] Workflows separados: `client.yml` (tests + APK + Release al etiquetar) y `manager.yml` (sólo manual, sin publicar).
- [x] Specs de PyInstaller versionados (`client/desktop/recetario.spec`, `manager/desktop/gestor.spec`).

## Compilación Android
- [x] Los dos APK compilan en local (WSL): Python 3.11.9, solo arm64-v8a, `PIP_NO_BINARY` para charset-normalizer/chardet. Ver la tabla de problemas en `docs/ANDROID.md`.
- [x] `tools/stage_android.py` + `tools/wsl_build.sh` (deja los APK en `apk/`).
- [ ] GitHub Actions: la cuenta tiene Actions **bloqueado por facturación**. Mientras siga así, se compila en local.

## Recetario (client)
- [x] Planificar → Mi menú (Platos / Compra) → Receta → Recetario con buscador; cambiar un plato; lista de la compra marcable y persistente.
- [x] Funciona sin conexión (caché + copia de la BD incluida en el APK).
- [x] Compartir con el menú nativo de Android (Intent).
- [x] Escritorio: un mismo menú para Recetas y Compra; PDF en `Documentos\Cocina Rápida`.

## Gestor (manager)
- [x] **Pantalla de bloqueo:** sólo entra un token cuyo usuario tenga permiso de escritura sobre `BaseDatosRecetas`, comprobado en cada arranque; «Salir» borra el token.
- [x] Guardado seguro: no guarda sin BD cargada; usa `sha` (no pisa cambios ajenos); si falla, no cambia nada.
- [x] Validación (nombre, página, cantidades, duplicados); permite mover una receta de categoría; pide confirmación al borrar.
- [x] Probado en el móvil con un token real.
- [x] Escritorio: escritura atómica; no pisa la receta equivocada tras editar.

## Datos
- [x] Filtros vegetariano / sin gluten marcados en las 95 recetas originales según sus ingredientes (criterio en el README de `BaseDatosRecetas`).
- [x] 31 recetas nuevas (sin página: no son del libro). Total: 126 recetas, 43 vegetarianas, 59 sin gluten.
- [x] Copia offline `shared/data/CocinaArguinyano.json` sincronizada con la BD.

## Pendiente
- [x] Probar ambos APK en un móvil real: instalados y funcionando.
- [ ] Generar los `.exe` con PyInstaller y publicarlos (Release) si se quieren distribuir.
- [ ] Publicar el APK del Recetario como Release cuando Actions funcione (o subirlo a mano en GitHub → Releases).
