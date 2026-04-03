# Rubrica de priorizacion

## Orden de prioridad

1. **P0 Arquitectura runtime**
   - Shims/bridges activos en ejecucion.
   - Ciclos de dependencia entre controladores nucleares.
2. **P1 Frontera UI/DTO**
   - Accesos por `dict`/`vars().get()` en UI para datos de dominio.
3. **P2 Tipado estricto**
   - Archivos con baja cobertura de anotaciones y alta centralidad.
4. **P3 Legacy puntual**
   - `print` en produccion, `bare except`, marcadores legacy sin plan.

## Criterio de desempate

1. Mayor riesgo en runtime.
2. Menor alcance de cambio para cerrar rapido y seguro.
3. Mejor disponibilidad de tests focales existentes.
