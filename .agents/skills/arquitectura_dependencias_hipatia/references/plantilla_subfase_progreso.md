# Plantilla — subfase o lote en PROGRESO_OPTIMIZACION_CAPAS.md

Usar bajo la sección **Sub-ítems y lotes** de la fase correspondiente (sobre todo **Opt-4**).

## Fila de tabla (Opt-4)

```markdown
| nombre_corto | pendiente | `controllers.foo` → diálogo X | — | Elegido de architecture_layer_edges.md línea … |
```

Al completar:

```markdown
| nombre_corto | completada | `controllers.foo` → diálogo X | ITEM NNN | … |
```

## Bloque de historial

Añadir en **Historial breve de cambios de estado**:

```markdown
| YYYY-MM-DD | Opt-N | Opt-N sub-ítem «nombre» → completada; REGISTRO ITEM NNN |
```

## Al marcar una fase entera completada

1. Tabla principal: columna **Estado** → `completada`.
2. **ultima_actualizacion** y **proxima_accion_sugerida** en cabecera (siguiente fase `pendiente`).
3. Regenerar `architecture_layer_edges` y comprobar el **criterio de hecho** de esa fase.
