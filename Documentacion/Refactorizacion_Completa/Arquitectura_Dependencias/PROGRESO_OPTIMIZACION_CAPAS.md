# Progreso — optimización por capas (Hipatia)

**Fuente de verdad del avance** entre sesiones. El agente debe leer este archivo al iniciar o cuando el usuario pida «continúa con la optimización» y **actualizarlo al cerrar** cada subfase o ítem (junto con `REGISTRO_EJECUCION_ITEMS.md`).

| Campo | Valor |
|-------|--------|
| **ultima_actualizacion** | 2026-04-03 |
| **proxima_accion_sugerida** | Opt-4b **cerrada** (ITEM 021): **0** aristas AST `controllers`→`ui`. Mantenimiento: no reintroducir `from ui` en `controllers/` (test `test_opt4_ast_guard_no_static_ui_imports.py`). Opt-5 **cerrada** en ITEM 019. |

**Informe maestro:** [ANALISIS_CAPAS.md](ANALISIS_CAPAS.md). **Skill:** [`.agents/skills/arquitectura_dependencias_hipatia/SKILL.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/SKILL.md). **Gates:** [`.agents/skills/arquitectura_dependencias_hipatia/references/gates.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/references/gates.md).

---

## Estados

`pendiente` | `en_curso` | `completada`

**Opt-0** es **recurrente**: conviene repetir sus pasos al abrir un sprint largo o tras muchos merges (regenerar informes y comparar con el baseline).

---

## Tabla de fases Opt

| Fase | Estado | Criterio de hecho | Último REGISTRO | Notas |
|------|--------|-------------------|-----------------|-------|
| **Opt-0** | completada | `audit_import_graph` + `architecture_layer_edges` (+ JSON opcional); snapshot opcional en esta carpeta; violaciones no empeoran vs baseline salvo nota | ITEM 009 (herramienta) | Baseline alineado con informe 2026-04-04. Repetir Opt-0 antes de lotes grandes. |
| **Opt-1** | completada | Cero aristas **duras** `core`→`ui` en `reports/architecture_layer_edges.md` | ITEM 010 | Import absoluto `core.qr_scanner.ui` en `scanner.py` (el relativo `.ui` se leía como paquete `ui`). |
| **Opt-2** | completada | Cero aristas `ui`→`database` en informe; sin imports AST a `database` en módulos UI tocados | ITEM 011 | `create_dialog` y `selection_dialogs`: retirados `TYPE_CHECKING` → `database.models`; tests `test_ui_opt2_fabrication_dialogs_boundary`. |
| **Opt-3** | completada | Cero aristas `features`→`ui` en informe | ITEM 012 | Runner de cámara en `controllers/worker/worker_camera_config.py`; import muerto `OrderSetupDialog`. |
| **Opt-4** | completada | Aristas AST `controllers`→`ui` en **0** (carga dinámica + tipos `Any`/`IView`) | ITEM 021 (cierre Opt-4b) | ITEM 013, 020, 021 (2026-04-03). |
| **Opt-5** | completada | Podas `AppModel` por consumidores 0 (`model.*` / `getattr`); DI explícita fuera de este criterio | ITEM 019 (poda 6) | **~77** métodos en `app_model.py`; sin candidatos extra tras barrido cíclico (2026-04-03). |

---

## Sub-ítems y lotes (Opt-4 y otras fases largas)

Añadir filas bajo la fase correspondiente cuando haya varios pasos. Usar la plantilla [`.agents/skills/arquitectura_dependencias_hipatia/references/plantilla_subfase_progreso.md`](../../../../.agents/skills/arquitectura_dependencias_hipatia/references/plantilla_subfase_progreso.md).

### Opt-2 — Sub-ítems (cerrados)

| Sub-ítem | Estado | Módulo | REGISTRO | Notas |
|----------|--------|--------|----------|-------|
| Opt-2a | completada | `create_dialog.py` | ITEM 011 | Sin `database` en AST. |
| Opt-2b | completada | `selection_dialogs.py` | ITEM 011 | Mismo ítem REGISTRO (cierre conjunto). |

### Opt-4 — Cola sugerida (rellenar al elegir lotes)

| Sub-ítem | Estado | Módulo / flujo | REGISTRO | Notas |
|----------|--------|----------------|----------|-------|
| Opt-4a | completada | `calculation_controller.py` (sin import `ui` en AST) | ITEM 013 | Tipos `calc_page` → `Any`. |
| Opt-4b | completada | `ui_class_loader` + migración masiva controladores (sesión ITEM 021) | ITEM 021 | 49→0 aristas AST; test `test_opt4_ast_guard_no_static_ui_imports.py`. |

### Opt-5 — Sub-ítems

| Sub-ítem | Estado | Módulo / cambio | REGISTRO | Notas |
|----------|--------|-----------------|----------|-------|
| Opt-5a | completada | `AppModel`: eliminado `get_all_prep_steps` | ITEM 014 | Sin consumidores; API en `SystemFacade` / servicios. |
| Opt-5b | completada | `AppModel`: eliminado `get_all_ordenes_fabricacion` | ITEM 015 | Sin consumidores vía `model`; uso real vía `fabricacion_service` / repo. |
| Opt-5c | completada | `AppModel`: retirados `search_lotes` / `create_lote` / `update_lote` / `delete_lote` | ITEM 016 | Se mantiene `get_lote_details` (`calculate_times_widget`). |
| Opt-5d | completada | `AppModel`: iteraciones/imagenes vía `db`/`facade` sin hub | ITEM 017 | Ajuste `IProductModel` (sin `update_iteration_file_path`). |
| Opt-5e | completada | `AppModel`: `get_latest_products`, `get_worker_history`, `get_worker_activity_log` | ITEM 018 | Listados vía `product_facade` / `worker_service` en controladores y widgets. |
| Opt-5f | completada | `AppModel`: lote servicios (`worker`/`machine`/`prep`/`product`/`planning`/`config`) | ITEM 019 | Cierre ciclo poda; métodos restantes con al menos un `model.*` en árbol. |

---

## Historial breve de cambios de estado

| Fecha | Fase | Cambio |
|-------|------|--------|
| 2026-04-04 | — | Creación del documento; Opt-0 marcada completada respecto al baseline del informe maestro. |
| 2026-04-05 | Opt-1 | Completada (ITEM 010); `core`→`ui` duro en 0 aristas en informe regenerado. |
| 2026-04-05 | Opt-2 | Completada (ITEM 011); `ui`→`database` en 0 aristas; tests de frontera AST. |
| 2026-04-05 | Opt-3 | Completada (ITEM 012); `features`→`ui` en 0 aristas. |
| 2026-04-05 | Opt-4 | Lote 1 (ITEM 013); `controllers`→`ui`: 56→55 aristas; §1.1 en ANALISIS_CAPAS sobre documentación. |
| 2026-04-03 | Opt-4 / Opt-5 | Opt-4 marcada completada con backlog 55 aristas; Opt-5 en curso; ITEM 014 poda `get_all_prep_steps` en `AppModel`. |
| 2026-04-03 | Opt-5 | ITEM 015: poda `get_all_ordenes_fabricacion` en `AppModel`. |
| 2026-04-03 | Opt-5 | ITEM 016: poda CRUD lote en `AppModel` (salvo `get_lote_details`). |
| 2026-04-03 | Opt-5 | ITEM 017: poda iteraciones/imágenes redundantes en `AppModel` + `IProductModel`. |
| 2026-04-03 | Opt-5 | ITEM 018: poda `get_latest_products` y métodos historial/log trabajador en `AppModel`. |
| 2026-04-03 | Opt-5 | ITEM 019: lote poda + barrido cíclico sin candidatos; Opt-5 → completada. |
| 2026-04-03 | Opt-4b | ITEM 020: sin import AST `ui` en `lote_controller`, `report_controller`, `ui_controller`; TYPE_CHECKING `ui` retirado en `machine_controller`; informe 55→49 aristas. |
| 2026-04-03 | Opt-4b | ITEM 021: `controllers/ui_class_loader.py`; eliminación de todos los imports estáticos `ui` bajo `controllers/`; informe 49→0 aristas AST. |
