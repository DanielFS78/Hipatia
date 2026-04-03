# Plan de Fragmentación: Monolitos Finales (Top 75 Archivos Pesados)

Este documento contiene el listado exhaustivo de los 75 archivos más pesados y complejos del proyecto Hipatia que requieren fragmentación obligatoria. Se detallan las instrucciones paso a paso para desmantelar cada monolito, garantizando un tipado estricto (0 errores mypy), cobertura de tests del 100% sin omitidos ni advertencias, y documentación exhaustiva en español.

## 🚨 Reglas Estrictas de Obligado Cumplimiento

Al fragmentar cualquier archivo de esta lista, se debe asegurar lo siguiente:

### 1. Tipado Estricto (Mypy)
- **Cero errores**: No se permite introducir `type: ignore`. Todos los archivos resultantes deben pasar la comprobación de Mypy en modo estricto.
- **Frontera UI/DTO sana**: No pasar diccionarios a la UI ni usar accesos por subíndice (`dict['key']`). Utilizar DTOs inmutables estrictamente definidos.

### 2. Testing Exhaustivo y de Alta Calidad
- **Cobertura 100%**: Cada nuevo archivo extraído debe tener su propio archivo de test asociado con cobertura total.
- **Cero Errores/Warnings/Skips**: `pytest` debe estar en verde sin advertencias ni tests saltados.
- **Mocks Estrictos Obligatorios**: Se prohíbe el uso de `MagicMock()` sin spec. Se debe usar obligatoriamente `create_autospec(Clase)`. Para `@patch`, es mandatorio pasar `autospec=True`.
- **Aserciones de Interacción**: En pruebas de servicios y controladores, usar `assert_called_once_with` o similar para verificar la delegación.
- **Validación DTO**: Usar `assert isinstance(result, XXXDTO)` para asegurar que las capas devuelven el tipo correcto.
- **Tests por Capa**: 
  - **UI (Headless)**: Instanciar el widget real. No simular el widget mismo. Usar `paintEvent` directo, NO usar `repaint()`. Testear visibilidad con `isHidden()`, no con `isVisible()`.
  - **Capa Controladores**: Mockear `AppController` estricto, mockear el Model/View.
  - **Capa Servicios/Core**: Mockear la persistencia (DatabaseManager).
  - **Capa Repositorios**: Usar la fixture `repos`, sin mocks (SQLite real en memoria).

### 3. Documentación Estándar
- **Docstrings obligatorios**: Todos los módulos, clases y métodos deben estar documentados siguiendo el estilo Google Style en español.
- **Script de Documentación**: Al terminar, ejecutar `python3 scripts/generate_daniel_doc.py` para asegurar que el archivo `Documentacion Daniel.md` incorpore las nuevas firmas y arquitecturas.

---
## 📜 Listado de los 75 Archivos a Fragmentar e Instrucciones

### 1. [COMPLETO] `ui/main_window.py`
- **Métricas actuales**: 411 LOC | 1 Clases | 19 Métodos | 0 Funciones aisladas | Complejidad Máxima: 41
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (411 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 41). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 41 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 2. [COMPLETO] `ui/dialogs/production_flow/define_flow_dialog.py`
- **Métricas actuales**: 387 LOC | 1 Clases | 17 Métodos | 0 Funciones aisladas | Complejidad Máxima: 64
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (387 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 64). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 64 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 3. [COMPLETO] `ui/widgets/production_flow/flow_canvas.py`
- **Métricas actuales**: 381 LOC | 2 Clases | 25 Métodos | 0 Funciones aisladas | Complejidad Máxima: 43
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (381 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 43). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 43 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 4. [COMPLETO] `ui/widgets/workers_widget.py`
- **Métricas actuales**: 379 LOC | 1 Clases | 13 Métodos | 0 Funciones aisladas | Complejidad Máxima: 46
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (379 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 46). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 46 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 5. `ui/worker/camera_config_dialog.py`
- **Métricas actuales**: 371 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 29
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (371 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 6. `ui/widgets/production_flow/inspector_panel.py`
- **Métricas actuales**: 363 LOC | 1 Clases | 22 Métodos | 0 Funciones aisladas | Complejidad Máxima: 30
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (363 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 7. `ui/startup_screen.py`
- **Métricas actuales**: 356 LOC | 1 Clases | 15 Métodos | 0 Funciones aisladas | Complejidad Máxima: 25
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (356 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 8. `controllers/schedule_controller.py`
- **Métricas actuales**: 355 LOC | 1 Clases | 18 Métodos | 0 Funciones aisladas | Complejidad Máxima: 53
**Explicación y Diagnóstico:**
El archivo es extremadamente extenso (355 líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 53). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 9. `core/app_model.py`
- **Métricas actuales**: 345 LOC | 1 Clases | 111 Métodos | 0 Funciones aisladas | Complejidad Máxima: 1
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (345 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 10. `core/simulation/timeline_task.py`
- **Métricas actuales**: 343 LOC | 1 Clases | 11 Métodos | 0 Funciones aisladas | Complejidad Máxima: 20
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (343 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 11. `features/worker_controller.py`
- **Métricas actuales**: 340 LOC | 2 Clases | 19 Métodos | 0 Funciones aisladas | Complejidad Máxima: 76
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (340 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 76). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 12. `ui/dialogs/production_flow/common_dialogs.py`
- **Métricas actuales**: 332 LOC | 3 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 15
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (332 líneas).
Contiene 3 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 2 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 13. `controllers/report_controller.py`
- **Métricas actuales**: 318 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 41
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (318 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 41). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 14. `ui/widgets/reports/charts_container.py`
- **Métricas actuales**: 318 LOC | 2 Clases | 11 Métodos | 0 Funciones aisladas | Complejidad Máxima: 27
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (318 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 15. `core/services/reporting/pdf_report_strategy.py`
- **Métricas actuales**: 314 LOC | 2 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 41
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (314 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 41). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 16. `ui/widgets/settings_widget.py`
- **Métricas actuales**: 312 LOC | 1 Clases | 12 Métodos | 0 Funciones aisladas | Complejidad Máxima: 32
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (312 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 32 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 17. `database/repositories/product_repository.py`
- **Métricas actuales**: 301 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 73
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (301 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 73). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 18. `controllers/backup_controller.py`
- **Métricas actuales**: 300 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 46
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (300 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 46). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 19. `controllers/product/product_manager.py`
- **Métricas actuales**: 293 LOC | 1 Clases | 18 Métodos | 0 Funciones aisladas | Complejidad Máxima: 66
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (293 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 66). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 20. `database/repositories/material_repository.py`
- **Métricas actuales**: 282 LOC | 1 Clases | 10 Métodos | 0 Funciones aisladas | Complejidad Máxima: 38
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (282 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 21. `core/simulation/simulation_engine.py`
- **Métricas actuales**: 274 LOC | 2 Clases | 7 Métodos | 0 Funciones aisladas | Complejidad Máxima: 35
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (274 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 22. `core/qr_generator.py`
- **Métricas actuales**: 269 LOC | 1 Clases | 6 Métodos | 2 Funciones aisladas | Complejidad Máxima: 13
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (269 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 23. `controllers/calculation_controller.py`
- **Métricas actuales**: 267 LOC | 1 Clases | 11 Métodos | 0 Funciones aisladas | Complejidad Máxima: 50
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (267 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 50). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 24. `controllers/hardware_controller.py`
- **Métricas actuales**: 265 LOC | 1 Clases | 6 Métodos | 0 Funciones aisladas | Complejidad Máxima: 44
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (265 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 44). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 25. `database/repositories/iteration_repository.py`
- **Métricas actuales**: 263 LOC | 1 Clases | 12 Métodos | 0 Funciones aisladas | Complejidad Máxima: 46
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (263 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 46). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 26. `ui/widgets/product/iterations_widget.py`
- **Métricas actuales**: 259 LOC | 1 Clases | 16 Métodos | 0 Funciones aisladas | Complejidad Máxima: 52
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (259 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 52). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 52 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 27. `core/health/health_checker.py`
- **Métricas actuales**: 257 LOC | 5 Clases | 4 Métodos | 0 Funciones aisladas | Complejidad Máxima: 43
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (257 líneas).
Contiene 5 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 43). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 4 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 28. `controllers/product/fabricacion_manager.py`
- **Métricas actuales**: 255 LOC | 1 Clases | 12 Métodos | 0 Funciones aisladas | Complejidad Máxima: 76
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (255 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 76). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 29. `core/services/backup_service.py`
- **Métricas actuales**: 255 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 48
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (255 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 48). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 30. `controllers/app_controller.py`
- **Métricas actuales**: 252 LOC | 1 Clases | 16 Métodos | 0 Funciones aisladas | Complejidad Máxima: 23
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (252 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 31. `ui/dialogs/fabrication/create_dialog.py`
- **Métricas actuales**: 251 LOC | 1 Clases | 26 Métodos | 0 Funciones aisladas | Complejidad Máxima: 11
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (251 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 32. `controllers/simulation/execution_manager.py`
- **Métricas actuales**: 250 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 36
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (250 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 33. `core/services/reporting/excel_report_strategy.py`
- **Métricas actuales**: 249 LOC | 1 Clases | 6 Métodos | 0 Funciones aisladas | Complejidad Máxima: 48
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (249 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 48). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 34. `core/simulation/simulation_events/production.py`
- **Métricas actuales**: 247 LOC | 2 Clases | 6 Métodos | 0 Funciones aisladas | Complejidad Máxima: 61
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (247 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 61). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 35. `ui/dialogs/canvas_widget.py`
- **Métricas actuales**: 243 LOC | 1 Clases | 15 Métodos | 0 Funciones aisladas | Complejidad Máxima: 38
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (243 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 38 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 36. `controllers/startup_controller.py`
- **Métricas actuales**: 239 LOC | 1 Clases | 7 Métodos | 0 Funciones aisladas | Complejidad Máxima: 8
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (239 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 37. `ui/dialogs/backup_restore_dialog.py`
- **Métricas actuales**: 237 LOC | 1 Clases | 5 Métodos | 0 Funciones aisladas | Complejidad Máxima: 18
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (237 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 38. `ui/widgets/products_widget.py`
- **Métricas actuales**: 235 LOC | 2 Clases | 14 Métodos | 0 Funciones aisladas | Complejidad Máxima: 19
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (235 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 39. `ui/dialogs/production_flow/enhanced_flow_dialog.py`
- **Métricas actuales**: 233 LOC | 1 Clases | 21 Métodos | 0 Funciones aisladas | Complejidad Máxima: 36
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (233 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 36 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 40. `ui/worker/main_window/ui_setup.py`
- **Métricas actuales**: 233 LOC | 1 Clases | 6 Métodos | 0 Funciones aisladas | Complejidad Máxima: 1
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (233 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 41. `ui/dialogs/utility_dialogs.py`
- **Métricas actuales**: 227 LOC | 6 Clases | 13 Métodos | 0 Funciones aisladas | Complejidad Máxima: 14
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (227 líneas).
Contiene 6 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 5 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 42. `core/dtos.py`
- **Métricas actuales**: 226 LOC | 30 Clases | 0 Métodos | 0 Funciones aisladas | Complejidad Máxima: 1
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (226 líneas).
Contiene 30 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 29 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 43. `controllers/session_controller.py`
- **Métricas actuales**: 221 LOC | 1 Clases | 5 Métodos | 0 Funciones aisladas | Complejidad Máxima: 22
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (221 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 44. `ui/dialogs/prep/preproceso_dialog.py`
- **Métricas actuales**: 219 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 30
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (219 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 45. `database/repositories/incidencia_repository.py`
- **Métricas actuales**: 217 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 29
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (217 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 46. `ui/widgets/reports/order_list.py`
- **Métricas actuales**: 214 LOC | 2 Clases | 11 Métodos | 0 Funciones aisladas | Complejidad Máxima: 8
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (214 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 47. `core/services/pila_service.py`
- **Métricas actuales**: 213 LOC | 1 Clases | 13 Métodos | 0 Funciones aisladas | Complejidad Máxima: 34
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (213 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 48. `database/repositories/tracking/core_manager.py`
- **Métricas actuales**: 206 LOC | 1 Clases | 10 Métodos | 0 Funciones aisladas | Complejidad Máxima: 52
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (206 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 52). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 49. `ui/widgets/timeline_widget.py`
- **Métricas actuales**: 204 LOC | 2 Clases | 12 Métodos | 0 Funciones aisladas | Complejidad Máxima: 19
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (204 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 50. `ui/widgets/production_flow/define_control_panel.py`
- **Métricas actuales**: 203 LOC | 1 Clases | 10 Métodos | 0 Funciones aisladas | Complejidad Máxima: 19
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (203 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 51. `core/sync_service.py`
- **Métricas actuales**: 202 LOC | 1 Clases | 5 Métodos | 0 Funciones aisladas | Complejidad Máxima: 24
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (202 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 52. `core/simulation/engine/motor.py`
- **Métricas actuales**: 199 LOC | 1 Clases | 28 Métodos | 0 Funciones aisladas | Complejidad Máxima: 28
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (199 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 53. `core/simulation/simulation_adapter.py`
- **Métricas actuales**: 199 LOC | 1 Clases | 7 Métodos | 0 Funciones aisladas | Complejidad Máxima: 46
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (199 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 46). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 54. `ui/widgets/production_flow/flow_graph_manager.py`
- **Métricas actuales**: 194 LOC | 1 Clases | 16 Métodos | 0 Funciones aisladas | Complejidad Máxima: 35
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (194 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 35 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 55. `controllers/navigation_controller.py`
- **Métricas actuales**: 193 LOC | 1 Clases | 10 Métodos | 0 Funciones aisladas | Complejidad Máxima: 45
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (193 líneas).
Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: 45). Requiere extracción de lógica condicional pesada.

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 56. `controllers/ui_signals_controller.py`
- **Métricas actuales**: 191 LOC | 1 Clases | 14 Métodos | 0 Funciones aisladas | Complejidad Máxima: 31
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (191 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 57. `ui/dialogs/prep/prep_groups_dialog.py`
- **Métricas actuales**: 189 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 20
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (189 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 58. `ui/dialogs/fabrication/bitacora_dialog.py`
- **Métricas actuales**: 188 LOC | 2 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 17
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (188 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 59. `ui/dialogs/prep/prep_steps_dialog.py`
- **Métricas actuales**: 188 LOC | 1 Clases | 6 Métodos | 0 Funciones aisladas | Complejidad Máxima: 16
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (188 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 60. `core/services/worker_service.py`
- **Métricas actuales**: 185 LOC | 1 Clases | 19 Métodos | 0 Funciones aisladas | Complejidad Máxima: 27
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (185 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 61. `ui/widgets/calculate_times_widget.py`
- **Métricas actuales**: 185 LOC | 1 Clases | 16 Métodos | 0 Funciones aisladas | Complejidad Máxima: 39
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (185 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 39 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 62. `ui/dialogs/product/subfabricaciones_dialog.py`
- **Métricas actuales**: 184 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 20
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (184 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 63. `ui/dialogs/production_flow/define_flow_presenter.py`
- **Métricas actuales**: 183 LOC | 1 Clases | 14 Métodos | 0 Funciones aisladas | Complejidad Máxima: 35
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (183 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de 35 dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 64. `controllers/worker/management_manager.py`
- **Métricas actuales**: 182 LOC | 1 Clases | 5 Métodos | 0 Funciones aisladas | Complejidad Máxima: 33
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (182 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 65. `controllers/product_controller_v2.py`
- **Métricas actuales**: 180 LOC | 1 Clases | 41 Métodos | 0 Funciones aisladas | Complejidad Máxima: 2
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (180 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 66. `database/database_manager.py`
- **Métricas actuales**: 176 LOC | 1 Clases | 22 Métodos | 0 Funciones aisladas | Complejidad Máxima: 16
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (176 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 67. `ui/dialogs/fabrication/selection_dialogs.py`
- **Métricas actuales**: 176 LOC | 2 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 10
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (176 líneas).
Contiene 2 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.
4. **Divide y Vencerás**: Mover al menos 1 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 68. `database/repositories/preproceso/fabricacion_manager.py`
- **Métricas actuales**: 174 LOC | 1 Clases | 13 Métodos | 0 Funciones aisladas | Complejidad Máxima: 38
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (174 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 69. `ui/widgets/reportes_widget.py`
- **Métricas actuales**: 172 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 22
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (172 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 70. `ui/worker/main_window/window.py`
- **Métricas actuales**: 172 LOC | 1 Clases | 16 Métodos | 0 Funciones aisladas | Complejidad Máxima: 27
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (172 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 71. `controllers/historial/view_manager.py`
- **Métricas actuales**: 169 LOC | 1 Clases | 5 Métodos | 0 Funciones aisladas | Complejidad Máxima: 38
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (169 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).
2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.
3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 72. `database/models/product.py`
- **Métricas actuales**: 169 LOC | 5 Clases | 7 Métodos | 0 Funciones aisladas | Complejidad Máxima: 1
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (169 líneas).
Contiene 5 clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).
4. **Divide y Vencerás**: Mover al menos 4 de las clases alojadas a sus propios archivos `.py` dedicados.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 73. `ui/dialogs/production_flow/enhanced_flow_presenter_builder.py`
- **Métricas actuales**: 165 LOC | 1 Clases | 10 Métodos | 0 Funciones aisladas | Complejidad Máxima: 28
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (165 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 74. `core/services/temporal_storage.py`
- **Métricas actuales**: 164 LOC | 1 Clases | 8 Métodos | 0 Funciones aisladas | Complejidad Máxima: 34
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (164 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).
2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---

### 75. `ui/dialogs/fabrication/products_dialog.py`
- **Métricas actuales**: 164 LOC | 1 Clases | 9 Métodos | 0 Funciones aisladas | Complejidad Máxima: 21
**Explicación y Diagnóstico:**
El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen (164 líneas).

**Instrucciones de Fragmentación:**
1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).
2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).
3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.

**Métricas Objetivo para esta tarea:**
Debe resultar en Múltiples módulos < 200 LOC.
Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.

---
