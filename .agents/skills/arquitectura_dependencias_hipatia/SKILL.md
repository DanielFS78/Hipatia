---
name: Arquitectura dependencias Hipatia
description: Auditoría por capas (fases 1–3), roadmap de optimización Opt-0–Opt-5 con progreso persistente en PROGRESO_OPTIMIZACION_CAPAS.md, y remedios iterativos (Fase 4). Ante «continúa con la optimización», leer progreso y ejecutar la siguiente subfase con gates y REGISTRO.
---

# Arquitectura y dependencias — Hipatia

## Objetivo

Mantener un **mapa vivo** de dependencias entre capas, detectar **violaciones** y **ciclos** a nivel de prefijo, y ejecutar **remedios mínimos** sin mega-refactors, alineado con [ejecucion_secuencial_calidad](../ejecucion_secuencial_calidad/SKILL.md).

## Documentos maestros

| Documento | Rol |
|-----------|-----|
| [ANALISIS_CAPAS.md](../../../Documentacion/Refactorizacion_Completa/Arquitectura_Dependencias/ANALISIS_CAPAS.md) | Informe ejecutivo, cómo regenerar, P0–P2, límites |
| [PROGRESO_OPTIMIZACION_CAPAS.md](../../../Documentacion/Refactorizacion_Completa/Arquitectura_Dependencias/PROGRESO_OPTIMIZACION_CAPAS.md) | **Estado por fase Opt** y `proxima_accion_sugerida` entre sesiones |

## Auditoría (fases 1–3) — hito de repositorio

Suelen estar **cerradas** salvo regeneración o ampliación de la herramienta:

1. **Fase 1 — Inventario y baseline:** `audit_import_graph`, `architecture_layer_edges`, snapshots opcionales, baseline mypy/pytest en `ANALISIS_CAPAS.md`.
2. **Fase 2 — Herramienta:** [scripts/architecture_layer_edges.py](../../../scripts/architecture_layer_edges.py), tests [tests/unit/test_architecture_layer_edges.py](../../../tests/unit/test_architecture_layer_edges.py).
3. **Fase 3 — Informe ejecutivo:** consolidar violaciones y tabla P0/P1/P2 en `ANALISIS_CAPAS.md`.

## Optimización (fases Opt-0 … Opt-5) — trabajo iterativo

Definidas en `PROGRESO_OPTIMIZACION_CAPAS.md`:

- **Opt-0:** mantenimiento / baseline (recurrente antes de lotes grandes).
- **Opt-1:** P1 duro — eliminar `core`→`ui`.
- **Opt-2:** P1 — eliminar `ui`→`database` (DTO/servicios).
- **Opt-3:** P1 — `features`→`ui`.
- **Opt-4:** P2 — lotes `controllers`→`ui` (un módulo o flujo por ítem).
- **Opt-5:** P2 — podas `AppModel` ([reduccion_god_objects](../reduccion_god_objects/SKILL.md)).

Cada cambio de código es **Fase 4 remedios**: un ítem REGISTRO + gates.

## Protocolo obligatorio para el agente

1. Leer **[PROGRESO_OPTIMIZACION_CAPAS.md](../../../Documentacion/Refactorizacion_Completa/Arquitectura_Dependencias/PROGRESO_OPTIMIZACION_CAPAS.md)** al inicio o cuando el usuario pida continuar la optimización.
2. Elegir la **primera fase/subfase `pendiente`** o la marcada **`en_curso`**.
3. Trabajar **un ítem acotado** por iteración de chat salvo petición explícita de lote mayor.
4. Aplicar [references/gates.md](references/gates.md) y cerrar en [REGISTRO_EJECUCION_ITEMS.md](../../../Documentacion/Refactorizacion_Completa/Auditoria_Secuencial/REGISTRO_EJECUCION_ITEMS.md) con [references/plantilla_item_registro.md](references/plantilla_item_registro.md).
5. Tras remedios relevantes: `python3 scripts/architecture_layer_edges.py` (y JSON si se usa). Actualizar `ANALISIS_CAPAS.md` si cambia el diagnóstico o la **última regeneración**.
6. **Actualizar el progreso:** estado de la fase, fecha en `ultima_actualizacion`, ítem REGISTRO, **`proxima_accion_sugerida`**, y una línea en el historial del progreso si aplica.

## Eje paralelo: plan de calidad (tests)

La optimización por capas **no sustituye** el flujo del hub [plan_mejora_calidad](../plan_mejora_calidad/SKILL.md) (dashboard de tests, antipatrones). Conviven: arquitectura aquí; calidad de tests allí.

## Fase 4 — Remedios (detalle)

Un **ítem** = una violación o un módulo puente.

- Seguir [references/gates.md](references/gates.md) (incluye actualizar `PROGRESO_OPTIMIZACION_CAPAS.md` al cerrar ítems de optimización).

## Skills relacionadas

| Skill | Uso |
|-------|-----|
| [reduccion_god_objects](../reduccion_god_objects/SKILL.md) | Podas `AppModel` |
| [ui_dialog_dependency_wiring](../ui_dialog_dependency_wiring/SKILL.md) | DI en diálogos |
| [ejecucion_secuencial_calidad](../ejecucion_secuencial_calidad/SKILL.md) | Gates y REGISTRO |
| [estandar_documentacion](../estandar_documentacion/SKILL.md) | Docstrings / generación |
| [testing_por_capa](../testing_por_capa/SKILL.md) | Tests por capa |
| [strict_testing](../strict_testing/SKILL.md) | Calidad de tests |
| [plan_mejora_calidad](../plan_mejora_calidad/SKILL.md) | Hub tests / fases de calidad (paralelo) |

## Agente sugerido

Ver [.cursor/agents/hipatia-arquitectura-dependencias.md](../../../.cursor/agents/hipatia-arquitectura-dependencias.md).

## Límites

- Solo imports **AST** estáticos.
- Ciclos entre capas **no** equivalen solos a bug; interpretar con contexto (p. ej. `database ↔ core`).
- Si el progreso fue editado a mano, **releer el archivo completo** antes de avanzar.
