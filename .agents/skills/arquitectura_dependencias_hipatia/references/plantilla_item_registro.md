# Plantilla — ítem REGISTRO (arquitectura / dependencias)

Copiar y adaptar en `Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md`.

```markdown
## ITEM XXX — [Título breve: p. ej. Quitar core→ui en qr_scanner]

- **Estado:** Completado | En progreso
- **Prioridad:** P0 | P1 | P2
- **Alcance:** rutas de archivo y regla de capa (`core`→`ui`, `ui`→`database`, etc.).
- **Cambio:** qué se movió (interfaz, DTO, delegación en controller).
- **Gates:** pytest focal; mypy; si ui: `ui_dto_boundary_analyzer` → 0; docs si aplica.
- **Informe:** `python3 scripts/architecture_layer_edges.py` (antes/después opcional).
- **Sync iCloud:** OK / N/A
- **Fecha cierre:** YYYY-MM-DD
```
