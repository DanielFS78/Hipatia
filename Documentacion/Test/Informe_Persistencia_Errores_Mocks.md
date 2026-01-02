# Informe de Errores Persistentes y Estrategia de Corrección

**Fecha:** 2026-01-01
**Asunto:** Análisis de los "27 Errores" (Mocks Laxos) persistentes tras la refactorización.

## 1. Situación Actual y Problema Detectado
El usuario reporta que "siguen habiendo 27 errores" tras el intento de corregir `test_widgets_integration.py`.
El análisis automatizado (`analyze_loose_mocks.py`) muestra:

*   **`tests/integration/test_widgets_integration.py`**: 5 mocks laxos detectados (Antes eran ~27).
    *   *Causa:* Aunque el `AppController` se mockea estrictamente, los objetos `mock_model`, `mock_view`, `mock_db` y `mock_schedule` se instanciaron como `MagicMock()` genéricos (laxos) en el `setup`.
*   **`tests/unit/test_widgets.py`**: 19 mocks laxos detectados.
    *   *Causa:* Similar al caso anterior, las dependencias inyectadas (`model`, `db`) no tienen `spec=Class`.

Es posible que la cifra de "27" referida por el usuario corresponda a la suma de problemas en estos archivos o a un archivo específico no abordado (ej. `test_materials_repository` tiene 29). Sin embargo, nos centraremos en **eliminar radicalmente los mocks laxos** de los widgets.

## 2. Acciones Realizadas (Intentos Previos)
Se reescribió `tests/integration/test_widgets_integration.py` para pasar de tests de "mocks vs mocks" a tests de integración con objetos reales (`RealAppController` + `RealWidgets`).
*   **Resultado Positivo**: Los tests ahora verifican lógica real de cableado (wiring) y pasan exitosamente (2 tests OK).
*   **Fallo**: Se mantuvieron definiciones laxas para objetos auxiliares (`mock_model = MagicMock()`), lo que impide alcanzar el estándar de "Cero Errores/Warnings" en validaciones estrictas.

## 3. Plan de Corrección Definitiva

Para asegurar que los tests sean 100% robustos y strictos:

1.  **Strict Mocking Total en Setup**:
    *   Sustituir `MagicMock()` por `MagicMock(spec=ClaseReal)` para **TODAS** las dependencias:
        *   `mock_model = MagicMock(spec=AppModel)`
        *   `mock_db = MagicMock(spec=DatabaseManager)`
        *   `mock_view = MagicMock(spec=MainView)`
        *   `mock_schedule = MagicMock(spec=ScheduleConfig)`
    
2.  **Refactorización de `test_widgets_integration.py`**:
    *   Actualizar el fixture `setup_integration` para usar estos mocks estrictos.
    
3.  **Refactorización de `test_widgets.py`**:
    *   Revisar y actualizar todas las instanciaciones de mocks.

4.  **Verificación**:
    *   Ejecutar `analyze_loose_mocks.py` nuevamente para confirmar que el conteo baja a 0 en estos archivos.
    *   Ejecutar `pytest` para asegurar que el mocking estricto no rompe los tests (detectando accesos a atributos inexistentes).

Esta estrategia garantiza que no solo la lógica sea correcta, sino que la arquitectura de pruebas cumpla con los estándares de calidad más exigentes.
