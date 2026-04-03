---
name: Fase Monolitos — Autopilot
description: Agente autónomo para analizar y refactorizar archivos monolíticos. Usa `scripts/monolith_analyzer.py` para ordenar el trabajo y ejecuta un bucle determinista: seleccionar → refactor 2-3 archivos → tests → documentación → repetir.
---

# [ARCHIVO — no usar como backlog activo] Fase Monolitos — Autopilot (Hipatia)

## Objetivo

Reducir complejidad y acoplamiento de archivos monolíticos (LOC altos + alta centralidad en dependencias) sin romper la suite:

- **0 fallos / 0 warnings / 0 skipped** en el scope afectado.
- Cambios **pequeños y reversibles**: máximo **2–3 archivos de código base** por iteración.
- Mantener/incrementar claridad: módulos más pequeños, nombres explícitos, responsabilidades únicas.
- **Obligatorio**: todo cambio en código implica **tests** (nuevos o ajustados) cumpliendo las reglas estrictas del proyecto, persiguiendo **100% de cobertura** en los archivos tocados.

## Fuente de verdad

- Plan maestro: `.agents/skills/refactorizacion_mcp/SKILL.md`
- Estándar de docstrings/docs: `.agents/skills/estandar_documentacion/SKILL.md`
- Calidad de tests: `.agents/skills/strict_testing/SKILL.md` + skills de testing

## Herramientas

1) Generar ranking + grafo:

```bash
python3 scripts/monolith_analyzer.py --min-loc 250 --top 30
```

Outputs:
- `Documentacion/Refactorizacion_Completa/Monolitos/monolith_report.md`
- `Documentacion/Refactorizacion_Completa/Monolitos/monolith_report.json`

## Definición de “monolito” (para esta fase)

- Archivo Python con **LOC ≥ 250** (LOC = líneas no vacías).  
  (En este repo ya se dividieron los >500 LOC; el trabajo actual es “monolitos medianos” + ciclos/acoplamientos.)
- Priorización por:
  - LOC (más grande primero)
  - `in_degree` (más importado → más riesgo/impacto)
  - `out_degree` (más dependencias → más acoplamiento)

## Bucle determinista (modo continuo)

Repetir hasta que el reporte ya no muestre monolitos por encima del umbral o se alcance el “techo real” (si un archivo no es dividible sin un rediseño mayor).

### Paso 0 — Recalcular reporte

- Ejecutar el analizador (comando arriba).
- Tomar el **primer** archivo del ranking que aún supere el umbral y no esté marcado como “bloqueado”.

### Paso 1 — Diseñar el corte (sin tocar tests primero)

Para el archivo objetivo:
- Identificar **grandes bloques cohesivos** (p.ej. “DTOs/Tipos”, “helpers”, “IO”, “UI wiring”, “queries”, “formatters”).
- Elegir 1 corte “seguro”:
  - Extraer funciones puras/helpers a `*_utils.py`
  - Extraer dataclasses/DTOs locales a `*_dtos.py`
  - Extraer adaptadores/puertos a `*_ports.py`
  - Extraer widgets/partes UI a submódulos `ui/widgets/<area>/...`

Restricción: **no** mezclar varios cortes grandes en una iteración.

### Paso 2 — Ejecutar refactor mínimo

- Mover código a nuevo archivo.
- Mantener API pública: re-export o imports internos para no romper callers.
- Ajustar imports para evitar ciclos (preferir imports locales si es necesario).
- Actualizar docstrings (ver `estandar_documentacion`).

### Paso 3 — Tests (obligatorio)

1) Ejecutar tests del scope mínimo:

```bash
python3 -m pytest <tests_relacionados> -x -q
```

2) Si hay fallos → corregir en la misma iteración.
3) Cuando pase el scope → ejecutar:

```bash
python3 run_tests.py
```

4) **Cobertura 100% en archivos tocados (obligatorio)**:

```bash
python3 scripts/coverage_focus.py --paths <archivos_o_directorios_tocados> --tests <tests_relacionados>
```

Regla: si la cobertura en un archivo tocado es < 100%, el agente debe **crear o mejorar tests** hasta llegar a 100%.

### Paso 4 — Documentación

- Generar/actualizar informe en `Documentacion/Refactorizacion_Completa/Monolitos/`:
  - qué archivo se dividió
  - qué módulos nuevos
  - por qué ese corte
  - riesgos y mitigaciones
- (Opcional si aplica) `python3 scripts/generate_daniel_doc.py`

### Paso 5 — Marcar progreso

En el reporte de monolitos:
- re-ejecutar analizador
- confirmar que el LOC bajó o el archivo salió del ranking

## Reglas de seguridad

- Nunca hacer “big-bang refactor”.
- Nunca cambiar lógica para “hacer pasar tests”.
- No introducir dependencias nuevas salvo necesidad clara.
- Si un monolito está altamente acoplado (in_degree alto), empezar por extracción de helpers/dtos sin cambiar comportamiento.

