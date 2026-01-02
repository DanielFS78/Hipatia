# Informe de Análisis de Fallo y Regresión (Fallo de Arranque Post-Refactorización)

## 1. Resumen Ejecutivo
El programa fallaba al iniciar debido a un error `AttributeError: 'ReportesWidget' object has no attribute 'search_entry'`.
Este error fue causado por código legado en el `AppController` que intentaba conectar señales a componentes internos del `ReportesWidget` que fueron eliminados o renombrados durante la refactorización de la Fase 3.

A pesar de contar con una suite de tests automatizados (`run_tests`) que reportaba éxito total, este error crítico no fue detectado. Este informe detalla las causas técnicas del fallo, la razón por la cual los tests dieron un falso positivo y las recomendaciones para evitar que esto se repita.

## 2. Análisis del Fallo Técnico
El `AppController` contenía el método `_connect_reportes_signals` (y otros métodos auxiliares como `_on_report_search_changed`) que asumían una estructura interna antigua del `ReportesWidget`:

```python
# CÓDIGO CAUSANTE DEL ERROR (Ahora eliminado)
def _connect_reportes_signals(self):
    reportes_page = self.view.pages.get("reportes")
    if isinstance(reportes_page, ReportesWidget):
        # ERROR: search_entry ya no existe en ReportesWidget v2
        reportes_page.search_entry.textChanged.connect(self._on_report_search_changed)
        reportes_page.results_list.itemClicked.connect(self._on_report_result_selected)
```

Durante la **Fase 3**, el `ReportesWidget` fue refactorizado para ser más modular, delegando la búsqueda a un sub-componente `SmartSearchWidget` y manejando sus propias conexiones internas. Sin embargo, el `AppController` no fue actualizado para reflejar este cambio, creando una discrepancia fatal en tiempo de ejecución.

## 3. ¿Por qué los Tests Pasaron? (Análisis de la Suite de Pruebas)
Es alarmante que una suite de tests pase al 100% mientras el programa no arranca. Tras analizar `tests/unit/test_app_controller.py`, se identificó la causa raíz del falso positivo: **Aislamiento Excesivo en los Tests Unitarios**.

### El Test Culpable
El test `test_connect_signals_calls_submethods` en `tests/unit/test_app_controller.py` tiene el propósito de verificar que las señales se conecten correctamente. Sin embargo, su implementación es deficiente para detectar este tipo de regresiones:

```python
# Excerpt from tests/unit/test_app_controller.py
def test_connect_signals_calls_submethods(self, controller):
    # ... setup mocks ...
    
    # MOCK INCOMPLETO: Solo se define 'gestion_datos' en las páginas de la vista
    mock_gestion = MagicMock()
    controller.view.pages = {"gestion_datos": mock_gestion}
    
    controller.connect_signals()
    # ... aserciones ...
```

### La Cadena de Fallos en el Test:
1.  **Mock Incompleto**: El test configura `controller.view.pages` conteniendo *solamente* la página "gestion_datos".
2.  **Código Omitido**: Al ejecutarse `controller.connect_signals()`, el método problemático `_connect_reportes_signals` se ejecuta.
3.  **Condición de Salida**: Dentro de `_connect_reportes_signals`, se intenta obtener la página "reportes": `reportes_page = self.view.pages.get("reportes")`.
4.  **Silencio del Error**: Como "reportes" no está en el diccionario del mock, `reportes_page` es `None`. El bloque `if isinstance(...)` se salta por completo.
5.  **Resultado**: El código erróneo nunca se ejecutó durante el test. El test pasó porque verificó solo lo que *había* configurado, ignorando el resto del sistema.

Esto demonstra un peligro común del testing unitario con mocks agresivos: **Se prueba la implementación del mock, no la integración real.**

## 4. Soluciones Aplicadas
Se ha realizado una limpieza inmediata del código en `AppController` para eliminar la dependencia a los atributos inexistentes.
- Se eliminó el contenido obsoleto de `_connect_reportes_signals`.
- Se eliminaron los métodos `_on_report_search_changed` y `_on_report_result_selected`.
- El programa ahora delega correctamente la lógica de UI al `ReportesWidget` refactorizado.

## 5. Recomendaciones para la Suite de Tests (Plan de Mejora)
Para garantizar que "Tests Pasados = Programa Funcional", se deben implementar los siguientes cambios en la estrategia de testing:

### A. Implementar Tests de Integración de UI (Smoke Tests)
No basta con tests unitarios aislados. Se necesita un test de "Smoke" que instancie la aplicación real (o una versión muy cercana) y verifique que arranca y conecta sus componentes.
*   **Acción**: Crear un test que instancie `MainView` y `AppController` con sus dependencias reales (o mocks de base de datos solamente) y llame a `connect_signals()`. Si este test existiera, habría fallado inmediatamente.

### B. Mocks "Estrictos" (Strict Mocks)
Los mocks actuales permiten acceder a cualquier atributo (devuelven otro MagicMock). Se deben usar `spec=ClaseReal` al crear mocks.
*   **Acción**: Al crear un mock para `ReportesWidget`, usar `MagicMock(spec=ReportesWidget)`. Si el código de prueba intenta acceder a `.search_entry` y este no existe en la clase real, el test fallará, alertando de la discrepancia.

### C. Verificar Cobertura de Ramas (Branch Coverage)
El test unitario actual no cubría la rama dentro del `if isinstance(...)`.
*   **Acción**: Revisar los reportes de cobertura (`coverage.py`). Asegurarse de que los tests pasen por todas las líneas lógicas de configuración inicial.

---
**Estado Actual**: El código ha sido corregido y el programa debería arrancar correctamente. Se recomienda ejecutar los tests de integración e implementar las mejoras sugeridas en la Fase 5.
