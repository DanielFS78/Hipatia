# Informe Pre-Fase 1 — Corrección de Tests Críticos

**Fecha:** 2026-03-14  
**Estado:** EN EJECUCIÓN

## Métricas Baseline

- Tests sin assert detectados: **164** (en 61 archivos)
- Score de calidad: **34.1/100**
- Tests totales: **2384**
- Cobertura global: **88.20%**

> Nota: el analizador `test_quality_analyzer.py` reportaba 583 — la diferencia se debe a que
> el analizador también cuenta tests que solo tienen `pytest.raises` sin assert adicional,
> o tests con `assert_called*` en ramas no alcanzadas. El análisis AST directo da 164 tests
> completamente vacíos de cualquier verificación.

## Clasificación de los 164 tests

### Tipo A — Tests de humo (verifican que no explota, necesitan assert mínimo): ~90 tests
Ejemplos: `test_connect_signals_*`, `test_paint_event_*`, `test_accept_reject`

### Tipo B — Tests incompletos (llaman al código pero no verifican nada): ~60 tests
Ejemplos: `test_no_gestion_page`, `test_no_settings_page`, `test_update_*`

### Tipo C — Tests vacíos o de debugging (candidatos a eliminar): ~14 tests
Archivos: `tests/debugging/`, `tests/verification/`

## Plan de Ejecución (por lotes)

| Lote | Archivo | Tests | Tipo |
|------|---------|-------|------|
| 1 | test_calculation_controller_comprehensive.py | 15 | A/B |
| 2 | test_settings_widget.py | 11 | A/B |
| 3 | test_flow_canvas.py | 9 | A |
| 4 | test_product_dialogs_coverage.py | 8 | A/B |
| 5 | test_ui_signals_controller_comprehensive.py | 8 | B |
| 6 | test_fabrication_dialogs.py | 7 | A |
| 7 | test_worker_controller_comprehensive.py | 7 | B |
| 8 | test_machine_controller_comprehensive.py | 6 | A/B |
| 9 | test_visual_effects.py | 5 | A |
| 10 | Resto (archivos con 1-5 tests) | ~88 | A/B/C |

## Orden de Corrección

1. Archivos de controladores (mayor impacto en score)
2. Archivos de widgets UI
3. Archivos de debugging (evaluar eliminación)
4. Archivos de verificación (evaluar eliminación)
