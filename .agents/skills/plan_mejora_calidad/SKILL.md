---
name: Plan de Mejora de Calidad
description: Hub central del plan de mejora de calidad del proyecto Hipatia. Define fases, subfases, orden de ejecución, medidas de seguridad, cómo documentar el progreso y cómo actualizar las skills al completar cada fase. LEE ESTE DOCUMENTO PRIMERO en cada sesión de mejora de calidad.
---

# Plan de Mejora de Calidad — Proyecto Hipatia

> **⚠️ INSTRUCCIÓN CRÍTICA PARA LA IA (agente de tests):**
> 1. Este documento es la **Única Fuente de Verdad** del plan de mejora de calidad. **LEE ESTE DOCUMENTO PRIMERO** en cada sesión.
> 2. Trabaja **una sección de antipatrones** cada vez (tabla "Secciones de antipatrones"); dentro de cada sección, **un archivo o ítem a la vez**.
> 3. Tras **cada** cambio: ejecutar los tests del scope afectado (`pytest <archivo> -x -q`). Si hay fallo, warning o skipped, **ajustar el test** hasta que todo pase. **No se toleran** errores, avisos ni skipped; los tests han de ser sólidos.
> 4. Al **terminar una sección**: actualizar documentación (analizador, métricas, docs generados) y **solo entonces** pasar a la siguiente sección.
> 5. Luego lee `.agents/skills/backlog_tests/SKILL.md` para reglas de corrección y checklist.
> 6. **Sincronización iCloud:** si el workspace es un worktree distinto del repo en iCloud Drive, **el agente** copia con `cp` todos los archivos tocados al clon Hipatia en iCloud **de forma continua** (tras cada lote de ediciones) — `.agents/skills/ejecucion_secuencial_calidad/references/sync_icloud_continuo.md`. No delegar en el usuario salvo fallo de entorno.

---

## Estado Actual

* **Fases del plan (tabla «Mapa de Fases»):** ✅ **Todas cerradas** a efectos del cierre global 2026-03-20. No queda fase obligatoria abierta.
* **Fase 12C (frontera UI/DTO):** ✅ Cerrada — catálogo estricto en 0 (`scripts/ui_dto_findings_catalog.py`); ver `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md`. **Mypy:** `python3 -m mypy . --config-file mypy.ini` en verde.
* **Score absoluto medio:** 76.7/100
* **Score optimizado medio:** 79.0/100
* **Archivos en su techo real:** 201/201
* **Actualizados:** 130 | **En Progreso:** 71 | **Legacy:** 0
* **Cobertura Global:** 97.4% media
* **MagicMock() sin spec:** 335 (todos inevitables ✅)
* **@patch sin autospec:** 7 (todos inevitables ✅)
* **Tests sin assert:** 0
* **Ctrl/Svc sin assert_called:** 0 archivos
* **Mock sesión BD:** 0 archivos
* **MagicMock(spec=object):** 0
* **Suite de tests:** ✅ 0 fallos — ver último `run_tests.py` (el dashboard puede listar ~200+ archivos; no implica fase pendiente)
* **Última actualización:** 2026-03-20 — Fase 12C (frontera UI/DTO) cerrada; catálogo estricto en 0; `run_tests.py` ✅

---

## Mapa de Fases y Estado

| Fase | Nombre | Estado | Prioridad |
|------|--------|--------|-----------|
| **1** | Corrección de Tests Críticos | ✅ COMPLETADA | CRÍTICA |
| **2** | Eliminación de Antipatrones de Testing | ✅ COMPLETADA | ALTA |
| **3** | Refactorización de Archivos Monolíticos | ✅ CERRADA (sin más reducción) | ALTA |
| **4** | Corrección de Código Legacy | ✅ COMPLETADA | MEDIA |
| **5** | Corrección de Errores Mypy | ✅ COMPLETADA | MEDIA |
| **6** | Configuración de CI/CD | ✅ COMPLETADA | Calidad asegurada con `run_tests.py` y analizadores en local; pipeline CI en servidor queda como mejora opcional futura |
| **7** | Documentación Técnica de Arquitectura | ✅ COMPLETADA | `generate_daniel_doc.py`, `Documentacion/`, estándar en `estandar_documentacion` |

**Nota:** Plan de refactorización histórico (MCP) archivado y retirado del repo. La **Fase 12C** quedó cerrada en 2026-03-20; vigilancia del catálogo: `python3 scripts/ui_dto_findings_catalog.py`.

---

## Flujo del agente de tests — Regla de oro

**Una tarea (o sección) cada vez. Tras cada cambio: ejecutar tests, corregir hasta que pasen sin errores, avisos ni skipped. Al cerrar una sección: actualizar documentación y pasar a la siguiente.**

- **No se toleran:** fallos, warnings ni tests skipped. Los tests han de ser sólidos para optimizar el código del programa.
- **Orden:** trabajar siempre la **siguiente sección** de la lista "Secciones de antipatrones (orden)"; dentro de cada sección, un archivo (o ítem) cada vez.
- **Verificación obligatoria tras cada archivo/ítem:** `python3 -m pytest <archivo> -x -q` (o el scope que corresponda). Si algo falla o hay skipped: ajustar el test de forma óptima hasta que todo pase.
- **Cierre de sección:** cuando se termina una sección completa: actualizar documentación (`test_reports/compliance_data.json` vía `python3 scripts/test_quality_analyzer.py`, y si aplica `scripts/generate_daniel_doc.py` / Plan/Backlog) y **solo entonces** pasar a la siguiente sección.

---

## Modo continuo (obligatorio cuando el usuario diga “continúa hasta concluir”)

Cuando el usuario pida ejecutar **todo lo pendiente de forma seguida**, el agente debe actuar como un bucle determinista:

1. **Identificar el siguiente archivo/ítem**
   - Usar `python3 scripts/test_quality_analyzer.py` y/o `test_reports/compliance_data.json`.
   - Elegir **el siguiente archivo con penalizaciones corregibles** de la **sección activa** (tabla “Secciones de antipatrones”).
   - Dentro de la sección, priorizar por **mayor penalización corregible** (más negativa) y luego por impacto (más tests).
2. **Corregir SOLO ese archivo/ítem**
   - Aplicar las reglas de `.agents/skills/backlog_tests/SKILL.md` y `.agents/skills/testing_fixtures_y_mocks/SKILL.md`.
3. **Verificar inmediatamente**
   - Ejecutar: `python3 -m pytest <archivo> -x -q`.
   - Si hay fallo/warning/skipped: iterar hasta que pase todo.
4. **Validar score óptimo alcanzable**
   - Ejecutar `python3 scripts/test_quality_analyzer.py`.
   - Confirmar que el archivo ya **no tiene penalización corregible** de la sección activa, o que llegó a su **techo real**.
5. **Actualizar listado y repetir**
   - Marcar el archivo como ✅ en el listado vivo del backlog (ver `.agents/skills/backlog_tests/SKILL.md`).
   - Volver al paso 1 y repetir hasta que no queden penalizaciones corregibles de la sección activa.

El agente **no debe** pedir confirmaciones: debe elegir el siguiente archivo, corregir, ejecutar tests, y actualizar el listado.

---

## Secciones de antipatrones (orden de ejecución)

El agente debe abordar **una sección cada vez**, en este orden. Dentro de cada sección, **un archivo (o ítem) a la vez**; tras cada uno, ejecutar tests y asegurar 0 fallos, 0 warnings, 0 skipped.

| # | Sección | Objetivo | Criterio de cierre |
|---|--------|----------|--------------------|
| 1 | **Tests sin assert** | Eliminar los ~30 tests que no tienen ningún assert | Cada test tiene al menos un assert observable (o `assert True` con `# smoke_test: ...` solo si es humo). Pytest del archivo pasa. |
| 2 | **Ctrl/Svc sin assert_called\*** | Los 5 archivos de controladores/servicios que no comprueban llamadas | En cada archivo, los tests que ejercitan el controlador/servicio comprueban interacción con dependencias (call_count + assert_called_*). Pytest del archivo pasa. |
| 3 | **MagicMock() sin spec (corregibles)** | Reducir los 332 MagicMock sin spec que son corregibles | Sustituir por `MagicMock(spec=[...])` o `create_autospec` solo en clases del proyecto (nunca en Qt). Un archivo cada vez; pytest pasa. |
| 4 | **@patch sin autospec (corregibles)** | Añadir autospec en los 44 patches corregibles | `autospec=True` solo donde el target NO sea Qt/builtins/OS. Un archivo cada vez; pytest pasa. |
| 5 | **Mock de sesión BD** | Documentar o reducir los 19 archivos que mockean sesión | Decisión por archivo: fixture real (in-memory) o dejar documentado; no introducir fallos. |
| 6 | **MagicMock(spec=object)** | Revisar los 21 usos de spec=object | Donde sea posible, sustituir por spec concreto; si es intencional (Qt/compat), dejar documentado. Pytest estable. |

**Estado (2026-03-17): Secciones 1–6 ✅ COMPLETADAS** (no quedan penalizaciones corregibles; todos los archivos en su techo real).

Tras **cerrar una sección**: ejecutar `python3 scripts/test_quality_analyzer.py`, actualizar "Estado Actual" en este documento y, si aplica, backlog y documentación generada. Luego pasar a la siguiente sección.

---

## Flujo de Trabajo Obligatorio (CADA SESIÓN)

### Paso 1 — Preparación
1. Leer este documento (y la tabla "Secciones de antipatrones" para saber la sección activa).
2. (Solo durante Fase de tests) Leer `.agents/skills/orden_trabajo_tests/SKILL.md` si se trabaja por archivos en lista; o revisar `test_reports/compliance_data.json` (o salida de `scripts/test_quality_analyzer.py`) para la sección de antipatrones que toque.
3. Leer `.agents/skills/backlog_tests/SKILL.md` — reglas de corrección y Checklist Revisión Fase B.
4. Ejecutar `python3 run_tests.py` para ver el estado actual (0 fallos antes de empezar).

### Paso 2 — Ejecución (una tarea a la vez)
5. Elegir **un solo archivo o ítem** de la sección activa (tests sin assert, Ctrl/Svc sin assert_called, MagicMock sin spec, etc.).
6. Aplicar las correcciones según backlog y Checklist Revisión Fase B (mocks con spec donde aplique, call_count, asserts reales, etc.).
7. Ejecutar **siempre** `python3 -m pytest <archivo> -x -q` (o el scope del ítem). Si hay fallo, warning o skipped: **ajustar el test de forma óptima** hasta que todo pase (sin tocar código de producción para hacer pasar el test).
8. Repetir 5–7 para el siguiente ítem de la misma sección hasta completarla.

### Paso 3 — Cierre de sección y documentación
9. Cuando se **termine una sección completa**: ejecutar `python3 scripts/test_quality_analyzer.py`; actualizar "Estado Actual" en este documento; actualizar backlog/registro si aplica; regenerar documentación si está definido (`scripts/generate_daniel_doc.py`).
10. Pasar a la **siguiente sección** de la tabla "Secciones de antipatrones" y reiniciar desde el Paso 2.

---

## Reglas Estrictas (SIEMPRE ACTIVAS)

1. **Nunca modificar código fuente** para hacer pasar un test
2. **0 tests fallando** antes de marcar cualquier archivo como completado
3. **Cero tolerancia a fallos, warnings y skipped:** tras cada cambio el agente ejecuta los tests del scope afectado; si hay error, warning o skipped, **debe ajustar el test** (o la corrección) de forma óptima hasta que pasen todos. Objetivo: tests sólidos que optimicen el código propio del programa.
4. **Una tarea a la vez:** un archivo o ítem por ciclo; verificar (pytest); solo entonces pasar al siguiente. Al terminar una **sección** completa, actualizar documentación y luego pasar a la siguiente sección.
5. **Score no puede bajar** entre iteraciones
6. **Cobertura no puede bajar** del baseline (97.3%)
7. **Español** para todos los docstrings, comentarios e informes
8. **NUNCA usar `autospec=True` con clases Qt (PyQt6)** — usar `MagicMock()` sin spec para widgets
9. **Siempre añadir `assert x.call_count == N`** antes de `assert_called_once_with(...)` — el analizador no detecta `assert_called_once_with` como assert explícito

---

## Cómo Actualizar el Backlog al Completar Archivos

Después de completar cada archivo:
1. Abrir `.agents/skills/backlog_tests/SKILL.md`
2. Marcar el archivo con ✅ y anotar el score antes/después
3. Actualizar las métricas globales en "Estado Actual" de este documento
4. Si el archivo alcanzó su techo real, añadir nota "en techo"

---

## Métricas de Progreso

| Métrica | Baseline | Fase 1 | Fase 2 actual | Objetivo |
|---------|----------|--------|---------------|----------|
| Score absoluto medio | 34.1 | 34.9 | 76.7 | 80 |
| Score optimizado medio | — | — | 79.0 | 80 |
| Tests sin asserts | 583 | 0 | (ver JSON) | 0 |
| Cobertura | 88.20% | 96.8% | 97.4% | 90% |
| Archivos en techo | — | — | 201/201 | 201/201 |
| Archivos fallando | — | 9 | 0 | 0 |

---

## Skills de Referencia

| Skill | Cuándo leerla |
|-------|---------------|
| `.agents/skills/orden_trabajo_tests/SKILL.md` | Solo Fase de tests — histórico/orden de trabajo ya cerrado (188/188 ✅) |
| `.agents/skills/backlog_tests/SKILL.md` | **SIEMPRE** — reglas de corrección y Checklist Revisión Fase B |
| `.agents/skills/strict_testing/SKILL.md` | Al escribir cualquier test |
| `.agents/skills/testing_antipatrones/SKILL.md` | Al corregir antipatrones |
| `.agents/skills/testing_fixtures_y_mocks/SKILL.md` | Al construir mocks y fixtures |
| `.agents/skills/testing_por_capa/SKILL.md` | Al testear una capa específica |
| `.agents/skills/testing_pyqt6_headless/SKILL.md` | Al testear widgets Qt |
| `.agents/skills/estandar_documentacion/SKILL.md` | Al añadir docstrings |

---

## Ubicaciones Importantes

| Recurso | Ruta |
|---------|------|
| **Backlog priorizado** | `.agents/skills/backlog_tests/SKILL.md` |
| **Analizador de calidad** | `scripts/test_quality_analyzer.py` |
| **Runner de tests** | `run_tests.py` |
| **Datos de compliance** | `test_reports/compliance_data.json` |
| **Informes de fase** | `Documentacion/Mejora_Calidad/` |

---

## Mantenimiento (sin fase obligatoria abierta)

El plan de fases está **cerrado**. Lo siguiente es **vigilancia** y mejora opcional:

- **Fase 12C — Sanear Frontera UI/DTO:** ✅ cerrada (2026-03-20). Referencia y mantenimiento: `.agents/skills/fase12c_sanear_frontera_ui/SKILL.md`; regresiones: `python3 scripts/ui_dto_findings_catalog.py`.
- **Tipado estricto (Mypy):** auditoría global `python3 -m mypy . --config-file mypy.ini`.
- `.agents/skills/estandar_documentacion/SKILL.md` (docstrings + generación de documentación)
