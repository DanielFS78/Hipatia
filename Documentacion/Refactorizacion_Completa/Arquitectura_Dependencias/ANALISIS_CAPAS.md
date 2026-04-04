# Análisis de arquitectura por capas — Hipatia

Documento maestro para el **mapa de dependencias**, **violaciones** y **cola de remedios** entre las capas `ui`, `controllers`, `core`, `database` y `features`.

**Última regeneración de informes (referencia):** 2026-04-03 (post Opt-4b ITEM 021: **0** aristas AST `controllers`→`ui`; 49→0 tras `ui_class_loader` + carga dinámica). **Actualización ejecutiva:** 2026-04-03 — Opt-5 **cerrada** (ITEM 014–019): **~77** métodos en `app_model.py`; sin más podas seguras solo con `rg` sobre `model.*` / `getattr(..., "model")`.

---

## 1. Cómo regenerar los informes

| Herramienta | Comando | Salida por defecto |
|-------------|---------|-------------------|
| Audit histórico controladores ↔ servicios | `python3 scripts/audit_import_graph.py` | [`reports/import_graph_audit.md`](../../../../reports/import_graph_audit.md) |
| Grafo completo por capas + violaciones + ciclos | `python3 scripts/architecture_layer_edges.py` | [`reports/architecture_layer_edges.md`](../../../../reports/architecture_layer_edges.md) |
| JSON (opcional, CI o filtros) | `python3 scripts/architecture_layer_edges.py --json reports/architecture_layer_edges.json` | `reports/architecture_layer_edges.json` |

**Snapshots archivados en esta carpeta** (no sustituyen `reports/`; sirven de hito en git):

- [`import_graph_audit_snapshot_2026-04-04.md`](import_graph_audit_snapshot_2026-04-04.md)
- [`architecture_layer_edges_snapshot_2026-04-04.md`](architecture_layer_edges_snapshot_2026-04-04.md)

**Tests del analizador:** `python3 -m pytest tests/unit/test_architecture_layer_edges.py -q`

### 1.1 Documentación que se actualiza en cada ítem de optimización

| Artefacto | Cuándo |
|-----------|--------|
| `REGISTRO_EJECUCION_ITEMS.md` | Siempre al cerrar un ítem |
| `PROGRESO_OPTIMIZACION_CAPAS.md` | Siempre (estado Opt, `proxima_accion_sugerida`) |
| `reports/architecture_layer_edges.md` (+ JSON) | Tras cambios que afecten imports entre capas |
| Este `ANALISIS_CAPAS.md` | Cuando cambie el diagnóstico ejecutivo o la fecha de regeneración |
| `python3 scripts/check_documentation_omissions.py` | Objetivo omitidos=0 en cada cierre de ítem |
| `python3 scripts/generate_daniel_doc.py` | **Hitos mayores** (varios módulos o contrato público), según [`.agents/skills/arquitectura_dependencias_hipatia/references/gates.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/references/gates.md) — no obligatorio en cada micro-lote Opt-4 |

---

## 2. Baseline de calidad (Fase 1)

Ejecutado sin cambios de producto en el cierre de la entrega de herramientas:

- **Mypy (equivalente CI):** `python3 -m mypy app.py core controllers database features ui tests` → sin errores (607 archivos en verificación 2026-04-05; puede variar al añadir módulos).
- **Pytest muestra:** `tests/unit/test_startup_controller.py` → OK (baseline focal).

---

## 3. Indicador de superficie del hub (`AppModel`)

En `core/app_model.py`, el **número de métodos** (`def` a nivel de clase) es del orden de **~77** (tras ITEM 019 / Opt-5f, 2026-04-03). Es un **indicador de delegación/fachada**. Las podas «ciegas» con `rg` = 0 consumidores `model.*` están **agotadas**; una reducción mayor exige **migración explícita** a servicios/fachadas inyectados (skill [`.agents/skills/reduccion_god_objects/SKILL.md`](../../../../.agents/skills/reduccion_god_objects/SKILL.md)).

---

## 4. Resumen ejecutivo (Fase 3)

### 4.1 Fiabilidad y riesgo de regresión

- El grafo por **imports AST** es **estático**: no ve `importlib` dinámico ni imports por cadena.
- Los **ciclos entre capas** listados en `architecture_layer_edges.md` son **simples** (2- y 3-aristas). Un ciclo `database ↔ core` es **esperable** en un monolito (modelos/ORM vs servicios); no implica por sí solo bug en runtime.
- **Violación dura `core`→`ui`:** **Resuelta (2026-04-05, ITEM 010 / Opt-1).** El informe anterior listaba `core.qr_scanner.scanner` → `ui` por un import relativo `from .ui` que el AST registra como el paquete top-level `ui`; el módulo real es `core.qr_scanner.ui` (dibujo OpenCV). Sustituido por import absoluto `from core.qr_scanner.ui import draw_qr_detection`. Ver `reports/architecture_layer_edges.md` (0 aristas en `core`→`ui`).

### 4.2 Escalabilidad (código)

- **controllers → ui** (**0** aristas AST tras ITEM 021: sin `import`/`from` estático a `ui` en `controllers/`; la UI se resuelve en runtime vía `controllers/ui_class_loader.py` y `importlib`). Histórico: 56 → 55 (ITEM 013), 55 → 49 (ITEM 020), 49 → 0 (ITEM 021).
- **ui → database:** **Resuelto (ITEM 011 / Opt-2).** Antes **2 aristas** AST por `TYPE_CHECKING` → `database.models` en `create_dialog` y `selection_dialogs` (sin uso en runtime). Retirados esos imports; informe actual: **0 aristas** `ui`→`database`. Regresión: [`tests/unit/test_ui_opt2_fabrication_dialogs_boundary.py`](../../../../tests/unit/test_ui_opt2_fabrication_dialogs_boundary.py).
- **features → ui:** **Resuelto (ITEM 012 / Opt-3).** Antes **2 aristas** (`worker_controller` → `tracking_dialogs` import muerto; `worker_controller_io_manager` → `camera_config_dialog`). Cámara centralizada en [`controllers/worker/worker_camera_config.py`](../../../../controllers/worker/worker_camera_config.py) con `camera_config_runner` inyectado. Informe: **0 aristas** `features`→`ui`.

### 4.3 Priorización sugerida (P0 / P1 / P2)

Alineado con [`.agents/skills/ejecucion_secuencial_calidad/references/priorizacion.md`](../../../../.agents/skills/ejecucion_secuencial_calidad/references/priorizacion.md):

| Prioridad | Tema | Acción |
|-----------|------|--------|
| **P0** | Ciclos que impidan arranque o import circular real en `app_controller` | Si el analizador AST o un fallo de import lo demuestra, **un ítem único** en `REGISTRO_EJECUCION_ITEMS.md`. *En el snapshot 2026-04-04 no se abre P0 automático por grafo de capas solo.* |
| **P1** | `core` → `ui`; `ui` → `database` | Ítems pequeños: extraer interfaz en `core`, sustituir modelos SQLAlchemy en UI por DTO. |
| **P2** | Podas `AppModel`; reducir `controllers` → `ui` donde haya duplicación | Un módulo o flujo por ítem; tests focales. |

---

## 5. Fase 4 — Remedios iterativos (operativa)

Cada remediación es **un ítem cerrado** con:

1. Alcance mínimo (una violación o un módulo).
2. Código + tests (ver [`.agents/skills/testing_por_capa/SKILL.md`](../../../../.agents/skills/testing_por_capa/SKILL.md)).
3. **Gates:** ver [`.agents/skills/arquitectura_dependencias_hipatia/references/gates.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/references/gates.md).
4. **REGISTRO:** plantilla en [`.agents/skills/arquitectura_dependencias_hipatia/references/plantilla_item_registro.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/references/plantilla_item_registro.md).
5. Tras hitos mayores: `python3 scripts/generate_daniel_doc.py` y `python3 scripts/check_documentation_omissions.py`.
6. **Sync iCloud** si el worktree no es el de iCloud: [`.agents/skills/ejecucion_secuencial_calidad/references/sync_icloud_continuo.md`](../../../../.agents/skills/ejecucion_secuencial_calidad/references/sync_icloud_continuo.md).

**Skill conductora:** [`.agents/skills/arquitectura_dependencias_hipatia/SKILL.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/SKILL.md).

**Agente Cursor sugerido:** [`.cursor/agents/hipatia-arquitectura-dependencias.md`](../../../../.cursor/agents/hipatia-arquitectura-dependencias.md).

---

## 6. Límites del análisis

- No sustituye **pruebas manuales** ni **carga real**.
- **Multiusuario / HA** dependen del **motor de BD y despliegue** (p. ej. PostgreSQL), no solo del grafo.
- Los “techos” del dashboard de tests **no miden** arquitectura; este informe es **complementario**.

---

## 7. Referencias cruzadas

- [`.agents/skills/reduccion_god_objects/SKILL.md`](../../../../.agents/skills/reduccion_god_objects/SKILL.md)
- [`.agents/skills/ui_dialog_dependency_wiring/SKILL.md`](../../../../.agents/skills/ui_dialog_dependency_wiring/SKILL.md)
- [`.agents/skills/ejecucion_secuencial_calidad/SKILL.md`](../../../../.agents/skills/ejecucion_secuencial_calidad/SKILL.md)
- [`.agents/skills/estandar_documentacion/SKILL.md`](../../../../.agents/skills/estandar_documentacion/SKILL.md)

---

## 8. Roadmap de optimización y progreso

El **seguimiento por fases Opt-0 … Opt-5** (estado `pendiente` / `en_curso` / `completada`, sub-lotes, `proxima_accion_sugerida`) vive en un solo archivo para que el agente y las sesiones de chat retomen sin perder contexto:

- **[PROGRESO_OPTIMIZACION_CAPAS.md](PROGRESO_OPTIMIZACION_CAPAS.md)**

No duplicar aquí tablas largas de checklist: enlazar y mantener el informe ejecutivo de la §4; el archivo de progreso refleja **qué toca a continuación** tras cada ítem cerrado.
