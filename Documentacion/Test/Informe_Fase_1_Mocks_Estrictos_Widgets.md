# Informe de Implementación de Mocks Estrictos - Fase 1: Widgets

> [!NOTE]
> **Estado**: Completado
> **Fecha**: 01/01/2026
> **Objetivo**: Eliminar el 100% de los mocks laxos en la capa de tests de UI (Widgets) e integración básica.

## 1. Resumen Ejecutivo
Se ha completado exitosamente la **Fase 1** de la estrategia de "Strict Mocking". Se refactorizaron los archivos `tests/unit/test_widgets.py` y `tests/integration/test_widgets_integration.py` para eliminar 10 mocks laxos identificados. El resultado garantiza que los tests de widgets validan la interfaz real de sus dependencias, previniendo la degradación silenciosa de la calidad.

**Métricas Clave:**
- **Mocks Laxos Iniciales:** 10
- **Mocks Laxos Finales:** 0
- **Tests Fallidos:** 0 (Todos los tests pasan tras la refactorización)
- **Cobertura de Código Afectado:** Mantenida/Mejorada (El cambio en `home_widget.py` facilita el testeo).

## 2. Archivos y Componentes Afectados

### Tests Unitarios (`tests/unit/test_widgets.py`)
Se corrigieron 8 mocks laxos en las siguientes clases de test:
- **`TestHomeWidgetLogic`**: Reemplazo de mocks genéricos de `requests` por `autospec=True`.
- **`TestWorkersWidgetLogic`**: Uso de `spec=Trabajador` (modelo real) para simular datos de trabajadores.
- **`TestProductsWidgetLogic`**: Uso de `spec=Producto` (modelo real).
- **`TestCalculateTimesWidgetLogic`**: Creación de una clase `MockDecision` anidada para simular estructuras de datos complejas devueltas por el optimizador, eliminando atributos dinámicos arbitrarios.
- **`TestPrepStepsWidgetLogic`**: Uso de `spec=MainView` para simular la vista principal.

### Tests de Integración (`tests/integration/test_widgets_integration.py`)
Se corrigieron 2 mocks laxos en el fixture `setup_integration`:
- **`OptimizerWorker`**: Se importó la clase real de `controllers.pila_controller` para usarla como `spec`.
- **`SessionLocal`**: Se importó `from sqlalchemy.orm import Session` para tipar correctamente el mock de la sesión de base de datos.

### Código Fuente (`ui/widgets/home_widget.py`)
Se realizó una mejora de calidad necesaria para el testing:
- **Problema**: `requests` se importaba localmente dentro del método `set_quote`, lo que impedía que `patch` o `autospec` funcionaran correctamente desde los tests.
- **Solución**: Se movieron los imports de `requests` y `QPixmap` al nivel superior del módulo. Esto permite un mocking estándar y estricto.

## 3. Retos Encontrados y Soluciones Técnicas

### 3.1. Importaciones Locales "Intocables"
El mock estricto fallaba con `AttributeError` al intentar parchear `requests` en `HomeWidget`.
**Solución**: Refactorizar el código fuente para exponer las dependencias. Esto valida la filosofía de que "el código testearle es mejor código".

### 3.2. Claudio de Clases Internas/Workers
El controlador `PilaController` instancia dinámicamente `OptimizerWorker`. En integración, se necesitaba mockear esto pero manteniendo la interfaz real.
**Solución**: Importar la definición de clase `OptimizerWorker` solamente en el test para usarla como `spec`, sin instanciarla realmente, garantizando que el test fallará si los métodos de `OptimizerWorker` cambian en el futuro (ej. renombrar `run` a `start`).

## 4. Verificación de Calidad

Se ejecutó el script de auditoría `scripts/analyze_loose_mocks.py` con el siguiente resultado:

```
Found 997 instances of loose mocks. (Global del proyecto)
...
tests/unit/test_widgets.py: 0 loose mocks
tests/integration/test_widgets_integration.py: 0 loose mocks
...
```

La ejecución de la suite de tests confirmó la estabilidad:
```bash
pytest tests/unit/test_widgets.py tests/integration/test_widgets_integration.py
# 13 passed in 1.21s
```

## 5. Próximos Pasos

Con los widgets "seguros" y validados estrictamente, el proyecto está listo para abordar la **Fase 2: Controladores Críticos**. Esta fase será más compleja debido a la alta densidad de mocks laxos en `test_app_controller.py` (26 mocks) y sus módulos satélite.

La estrategia validada en Fase 1 (importar modelos/clases reales para specs, corregir imports locales si es necesario) se aplicará directamente.
