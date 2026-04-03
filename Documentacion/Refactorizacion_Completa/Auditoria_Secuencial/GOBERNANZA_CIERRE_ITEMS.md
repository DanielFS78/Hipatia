# Gobernanza de Cierre y Paso al Siguiente Item

## Regla principal

No se habilita el siguiente item hasta cerrar completamente el item actual con todos los gates en verde y documentacion validada.

## Condiciones para marcar `Completado`

1. `pytest` focal en verde.
2. `mypy` focal en verde.
3. `mypy` global en verde.
4. `pytest` global en verde.
5. `python3 scripts/generate_daniel_doc.py` ejecutado sin error.
6. `python3 scripts/check_documentation_omissions.py` con `omitidos=0`.
7. Registro actualizado en `REGISTRO_EJECUCION_ITEMS.md`.

## Protocolo de avance

1. Cambiar estado del item actual a `Completado` en el registro.
2. Marcar resultado final (evidencias y fecha de cierre).
3. Seleccionar el siguiente item no completado del backlog (`PLAN_EJECUCION_UNO_A_UNO.md`).
4. Abrir nuevo bloque en `REGISTRO_EJECUCION_ITEMS.md` con estado `En progreso`.
5. Ejecutar baseline focal del nuevo item antes de cualquier refactor.

## Regla de bloqueo

Si un gate global falla despues de un cambio, el item queda en `En progreso` y no se puede pasar al siguiente hasta recuperar verde total.
