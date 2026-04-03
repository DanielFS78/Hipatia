# Reporte de Errores y Soluciones - Refactorización de Flujo de Producción

Este documento detalla los problemas técnicos encontrados durante la refactorización del módulo de flujo de producción (de un archivo monolítico a un paquete modular) y cómo se resolvieron para restaurar la integridad del sistema.

## 1. Errores de Importación e Infraestructura de Tests

### ❌ Error de Importación en Tests de Humo
- **Error**: `ImportError` en `tests/unit/test_dialog_integration_smoke.py`.
- **Causa**: El test seguía intentando importar `EnhancedProductionFlowDialog` desde el archivo antiguo `ui.dialogs.production_flow_dialogs` que fue movido.
- **Solución**: Se actualizó el path de importación a `from ui.dialogs import EnhancedProductionFlowDialog` (vía `__init__.py` del paquete).

## 2. Desajustes de Interfaz y Señales (Widgets Desacoplados)

### ❌ Señal `task_requested` Faltante
- **Error**: `AttributeError: 'TaskLibraryPanel' object has no attribute 'task_requested'`.
- **Causa**: El panel de librería extraído no implementaba la señal que el diálogo esperaba para añadir tareas.
- **Solución**: Se añadió `task_requested = pyqtSignal(dict)` a `TaskLibraryPanel` y se conectó al evento de doble clic del árbol.

### ❌ Métodos Visuales en `CardWidget`
- **Error**: `AttributeError: 'CardWidget' object has no attribute 'set_selected'`.
- **Causa**: Al extraer `CardWidget` a su propio archivo, se omitieron métodos de feedback visual que el diálogo utilizaba.
- **Solución**: Se implementaron `set_selected`, `set_highlighted` y `update_workers` en `ui/widgets/production_flow/flow_canvas.py`.

### ❌ Discrepancia en Nombres de Señales
- **Error**: `AttributeError: 'ProductionFlowCanvas' object has no attribute 'task_dropped'`.
- **Causa**: Se usó `task_dropped` (snake_case) en la conexión pero el widget definía `taskDropped` (camelCase).
- **Solución**: Se estandarizaron las conexiones en `EnhancedProductionFlowDialog` para usar los nombres correctos del componente canvas.

## 3. Manejo de Datos y Lógica de Negocio

### ❌ Mismatch de Tipo: 'list' vs 'dict'
- **Error**: `AttributeError: 'list' object has no attribute 'items'` en `populate_tasks`.
- **Causa**: `EnhancedProductionFlowDialog` pasaba los datos crudos (lista) directamente al panel, en lugar del diccionario estructurado por producto.
- **Solución**: Se re-incorporó el método `_prepare_task_data` para transformar la lista plana en la estructura esperada por la biblioteca.

### ❌ Error de Tipo en Recursos (Máquinas)
- **Error**: `TypeError: 'int' object is not iterable` al cargar el inspector.
- **Causa**: Se pasaba `self.units` (un entero con la cantidad de producción) al argumento `machines` (que espera una lista) del inspector.
- **Solución**: Se corrigió la llamada para pasar una lista vacía `[]` ya que este diálogo específico no gestiona máquinas actualmente.

## 4. Errores de Inicialización y Ámbito

### ❌ Canvas no Inicializado
- **Error**: `AttributeError: 'EnhancedProductionFlowDialog' object has no attribute 'canvas'`.
- **Causa**: Un error de indentación en la inserción del método `_prepare_task_data` causó que el resto de `_setup_ui` (donde se crea el canvas) quedara dentro del ámbito del método o nunca se ejecutara tras un return temprano.
- **Solución**: Se movió `_prepare_task_data` al final del archivo como un método de apoyo, permitiendo que `_setup_ui` se complete correctamente.

### ❌ Registro de Widgets en Canvas
- **Error**: Fallo en test de integración (el canvas aparecía vacío a pesar de añadir tareas).
- **Causa**: Se creaban las tarjetas pero no se llamaba a `self.canvas.add_task_widget(card)`, por lo que el canvas no las registraba en su lista interna `task_widgets`.
- **Solución**: Se actualizó `_add_task_to_canvas` para registrar explícitamente cada widget nuevo.

## Resumen Final de Verificación
Tras resolver estos 12 puntos críticos de integración:
- **Tests Unitarios**: 1466 pasados.
- **Tests de Humo de Integración**: 2 pasados.
- **Manual**: El arrastre, selección e inspección de tareas funcionan correctamente.
