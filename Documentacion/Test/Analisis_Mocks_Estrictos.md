# Informe de Auditoría de Tests: Transición a Mocks Estrictos

**Fecha:** 1 de Enero de 2026
**Ubicación:** `documentacion/Test/Analisis_Mocks_Estrictos.md`
**Estado:** Pendiente de Refactorización Masiva

## 1. Resumen de la Situación
A raíz del fallo crítico detectado en el **Informe de Implementación del Smoke Test**, donde la suite de pruebas pasó exitosamente mientras la aplicación fallaba al inicio, se ha realizado una auditoría completa del código de pruebas.

El problema raíz fue el uso de "Mocks Permisivos" (Luss Mocks). Un `MagicMock` por defecto permite acceder a *cualquier* atributo (ej: `page.search_entry`), devolviendo otro mock en lugar de lanzar un error si el atributo no existe en la clase real. Esto ocultó el hecho de que `search_entry` había sido eliminado en el código de producción.

## 2. Resultados de la Auditoría
Se ha ejecutado un script de análisis estático (`scripts/analyze_loose_mocks.py`) sobre la carpeta `tests/`.

*   **Total de Mocks Permisivos Detectados:** 1139
*   **Archivos Afectados:** 56 archivos de test

### Archivos Críticos (Mayor Deuda Técnica)
Estos archivos contienen la mayor cantidad de mocks inseguros y deben ser priorizados:

| Archivo | Mocks Permisivos | Prioridad |
|:---|:---:|:---:|
| `tests/unit/test_database_manager_migrations.py` | 116 | Media |
| `tests/repositories/test_material_repository.py` | 83 | Media |
| `tests/unit/test_app_controller_navigation.py` | 76 | Alta |
| `tests/unit/test_widgets.py` | 56 | Alta |
| `tests/unit/test_dialogs.py` | 49 | Alta |
| `tests/unit/test_app_controller_comprehensive.py` | 42 | Alta |
| `tests/unit/test_app_controller_preprocesos.py` | 40 | Alta |
| `tests/unit/test_features_worker_controller.py` | 36 | Alta |

*(Ver anexo para la lista completa)*

## 3. Plan de Acción: Adopción de Mocks Estrictos

Para asegurar la robustez de la suite de tests y evitar falsos positivos futuros, se debe refactorizar el código de prueba siguiendo estas reglas:

### Regla de Oro
**Todo Mock que simule una clase compleja (Widgets, Controladores, Repositorios) debe usar el argumento `spec`.**

### Ejemplo de Refactorización

#### Código Inseguro (Actual)
```python
# test_app_controller.py
from unittest.mock import MagicMock

def test_example(controller):
    # Este mock acepta CUALQUIER COSA. 
    # Si reportes_page.search_entry se elimina de la clase real, este test NO fallará.
    mock_page = MagicMock() 
    controller.view.pages.get.return_value = mock_page
    
    controller.connect_signals() # Accede a page.search_entry (que ya no existe) -> El mock se lo traga.
```

#### Código Seguro (Propuesto)
```python
# test_app_controller.py
from unittest.mock import MagicMock
from ui.widgets import ReportesWidget # Importar la clase real

def test_example(controller):
    # Al usar spec, el mock valida contra la estructura de la clase real.
    mock_page = MagicMock(spec=ReportesWidget) 
    controller.view.pages.get.return_value = mock_page
    
    controller.connect_signals() 
    # Si el código intenta acceder a 'search_entry' y NO existe en ReportesWidget,
    # el test fallará inmediatamente con AttributeError.
```

## 4. Estrategia de Implementación
Dada la magnitud de los cambios (1139 instancias), se recomienda proceder por bloques:

1.  **Bloque 1: Controladores de UI (Alta Prioridad)**
    *   Refactorizar `tests/unit/test_app_controller*.py`.
    *   Estos son los más propensos a fallar por cambios en la interfaz gráfica.
    
2.  **Bloque 2: Widgets y Diálogos (Alta Prioridad)**
    *   Refactorizar `test_widgets.py`, `test_dialogs.py`.
    
3.  **Bloque 3: Repositorios y Base de Datos (Media Prioridad)**
    *   Refactorizar tests de repositorios. Aunque menos volátiles, el tipado estricto ayuda a detectar cambios en modelos de BD.

4.  **Bloque 4: Integración (Baja Prioridad)**
    *   Los tests de integración a menudo usan datos reales o mocks parciales, revisar caso por caso.

## 5. Anexo: Lista Completa de Archivos Afectados

```text
tests/e2e/test_dialogs_e2e.py: 5
tests/e2e/test_main_window_flows.py: 5
tests/integration/test_app_startup_integration.py: 11
tests/integration/test_configuration_integration.py: 1
tests/integration/test_dialogs_integration.py: 9
tests/integration/test_widgets_integration.py: 27
tests/repositories/test_material_repository.py: 83
tests/unit/test_app_controller.py: 32
tests/unit/test_app_controller_backup.py: 5
tests/unit/test_app_controller_basics.py: 7
tests/unit/test_app_controller_chunking.py: 4
tests/unit/test_app_controller_comprehensive.py: 42
tests/unit/test_app_controller_exceptions.py: 5
tests/unit/test_app_controller_export.py: 10
tests/unit/test_app_controller_fabricaciones.py: 6
tests/unit/test_app_controller_files.py: 8
tests/unit/test_app_controller_hardware.py: 13
tests/unit/test_app_controller_historial.py: 29
tests/unit/test_app_controller_navigation.py: 76
tests/unit/test_app_controller_optimization.py: 9
tests/unit/test_app_controller_preprocesos.py: 40
tests/unit/test_app_controller_settings.py: 31
tests/unit/test_app_controller_simulation_extra.py: 10
tests/unit/test_app_controller_ui_signals.py: 30
tests/unit/test_app_controller_visual_editor.py: 17
tests/unit/test_app_controller_worker_interface.py: 4
tests/unit/test_app_coverage.py: 3
tests/unit/test_app_model.py: 26
tests/unit/test_app_model_coverage.py: 21
tests/unit/test_configuration_repository.py: 2
tests/unit/test_database_manager_core.py: 4
tests/unit/test_database_manager_delegated.py: 39
tests/unit/test_database_manager_full.py: 21
tests/unit/test_database_manager_migrations.py: 116
tests/unit/test_dialogs.py: 49
tests/unit/test_dialogs_flow.py: 3
tests/unit/test_features_pila_controller.py: 34
tests/unit/test_features_worker_controller.py: 36
tests/unit/test_iteration_repository.py: 2
tests/unit/test_machine_repository.py: 10
tests/unit/test_main_window.py: 3
tests/unit/test_pila_controller_lotes.py: 34
tests/unit/test_pila_controller_simulation.py: 12
tests/unit/test_preproceso_repository.py: 2
tests/unit/test_product_controller.py: 34
tests/unit/test_product_repository.py: 1
tests/unit/test_reports_widgets.py: 2
tests/unit/test_tracking_exceptions.py: 25
tests/unit/test_tracking_repository_coverage_fix.py: 1
tests/unit/test_tracking_repository_full.py: 3
tests/unit/test_tracking_repository_stats_export.py: 1
tests/unit/test_widgets.py: 56
tests/unit/test_widgets_coverage.py: 30
tests/unit/test_widgets_dashboard.py: 20
tests/unit/test_worker_controller.py: 15
tests/unit/test_worker_controller_admin.py: 15
```

---
Este documento sirve como hoja de ruta para la refactorización de la calidad del código de pruebas del proyecto.
