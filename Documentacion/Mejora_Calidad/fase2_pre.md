# Informe Pre-Fase 2 — Lote 1: Archivos con Score 0/100

**Fecha:** 2026-03-14  
**Estado:** EN PROGRESO

## Objetivo del lote

Subir de 0/100 a ≥50/100 los 5 archivos con peor score del dashboard.

## Archivos a modificar

| Archivo | Score actual | Antipatrones detectados |
|---------|-------------|------------------------|
| `test_backup_controller.py` | 0/100 | 6 MagicMock sueltos, 4 tests sin assert, 3 assert_called_once sin args |
| `test_backup_controller_comprehensive.py` | 0/100 | 7 MagicMock sueltos, 11 tests sin assert, 15 assert_called_once sin args |
| `test_backup_integration.py` | 0/100 | 7 MagicMock sueltos, 2 tests sin assert, 3 assert_called_once sin args |
| `test_controller_interface.py` | 0/100 | 9 MagicMock sueltos, sin assert_called* en archivo de controlador |
| `test_app_model_coverage.py` | 0/100 | 11 MagicMock sueltos, 1 test sin assert, 6 assert_called_once sin args |

## Cambios planificados por archivo

### test_backup_controller.py
- Añadir `@pytest.mark.unit` a la clase
- Añadir docstring de módulo y clase
- Convertir fixtures `mock_db`, `mock_view`, `mock_backup_service`, `mock_audit_logger` a `create_autospec`
- Añadir `autospec=True` a los `@patch` / `with patch()`
- Completar asserts en tests que solo verifican llamadas sin argumentos

### test_backup_controller_comprehensive.py
- Ya tiene `@pytest.mark.unit` en algunas clases ✓
- Ya tiene docstrings ✓
- Convertir `MagicMock()` sueltos en fixtures a `create_autospec`
- Añadir `autospec=True` a los `with patch()` donde falte
- Reemplazar `assert_called_once()` por `assert_called_once_with(...)` donde los args sean conocidos

### test_backup_integration.py
- Añadir `@pytest.mark.integration` 
- Añadir docstring de módulo
- Convertir mocks sueltos a `create_autospec`
- Completar asserts en `test_integration_settings_button_signal`

### test_controller_interface.py
- Añadir `@pytest.mark.unit`
- Añadir docstring de módulo y clase
- Convertir `MagicMock()` sueltos a `create_autospec`
- Añadir `assert_called_*` en los tests de `initialize()` y `cleanup()`

### test_app_model_coverage.py
- Añadir `@pytest.mark.unit`
- Añadir docstring de módulo
- Convertir `MagicMock()` sueltos a `create_autospec` donde sea posible
- Completar asserts faltantes

## Reglas aplicadas
- No modificar código fuente
- Máximo 5 archivos por iteración
- Verificar con `pytest` que 0 tests fallan tras los cambios
- Consultar `testing_antipatrones` y `testing_fixtures_y_mocks`
