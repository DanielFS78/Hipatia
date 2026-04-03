# Informe Pre-Fase: Módulo 12B (Convertir Mixins en Gestores)

## 1. Estado Actual y Contexto
La Fase 12A concluyó con éxito, inyectando directamente los servicios necesarios en los controladores y eliminando las peticiones a través del `AppModel`. Sin embargo, algunos controladores complejos (como `ProductController` o `WorkerController`) continúan delegando gran parte de su lógica en clases `Mixin` mediante herencia múltiple.
Esto contradice los principios de diseño limpios buscados (Composición sobre Herencia) y complica la inyección limpia de dependencias (para el futuro tipado estricto).

## 2. Descripción de la Fase Activa
La **Fase 12B** se enfoca exclusivamente en refactorizar esta herencia múltiple convirtiendo cada archivo `..._mixin.py` en un Gestor/Handler (`..._manager.py`). 

## 3. Plan de Acción Detallado
Se procesarán los 12 Mixins existentes distribuidos en 4 controladores:

### 3.1. Controladores de Dominio y sus Mixins
*   **WorkerController**: Se migrará de (`ManagementMixin`, `AuthMixin`, `TaskMixin`) a contener instancias de `WorkerManagementManager`, `WorkerAuthManager` y `WorkerTaskManager`.
*   **ProductController**: Se migrará de (`ProductMixin`, `FabricacionMixin`, `PreprocesoMixin`, `MaterialMixin`) a contener instancias de `ProductManager`, `FabricacionManager`, `PreprocesoManager` y `MaterialManager`.
*   **HistorialController**: Se migrará de (`ViewMixin`, `InteractionMixin`, `ReportMixin`) a contener instancias de `HistorialViewManager`, `HistorialInteractionManager` y `HistorialReportManager`.
*   **SimulationController**: Se migrará de (`VisualEditorMixin`, `ExecutionMixin`) a contener instancias de `VisualEditorManager` y `SimulationExecutionManager`.

### 3.2. Estrategia de Composición
1.  **Extracción de Métodos**: Los métodos de la clase Mixin se copiarán al nuevo archivo `..._manager.py`. Instanciaremos una clase (ej. `MaterialManager`) recibiendo explícitamente el `view` y el `service` necesario vía `__init__`.
2.  **Eliminación de Herencia Multi**: Se eliminarán los mixins de las definiciones `class Controller(QObject, ViewMixin, ...):` dejándolos como `class Controller(QObject):`.
3.  **Inyección en Constructor**: Se instanciarán/inyectarán los Managers en el `__init__` del main Controller.
4.  **Enrutamiento**: Los métodos obsoletos o conexiones a las señales UI se enrutarán directamente a los gestores: `self.view.signal.connect(self.material_manager.handle_action)`.

## 4. Estrategia de Tests y Verificación
Se seguirá la máxima **Regla Estricta del MCP**:
*   Modificar solo **un controlador a la vez** y sus respectivos Mixins. 
*   No avanzar al siguiente controlador hasta que toda la suite global (`python3 run_tests.py`) y las suites específicas (ej. `tests/unit/test_worker_controller_comprehensive.py`) **arrojen 100% de éxito, 100% de cobertura y 100% de test quality**.
*   Los tests posiblemente necesiten actualizaciones en la forma en la que "mockean" el controlador o cómo observan el uso de dependencias (se espera impactar tests, por lo que su adecuación es parte integral de esta fase).

## 5. Prevención de Riesgos
*   **Archivos Base**: Asegurarse de mantener las importaciones circulares al margen.
*   **Tipado**: No tipar estrictamente con Mypy aún (isso será la Fase de tipado). Simplemente estructurar la Composición.
