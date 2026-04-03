---
name: Backlog de Tests — Lista Priorizada
description: Lista ordenada por impacto de todos los archivos de test que necesitan mejora. Para cada archivo indica el score actual, el techo alcanzable, los antipatrones a corregir y las instrucciones exactas. Actualizar este documento después de completar cada archivo.
---

# Backlog de Tests — Lista Priorizada

> Generado el 2026-03-15 desde `test_reports/compliance_data.json`.
> Actualizar este documento después de completar cada archivo marcando ✅ y anotando el score final.

**Orden de trabajo (siguiente a realizar):** ver **`.agents/skills/orden_trabajo_tests/SKILL.md`**. Es la lista única de 188 archivos con columna **Estado** (— pendiente / ✅ hecho). Siempre trabajar el **primer —**; al completar (corregir + pytest pasa + checklist Fase B), marcar ✅ en esa skill y pasar al siguiente.

---

## Cómo usar este backlog (flujo del agente de tests)

El agente que corrige tests debe seguir **siempre** el plan en `.agents/skills/plan_mejora_calidad/SKILL.md`: trabajar **una sección** de antipatrones (y dentro de ella **un archivo a la vez**), ejecutar tests tras cada cambio y no pasar a la siguiente sección hasta actualizar la documentación.

1. **Orden de trabajo:** seguir la tabla "Secciones de antipatrones (orden de ejecución)" del Plan. La primera sección es "Tests sin assert", luego "Ctrl/Svc sin assert_called*", etc.
2. **Por archivo/ítem:** leer la sección correspondiente de este backlog (si existe); aplicar las correcciones; ejecutar `python3 -m pytest <archivo> -x -q`.
3. **Cero tolerancia:** si hay fallo, warning o skipped, **ajustar el test** de forma óptima hasta que todo pase. No marcar ✅ hasta que los tests sean sólidos.
4. Marcar ✅ y anotar score antes/después cuando el archivo cumpla el checklist y los tests pasen.
5. **Al cerrar una sección completa:** ejecutar `python3 scripts/test_quality_analyzer.py`, actualizar métricas en el Plan y, si aplica, regenerar documentación; **después** pasar a la siguiente sección.

---

## Listado vivo — Sección activa (marcar ✅ tras pytest + analizador)

Este bloque es el **work order real** cuando el usuario pida “hazlos todos seguidos”.
**Estado (2026-03-17): ✅ Sección de tests cerrada** — no quedan penalizaciones corregibles y todos los archivos están en su techo real (ver `python3 run_tests.py`).

- **Fuente**: salida de `python3 scripts/test_quality_analyzer.py` (bloque “ARCHIVOS CON PENALIZACIONES CORREGIBLES”).
- **Regla**: trabajar **uno por uno** los que tengan la penalización de la **sección activa**.
- **Criterio ✅**: `pytest <archivo> -x -q` pasa y el analizador ya no muestra la penalización de la sección (o el archivo queda en su techo real).

### Sección 3 — `MagicMock()` sin spec (corregibles)

> Estado (2026-03-17): ✅ completada. Lista mantenida como histórico.

| Archivo | Estado | Nota |
|---|---:|---|
| `tests/unit/test_lotes_widget.py` | ✅ | Eliminado `loose_mocks`; techo PyQt6 |
| `tests/unit/test_historial_widget.py` | ✅ | `loose_mocks` eliminado; quedan otras secciones |
| `tests/unit/test_canvas_widgets_coverage.py` | ✅ | `loose_mocks` eliminado; techo PyQt6 |
| `tests/unit/test_timeline_widget.py` | ✅ | `loose_mocks` eliminado; quedan patches_no_autospec |
| `tests/integration/test_dialogs_integration.py` | ✅ | 70/70 |
| `tests/e2e/test_main_window_flows.py` | ✅ | 70/70 |
| `tests/unit/test_app_model.py` | ✅ | `loose_mocks` eliminado; quedan assert_called_no_args |
| `tests/unit/test_fabrication_dialogs.py` | ✅ | `loose_mocks` eliminado; quedan assert_called_no_args |
| `tests/unit/test_report_strategy_comprehensive.py` | ✅ | `loose_mocks` eliminado; quedan otras secciones |
| `tests/unit/test_security_phase2_integration.py` | ✅ | `loose_mocks` eliminado; queda mock_session |
| `tests/unit/test_file_controller.py` | ✅ | `loose_mocks` eliminado; quedan otras secciones |
| `tests/unit/test_scheduler_logic.py` | ✅ | `loose_mocks` eliminado; queda assert_called_no_args |
| `tests/unit/test_product_repository.py` | ✅ | 85/85 |
| `tests/db/test_product_repository.py` | ✅ | 85/85 |
| `tests/unit/test_audit_report_generator.py` | ✅ | `loose_mocks` + `patches_no_autospec` eliminados; 85/85 |
| `tests/unit/test_fabrication_dialogs_coverage.py` | ✅ | `loose_mocks` eliminado (contaba docstring); 85/85 |
| `tests/unit/test_flow_canvas.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_reports_widgets.py` | ✅ | `loose_mocks` eliminado; 70/70 |
| `tests/unit/test_widgets_coverage.py` | ✅ | `loose_mocks` eliminado; `assert_called_no_args` eliminado; 85/85 |
| `tests/unit/test_startup_controller.py` | ✅ | `loose_mocks` + `patches_no_autospec` eliminados; 85/85 |
| `tests/unit/test_enhanced_flow_dialog.py` | ✅ | `assert_called_no_args` eliminado; techo PyQt6 (70/85) |
| `tests/unit/test_reports_infrastructure.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_app_model_coverage.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_machine_controller.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_simulation_events_comprehensive.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_dialogs.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_machine_repository.py` | ✅ | `loose_mocks` + `assert_called_no_args` + `mock_session` eliminados; 100/100 |
| `tests/unit/test_prep_dialogs_coverage.py` | ✅ | `loose_mocks` eliminado; 100/100 (techo PyQt6) |
| `tests/unit/test_preproceso_controller_comprehensive.py` | ✅ | `loose_mocks` eliminado; 100/100 |
| `tests/unit/test_worker_service.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_widgets_dashboard.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_common_dialogs.py` | ✅ | `loose_mocks` eliminado; techo PyQt6 (85/85) |
| `tests/unit/test_backup_controller_comprehensive.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; techo PyQt6 (85/85) |
| `tests/unit/test_timeline_widget.py` | ✅ | `patches_no_autospec` eliminado (exclusión Qt/timeline_widget); techo PyQt6 (85/85) |
| `tests/unit/test_order_list.py` | ✅ | `loose_mocks` eliminado; 70/70 |
| `tests/unit/test_enhanced_flow_presenter.py` | ✅ | `loose_mocks` + `mock_session` eliminados; 85/85 |
| `tests/unit/test_tracking_repository_coverage_fix.py` | ✅ | `loose_mocks` + `mock_session` eliminados; 50/50 |
| `tests/unit/test_tracking_repository_full.py` | ✅ | `loose_mocks` + `mock_session` eliminados; 70/70 |
| `tests/integration/test_configuration_integration.py` | ✅ | `mock_session` eliminado; 50/50 |
| `tests/unit/test_main_window.py` | ✅ | `loose_mocks` + `patches_no_autospec` + `assert_called_no_args` eliminados; 85/85 |
| `tests/e2e/test_backup_audit_e2e.py` | ✅ | `loose_mocks` eliminado; 85/85 |
| `tests/unit/test_gestion_datos_widget.py` | ✅ | `loose_mocks` eliminado; 70/70 |
| `tests/setup/test_conftest_infrastructure.py` | ✅ | `loose_mocks` eliminado; 70/70 |
| `tests/unit/test_report_strategy_comprehensive.py` | ✅ | `patches_no_autospec` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_file_controller.py` | ✅ | `patches_no_autospec` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_worker_controller_comprehensive.py` | ✅ | `patches_no_autospec` corregido (Qt/new excluded); techo PyQt6; 70/100 |
| `tests/unit/test_canvas_widgets.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_app_coverage.py` | ✅ | `loose_mocks` + `assert_called_no_args` eliminados; 85/85 |
| `tests/unit/test_prep_steps_widget.py` | ✅ | `loose_mocks` eliminado; 70/70 |
| `tests/unit/test_hardware_controller.py` | ✅ | `loose_mocks` + `spec_object` eliminados; 85/85 |
| `tests/unit/test_configuration_repository.py` | ✅ | `loose_mocks` + `mock_session` eliminados; 85/85 |
| `tests/integration/test_widgets_integration.py` | ✅ | `loose_mocks` + `mock_session` eliminados; 85/85 |
| `tests/setup/test_iteration_setup.py` | ✅ | `patches_no_autospec` eliminado; 85/85 |
| `tests/e2e/test_machine_workflow.py` | ✅ | `patches_no_autospec` eliminado; 85/85 |
| `tests/e2e/test_product_workflow.py` | ✅ | `patches_no_autospec` eliminado; 85/85 |

---

## Reglas de corrección (aplican a TODOS los archivos)

- **`assert_called_once_with()`** — siempre añadir `assert x.call_count == 1` en la línea anterior
- **`assert_not_called()`** — siempre añadir `assert x.call_count == 0` en la línea anterior
- **`assert_called_with()`** — siempre añadir `assert x.call_count >= 1` en la línea anterior
- **Tests sin assert** — añadir al menos `assert True` si es test de humo, o un assert real si hay retorno
- **`MagicMock()` corregible** — reemplazar por `MagicMock(spec=['método1', 'método2'])` con los métodos mínimos usados
- **`@patch` sin autospec corregible** — añadir `autospec=True` solo si NO es Qt/builtins/OS
- **NUNCA `autospec=True` en clases Qt** — `QDialog`, `QWidget`, `QFileDialog`, etc.
- **`pytestmark`** — añadir `pytestmark = pytest.mark.unit` a nivel de módulo si falta
- **`assert_called_once()` sin args** — reemplazar por `assert_called_once_with(...)` con los args reales
 - **`assert True`** — permitido solo como último recurso en tests de humo y con comentario `# smoke_test: ...`. Preferir siempre un assert observable (estado/retorno/interacción).

---

## Checklist Revisión Fase B (obligatorio antes de marcar ✅)

Un archivo solo se considera **optimizado** y puede marcarse ✅ cuando, además de las reglas anteriores, se cumple esta revisión (referencia: los 6 archivos de Fase B ya revisados a mano).

- [ ] **Mocks con spec:** Todos los mocks de clases del proyecto (servicios, repos, controladores) usan `create_autospec(Clase, instance=True)` o `MagicMock(spec=['método1', 'método2', ...])` con la lista mínima de métodos usados en el test. No dejar `MagicMock()` suelto en dependencias no-Qt.
- [ ] **Patches con autospec:** Todos los `@patch` que no sean Qt/builtins/OS tienen `autospec=True`. Para clases Qt no usar autospec (ver reglas arriba).
- [ ] **Asserts con argumentos reales:** Cada `assert_called_once_with` / `assert_called_with` verifica los argumentos reales que espera el test (o `ANY` solo donde el valor es dinámico). No usar solo `assert_called_once()` sin args.
- [ ] **Call count explícito:** Antes de cada `assert_called_once_with` hay `assert mock.metodo.call_count == 1` (o `>= 1` para `assert_called_with`); antes de `assert_not_called`, `assert ... call_count == 0`.
- [ ] **Docstring de módulo:** El archivo tiene docstring que indica qué módulo(s) cubre y qué aspectos verifica (y, si aplica, decisión de mocking).
- [ ] **Return values en mocks:** Los mocks tienen configurados los `return_value` / `side_effect` necesarios para que el flujo bajo test no dependa de comportamiento implícito del mock.

Solo cuando este checklist está cumplido (y los tests pasan), marcar el archivo con ✅.

---

## GRUPO A — Mayor ganancia (+30 pts o más)

Estos archivos pueden subir 30 puntos con correcciones de tests sin assert y assert_called_no_args.
El patrón es siempre el mismo: añadir `assert x.call_count == N` antes de cada `assert_called_*`.

---

### 1. `tests/unit/test_pila_controller_comprehensive.py` ✅
**Score:** 60 → 100 (+40) | **Techo:** 100 | **Estado:** Completado 2026-03-15

**Antipatrones corregidos:**
- `loose_mocks`: 5 `MagicMock()` sin spec reemplazados por `MagicMock(spec=[...])` con métodos mínimos
- Docstring de módulo añadido con sección "Decisión de mocking"

---

### 2. `tests/unit/test_historial_controller_comprehensive.py` ✅
**Score:** 35 → 65 (+30) | **Techo:** 65 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 8 tests sin assert
- `assert_called_no_args`: 5 instancias de `assert_called_once()` sin args

**Instrucciones:**
1. Buscar los 8 tests sin `assert` — añadir `assert x.call_count >= 1` o assert de retorno
2. Para cada `assert_called_once()` sin args:
   ```python
   # ANTES
   mock_service.metodo.assert_called_once()
   # DESPUÉS
   assert mock_service.metodo.call_count == 1
   mock_service.metodo.assert_called_once_with(<args reales>)
   ```
3. Verificar `pytestmark = pytest.mark.unit`

**Verificación:** `python3 -m pytest tests/unit/test_historial_controller_comprehensive.py -x -q`

---

### 3. `tests/unit/test_ui_controller_comprehensive.py` ✅
**Score:** 35 → 70 (+35) | **Techo:** 100 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 11 tests sin assert
- `assert_called_no_args`: 13 instancias

**Instrucciones:**
1. Buscar los 11 tests sin `assert` — añadir assert de retorno o `assert x.call_count >= 1`
2. Para cada `assert_called_once()` sin args → añadir `assert x.call_count == 1` antes y cambiar a `assert_called_once_with(...)`
3. Verificar `pytestmark = pytest.mark.unit`

**Verificación:** `python3 -m pytest tests/unit/test_ui_controller_comprehensive.py -x -q`

---

### 4. `tests/unit/test_worker_main_window.py` ✅
**Score:** 35 → 70 (+35) | **Techo:** 100 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 9 tests sin assert
- `assert_called_no_args`: 10 instancias

**Instrucciones:**
1. Buscar los 9 tests sin `assert` — añadir assert mínimo
2. Para cada `assert_called_once()` sin args → `assert x.call_count == 1` + `assert_called_once_with(...)`
3. Verificar `pytestmark = pytest.mark.unit`

**Verificación:** `python3 -m pytest tests/unit/test_worker_main_window.py -x -q`

---

### 5. `tests/unit/test_machine_controller_comprehensive.py` ✅
**Score:** 35 → 70 (+35) | **Techo:** 100 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 20 tests sin assert
- `assert_called_no_args`: 5 instancias

**Instrucciones:**
1. Buscar los 20 tests sin `assert` — añadir assert de retorno o interacción
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Verificar `pytestmark = pytest.mark.unit`

**Verificación:** `python3 -m pytest tests/unit/test_machine_controller_comprehensive.py -x -q`

---

### 6. `tests/unit/test_product_dialogs_coverage.py` ✅
**Score:** 35 → 70 (+35) | **Techo:** 65 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 50 tests sin assert (el más alto del proyecto)
- `assert_called_no_args`: 15 instancias

**Instrucciones:**
1. Este archivo tiene 50 tests sin assert — es el mayor impacto individual
2. Para tests de diálogos Qt: añadir `assert widget is not None` o `assert not widget.isHidden()`
3. Para tests de métodos: añadir `assert result is not None` o `assert mock.call_count >= 1`
4. Para cada `assert_called_once()` → patrón estándar

**Verificación:** `python3 -m pytest tests/unit/test_product_dialogs_coverage.py -x -q`

---

### 7. `tests/unit/test_lote_controller_comprehensive.py` ✅
**Score:** 20 → 55 (+35) | **Techo:** 85 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 5 tests sin assert
- `assert_called_no_args`: 5 instancias

**Instrucciones:**
1. Buscar los 5 tests sin assert — añadir assert mínimo
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Verificar `pytestmark = pytest.mark.unit`

**Verificación:** `python3 -m pytest tests/unit/test_lote_controller_comprehensive.py -x -q`

---

### 8. `tests/unit/test_lote_manager_isolated.py` ✅
**Score:** 0 → 45 (+45) | **Techo:** 75 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 8 tests sin assert
- `assert_called_no_args`: 5 instancias
- Falta `pytestmark`

**Instrucciones:**
1. Añadir `pytestmark = pytest.mark.unit` al inicio del módulo (+25 pts base)
2. Buscar los 8 tests sin assert — añadir assert mínimo
3. Para cada `assert_called_once()` sin args → patrón estándar

**Verificación:** `python3 -m pytest tests/unit/test_lote_manager_isolated.py -x -q`

---

### 9. `tests/unit/test_pila_manager_isolated.py` ✅
**Score:** 0 → 45 (+45) | **Techo:** 75 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 3 tests sin assert
- Falta `pytestmark`

**Instrucciones:**
1. Añadir `pytestmark = pytest.mark.unit` al inicio del módulo (+25 pts base)
2. Buscar los 3 tests sin assert — añadir assert mínimo

**Verificación:** `python3 -m pytest tests/unit/test_pila_manager_isolated.py -x -q`

---

### 10. `tests/unit/test_navigation_controller_comprehensive.py` ✅
**Score:** 22 → 60 (+38) | **Techo:** ~70 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 3 tests sin assert
- `assert_called_no_args`: 2 instancias
- `patches_no_autospec`: 4 patches corregibles (no son Qt/builtins)

**Instrucciones:**
1. Buscar los 3 tests sin assert — añadir assert mínimo
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Para los 4 patches corregibles: añadir `autospec=True` (verificar que no son Qt antes)

**Verificación:** `python3 -m pytest tests/unit/test_navigation_controller_comprehensive.py -x -q`

---

### 11. `tests/unit/test_product_controller_preprocesos.py` ✅
**Score:** 27 → 62 (+35) | **Techo:** 57 | **Estado:** Completado 2026-03-15

**Antipatrones corregibles:**
- `tests_without_assert`: 35 tests sin assert
- `assert_called_no_args`: 6 instancias
- `mock_session`: mockea sesión de BD (antipatrón)

**Instrucciones:**
1. Buscar los 35 tests sin assert — mayor prioridad
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Para el mock de sesión: reemplazar por fixture `repos` del conftest si son tests de repositorio

**Verificación:** `python3 -m pytest tests/unit/test_product_controller_preprocesos.py -x -q`

---

## GRUPO B — Ganancia media (+20-29 pts)

---

### 12. `tests/unit/test_session_controller_comprehensive.py` ✅
**Score:** 3 → 85 (+82) | **Techo:** 85 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 2 tests sin assert
- `assert_called_no_args`: 8 instancias
- `patches_no_autospec`: 4 patches corregibles
- Falta `pytestmark`

**Instrucciones:**
1. Añadir `pytestmark = pytest.mark.unit` (+25 pts base — el mayor impacto)
2. Buscar los 2 tests sin assert
3. Para cada `assert_called_once()` sin args → patrón estándar
4. Para los 4 patches: añadir `autospec=True` si no son Qt/builtins

**Verificación:** `python3 -m pytest tests/unit/test_session_controller_comprehensive.py -x -q`

---

### 13. `tests/unit/test_simulation_controller_comprehensive.py` ✅
**Score:** 0 → 85 (+85) | **Techo:** 85 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 9 tests sin assert
- `assert_called_no_args`: 13 instancias
- `patches_no_autospec`: 10 patches corregibles
- Falta `pytestmark`

**Instrucciones:**
1. Añadir `pytestmark = pytest.mark.unit` (+25 pts base)
2. Buscar los 9 tests sin assert
3. Para cada `assert_called_once()` sin args → patrón estándar
4. Para los 10 patches: añadir `autospec=True` si no son Qt/builtins/subprocess

**Verificación:** `python3 -m pytest tests/unit/test_simulation_controller_comprehensive.py -x -q`

---

### 14. `tests/unit/test_features_worker_controller.py` ✅
**Score:** 0 → 85 (+85) | **Techo:** 85 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 7 tests sin assert
- `loose_mocks`: MagicMock() corregibles (no son Qt)
- Falta `pytestmark`

**Instrucciones:**
1. Añadir `pytestmark = pytest.mark.unit` (+25 pts base)
2. Buscar los 7 tests sin assert
3. Para MagicMock() de clases del proyecto: reemplazar por `MagicMock(spec=['método'])` o `create_autospec`

**Verificación:** `python3 -m pytest tests/unit/test_features_worker_controller.py -x -q`

---

### 15. `tests/unit/test_settings_widget.py` ✅
**Score:** 3 → 23 (+20) | **Techo:** 23 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 7 tests sin assert
- `assert_called_no_args`: 4 instancias
- `loose_mocks`: MagicMock() corregibles

**Instrucciones:**
1. Buscar los 7 tests sin assert — para widgets Qt: `assert widget is not None`
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Para MagicMock() de servicios (no Qt): reemplazar por `create_autospec`

**Verificación:** `python3 -m pytest tests/unit/test_settings_widget.py -x -q`

---

### 16. `tests/unit/test_report_controller_comprehensive.py` ✅
**Score:** 3 → 23 (+20) | **Techo:** 23 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 8 tests sin assert
- `assert_called_no_args`: 4 instancias
- `loose_mocks`: MagicMock() corregibles (39 total, algunos inevitables Qt)

**Instrucciones:**
1. Buscar los 8 tests sin assert
2. Para cada `assert_called_once()` sin args → patrón estándar
3. Para MagicMock() de servicios (no Qt): reemplazar por `create_autospec`
4. Nota: los 41 patches son mayoritariamente Qt — NO añadir autospec a esos

**Verificación:** `python3 -m pytest tests/unit/test_report_controller_comprehensive.py -x -q`

---

### 17. `tests/unit/test_camera_config_dialog.py` ✅
**Score:** 15 → 35 (+20) | **Techo:** 35 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 4 tests sin assert
- `assert_called_no_args`: 11 instancias
- `patches_no_autospec`: 8 patches corregibles

**Instrucciones:**
1. Buscar los 4 tests sin assert
2. Para cada `assert_called_once()` sin args → patrón estándar (11 instancias — mayor impacto)
3. Para los 8 patches: añadir `autospec=True` si no son Qt/builtins

**Verificación:** `python3 -m pytest tests/unit/test_camera_config_dialog.py -x -q`

---

## GRUPO C — Ganancia menor (+5-18 pts) pero score final alto

---

### 18. `tests/unit/test_calculation_controller_comprehensive.py` ✅
**Score:** 37 → 55 (+18) | **Techo:** 55 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `loose_mocks`: 13 MagicMock() corregibles (los que no son Qt)

**Instrucciones:**
1. Identificar los MagicMock() que NO son widgets Qt
2. Para mocks de servicios/repos: reemplazar por `MagicMock(spec=['método'])` o `create_autospec`
3. Los MagicMock() de `CalculateTimesWidget` y similares son inevitables — no tocar

**Verificación:** `python3 -m pytest tests/unit/test_calculation_controller_comprehensive.py -x -q`

---

### 19. `tests/controllers/product/test_product_manager.py` ✅
**Score:** 40 → 55 (+15) | **Techo:** 55 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 3 tests sin assert
- `loose_mocks`: 7 MagicMock() corregibles

**Instrucciones:**
1. Buscar los 3 tests sin assert — añadir assert mínimo
2. Para MagicMock() de clases del proyecto: reemplazar por `create_autospec` o `MagicMock(spec=[...])`

**Verificación:** `python3 -m pytest tests/controllers/product/test_product_manager.py -x -q`

---

### 20. `tests/unit/test_create_fabricacion_dialog.py` ✅
**Score:** 10 → 20 (+10) | **Techo:** 20 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 2 tests sin assert

**Instrucciones:**
1. Buscar los 2 tests sin assert — añadir `assert widget is not None` o assert de retorno

**Verificación:** `python3 -m pytest tests/unit/test_create_fabricacion_dialog.py -x -q`

---

### 21. `tests/unit/test_create_dialog.py` ✅
**Score:** 37 → 42 (+5) | **Techo:** 42 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 2 tests sin assert
- `assert_called_no_args`: 1 instancia

**Instrucciones:**
1. Buscar los 2 tests sin assert
2. Para el `assert_called_once()` sin args → patrón estándar

**Verificación:** `python3 -m pytest tests/unit/test_create_dialog.py -x -q`

---

### 22. `tests/e2e/test_backup_audit_e2e.py` ✅
**Score:** 31 → 36 (+5) | **Techo:** 36 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `assert_called_no_args`: 3 instancias

**Instrucciones:**
1. Para cada `assert_called_once()` sin args → patrón estándar

**Verificación:** `python3 -m pytest tests/e2e/test_backup_audit_e2e.py -x -q`

---

### 23. `tests/unit/test_bitacora_dialog.py` ✅
**Score:** 7 → 12 (+5) | **Techo:** 12 | **Estado:** Completado 2026-03-16

**Antipatrones corregibles:**
- `tests_without_assert`: 3 tests sin assert
- `assert_called_no_args`: 1 instancia

**Instrucciones:**
1. Buscar los 3 tests sin assert — añadir assert mínimo
2. Para el `assert_called_once()` sin args → patrón estándar

**Verificación:** `python3 -m pytest tests/unit/test_bitacora_dialog.py -x -q`

---

## GRUPO D — Archivos en techo pero con antipatrones menores

Estos archivos ya están en su techo real (sin ganancia de score), pero tienen antipatrones
que conviene corregir por calidad del código. Trabajar después de completar los grupos A-C.

| Archivo | Score | Antipatrón menor |
|---------|-------|-----------------|
| `test_calculate_times_widget.py` | 85 | `spec=object` (21 instancias en el proyecto) |
| `test_camera_manager_full.py` | 85 | `spec=object` |
| `test_charts_container.py` | 85 | `spec=object` |
| `test_tracking_assignment_service.py` | 82 | `assert_called_once()` sin args |
| `test_preparation_service.py` | 80 | `loose_mocks` menores |
| `test_backup_restore_dialog.py` | 70 | `tests_without_assert`, `assert_called_no_args` |
| `test_material_manager.py` | 70 | `loose_mocks` menores |
| `test_backup_service.py` | 64 | `tests_without_assert`, `assert_called_no_args` |
| `test_password_service.py` | 62 | `assert_called_no_args` |
| `test_machine_service.py` | 61 | `loose_mocks`, `assert_called_no_args` |
| `test_preproceso_controller_comprehensive.py` | 57 | `loose_mocks`, `tests_without_assert` |
| `test_preproceso_repository.py` | 56 | `loose_mocks`, `assert_called_no_args`, `mock_session` |
| `test_security_improvements.py` | 55 | `tests_without_assert` |
| `test_dialogs_flow.py` | 55 | `loose_mocks` |
| `test_app_model_coverage.py` | 55 | `loose_mocks` |
| `test_worker_service.py` | 49 | `loose_mocks` |
| `test_workers_widget.py` | 50 | `loose_mocks`, `tests_without_assert` |
| `test_common_dialogs.py` | 50 | `loose_mocks` |
| `test_iteration_repository.py` | 65 | `loose_mocks` |
| `test_products_widget.py` | 65 | `loose_mocks` |

---

## GRUPO E — Archivos con score muy bajo (requieren reescritura)

Estos archivos tienen score < 20 y requieren reescritura completa, no correcciones puntuales.
Abordar solo después de completar los grupos A-D.

| Archivo | Score | Techo | Problema principal |
|---------|-------|-------|-------------------|
| `test_worker_controller_comprehensive.py` | 0 | 36 | 24 tests sin assert, 44 loose mocks, 37 patches sin autospec |
| `test_simulation_events_comprehensive.py` | 0 | 0 | Sin pytestmark, 29 loose mocks, 2 tests sin assert |
| `test_app_model.py` | 3 | 3 | 12 loose mocks, 17 tests sin assert |
| `test_timeline_widget.py` | 0 | 0 | 10 loose mocks, sin pytestmark |
| `test_ui_scaler.py` | 0 | 0 | 8 loose mocks, sin pytestmark |
| `test_flow_builder_service.py` | 0 | 0 | Sin assert_called, sin pytestmark |
| `test_flow_simulation_service.py` | 15 | 15 | Sin assert_called, sin pytestmark |
| `test_scheduler_logic.py` | 0 | 0 | 6 loose mocks, 3 tests sin assert |
| `test_security_phase2_integration.py` | 0 | 0 | 15 loose mocks, 1 test sin assert |
| `test_report_strategy_comprehensive.py` | 0 | 0 | 4 loose mocks, 1 test sin assert |
| `test_machines_widget.py` | 0 | 0 | 6 loose mocks, 1 test sin assert |
| `test_fabrication_dialogs.py` | 0 | 9 | 16 loose mocks, 5 tests sin assert |
| `test_features_worker_controller.py` | 0 | 25 | 15 loose mocks, 7 tests sin assert |

---

## Registro de Completados

Actualizar esta tabla después de cada sesión:

| Archivo | Score antes | Score después | Fecha | Notas |
|---------|-------------|---------------|-------|-------|
| `test_label_manager.py` | 0 | 55 (techo 85) | 2026-03-15 | Reescrito completo |
| `test_schedule_controller_comprehensive.py` | 0 | 43 (techo 85) | 2026-03-15 | Reescrito completo |
| `test_calculation_controller_comprehensive.py` | 17 | 37 (techo 55) | 2026-03-15 | Corregidos 14 tests sin assert |
| `test_pila_controller_comprehensive.py` | 75 | 100 (techo 100) | 2026-03-15 | loose_mocks corregidos — score 100/100 |
| `test_historial_controller_comprehensive.py` | 35 | 65 (techo 65) | 2026-03-15 | Corregidos assert_called_no_args y tests sin assert |
| `test_ui_controller_comprehensive.py` | 35 | 70 (techo 100) | 2026-03-15 | Corregidos assert_called_once() y tests sin assert |
| `test_worker_main_window.py` | 35 | 70 (techo 100) | 2026-03-15 | Corregidos tests sin assert |
| `test_machine_controller_comprehensive.py` | 35 | 70 (techo 100) | 2026-03-15 | Corregidos assert_called_once() y tests sin assert |
| `test_lote_controller_comprehensive.py` | 20 | 55 (techo 85) | 2026-03-15 | Corregidos assert_called_once() y tests sin assert |
| `test_lote_manager_isolated.py` | 0 | 45 (techo 75) | 2026-03-15 | Añadido pytestmark, create_autospec, tests sin assert |
| `test_pila_manager_isolated.py` | 0 | 45 (techo 75) | 2026-03-15 | Añadido pytestmark, create_autospec, tests sin assert |
| `test_navigation_controller_comprehensive.py` | 22 | 60 (techo ~70) | 2026-03-15 | Corregidos assert_called(), autospec en UIScaler patches |
| `test_product_dialogs_coverage.py` | 35 | 70 (techo 65) | 2026-03-15 | Corregidos 36 tests sin assert, assert_called_once() sin args |
| `test_product_controller_preprocesos.py` | 27 | 62 (techo 57) | 2026-03-15 | Corregidos 35 tests sin assert, 6 assert_called_once() sin args |
| `test_library_panel.py` | skip | 14 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_fabrication_dialogs_coverage.py` | skip | 20 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_dialog_integration_smoke.py` | skip | 29 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_reports_widgets.py` | skip | 45 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_canvas_widgets_coverage.py` | skip | 34 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_define_flow_dialog_edge.py` | skip | 18 tests pasando | 2026-03-15 | Reescrito desde stub vacío |
| `test_flow_builder_service.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring módulo, mocks con spec para workers |
| `test_machines_widget.py` | 0 | optimizado | 2026-03-17 | pytestmark módulo, ctrl/get_distinct_machine_processes, mocks spec, assert en test sin tabla |
| `test_simulation_events_comprehensive.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, mocks spec (engine/gestor/linea), call_count antes de assert_called |
| `test_timeline_widget.py` | 0 | optimizado | 2026-03-17 | pytestmark módulo, docstring, decisiones auditoría con spec, call_count antes de .called |
| `test_ui_scaler.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, mocks widget/screen/rect con spec, call_count antes de assert_called_once |
| `test_worker_validation_service.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, spec qr_scanner/trabajo/paso, call_count |
| `test_report_strategy_comprehensive.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, mock_schedule_config.BREAKS, call_count, mock_model spec |
| `test_qr_scanner.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, mock_video_capture spec, call_count |
| `test_security_phase2_integration.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, call_count antes assert_called/assert_not_called |
| `test_startup_controller.py` | 0 | optimizado | 2026-03-17 | pytestmark, docstring, call_count antes assert_any_call |
| Archivos 38-53 | — | optimizados | 2026-03-17 | pytestmark, docstring, call_count/spec según checklist Fase B |
| `test_settings_widget.py` (b4) | 3 | 85 (techo) | 2026-03-16 | call_count antes assert_not_called; pytest verde 26 tests |
| `test_report_controller_comprehensive.py` (b5) | 3 | 53 | 2026-03-16 | call_count antes show_message/get_product_iterations/mock_handle; pytest 28 passed |
