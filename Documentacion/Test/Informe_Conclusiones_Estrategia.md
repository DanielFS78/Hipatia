# Informe de Conclusiones y Estrategia de Corrección

**Fecha:** 1 de Enero de 2026
**Asunto:** Estrategia integral para la eliminación de "Errores" (Mocks Laxos) y robustecimiento de tests.

## 1. Conclusiones del Análisis de Documentación

Tras revisar toda la documentación existente en `documentacion/Test`, se extraen las siguientes conclusiones clave:

1.  **Diagnóstico Crítico: Fatiga de Mocks**:
    *   El problema recurrente de "los tests pasan pero la app falla" se debe al uso masivo de `MagicMock()` sin especificaciones (`spec`).
    *   Hay más de **1000 instancias** de estos mocks en el proyecto.
    *   Los archivos más críticos son los tests de Controladores (`test_app_controller.py`) y Widgets (`test_widgets.py`), ya que son los que tienen mayor superficie de cambio en la UI.

2.  **Origen de los "27 Errores" Persistentes**:
    *   Se ha identificado que, aunque se refactorizó la lógica principal de `test_widgets_integration.py`, se dejaron **mocks auxiliares laxos** (Model, View, DB) en el `setup`.
    *   El usuario exige una limpieza **total** en estos archivos antes de proceder con el resto.
    *   Es probable que el número "27" también haga referencia a archivos como `test_app_controller_historial.py` (29 mocks) o `test_widgets.py` (19 mocks restantes), que requieren el mismo tratamiento.

3.  **Validación de la Nueva Estrategia**:
    *   La refactorización a **Tests de Integración con Objetos Reales** (aplicada en `test_widgets_integration.py`) ha demostrado ser efectiva para verificar el cableado real (Signals -> Slots).
    *   La refactorización a **Mocks Estrictos** (`spec=Classe`) aplicada parcialmente ha revelado bugs reales (como nombres de métodos incorrectos).

## 2. Estrategia de Corrección (Plan de Acción)

Para cerrar definitivamente la brecha de fiabilidad y eliminar los mensajes de error/advertencia del usuario, se procederá con el siguiente plan innegociable:

### Fase 1: Tolerancia Cero en Widgets (Inmediato)
**Objetivo**: Convertir `test_widgets.py` y `test_widgets_integration.py` en "Zonas Libres de Mocks Laxos".

*   **Acción 1**: Instanciar dependencias (`AppModel`, `DatabaseManager`, `ScheduleConfig`) usando estrictamente `MagicMock(spec=ClaseReal)`.
*   **Acción 2**: En los tests unitarios (`test_widgets.py`), verificar que cada atributo accedido exista realmente en la clase mockeada.
*   **Acción 3**: Ejecutar el script `analyze_loose_mocks.py` para certificar matemáticamente que el conteo en estos archivos es **0**.

### Fase 2: Extensión a Controladores (Siguiente Paso)
Una vez saneados los widgets, aplicar la misma medicina a los controladores críticos identificados en el análisis de riesgos:
*   `test_app_controller.py`
*   `test_product_controller.py`

### Fase 3: Integración Continua Local
*   Cada cambio debe validarse no solo con `pytest` (que pase el test), sino con el script de análisis para asegurar que no se introduzca nueva deuda técnica.

## 3. Próximos Pasos (Inmediato)
Se procederá a ejecutar la **Fase 1** inmediatamente, corrigiendo `test_widgets_integration.py` y `test_widgets.py` para cumplir con la exigencia del usuario.
