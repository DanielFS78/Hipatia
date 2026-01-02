# Informe de Análisis de Riesgos: Cobertura Cruzada con Mocks

**Fecha:** 1 de Enero de 2026
**Ubicación:** `documentacion/Test/Analisis_Cobertura_y_Riesgos.md`

## 1. Introducción
Este informe complementa el análisis de "Mocks Estrictos" cruzando los datos de cobertura de código (ejecución real) con la densidad de mocks permisivos. 
El objetivo es identificar las "Zonas Rojas": archivos críticos que están **poco probados** y **probados de forma insegura**.

## 2. Metodología de Scoring
Se ha calculado un **Risk Score** (Puntaje de Riesgo) para cada archivo fuente usando la siguiente fórmula heurística:
> `Risk Score = (100 - Cobertura%) + (Mocks Permisivos Relacionados * 0.5)`

*   **Baja Cobertura**: Aumenta el riesgo (máx 100 puntos si la cobertura es 0%).
*   **Muchos Mocks**: Aumenta el riesgo (añade peso por cada mock que podría estar ocultando un fallo de integración).

## 3. Top Archivos de Alto Riesgo

A continuación se presentan los componentes más críticos que requieren atención inmediata.

| Ranking | Archivo Fuente | Cobertura | Mocks Permisivos | Tests Relacionados | Análisis |
|:---:|:---|:---:|:---:|:---|:---|
| **1** | `database/repositories/material_repository.py` | **12.2%** | **83** | `test_material_repository.py` | **Crítico**. Casi sin testear real y test existente lleno de mocks falsos. |
| **2** | `ui/widgets/base.py` | 80.0% | 180 | `test_database_manager_*` | **Alto**. Aunque la cobertura es decente, la cantidad de mocks en los tests que lo usan es alarmante. |
| **3** | `ui/dialogs/prep_dialogs.py` | **0.0%** | 0 | - | **Crítico**. Código muerto o totalmente sin testear. |
| **4** | `controllers/product_controller.py` | **23.6%** | **34** | `test_product_controller.py` | **Alto**. Lógica de negocio core con muy baja cobertura y mocks inseguros. |
| **5** | `controllers/pila_controller.py` | 71.9% | 80 | `test_pila_controller_*` | **Medio-Alto**. Buena cobertura base, pero muy dependiente de mocks permisivos (80 instancias). |

## 4. Hallazgos Específicos sobre Cobertura de Ramas

El análisis confirma la hipótesis del fallo original:
*   **Baja cobertura en Controladores**: `product_controller.py` (23.6%) y `worker_controller.py` (no en top 30 pero revisado) tienen grandes secciones de lógica condicional (`if/else`) que no son alcanzadas por los tests actuales.
*   **Mocks que Ocultan Ramas**: En `pila_controller.py`, a pesar de tener 71.9% de cobertura, la presencia de 80 mocks permisivos sugiere que muchas de esas ramas se visitan con datos "falsos" que no validarían un cambio de estructura en los objetos reales.

## 5. Recomendaciones de Refactorización (Priorizadas)

### Fase 1: Blindaje de Repositorios (Semana 1)
*   **Objetivo**: `material_repository.py`
*   **Acción**: Reescribir sus tests usando una base de datos en memoria (SQLite) en lugar de mockear `Session` y `query`. Esto eliminará los 83 mocks y subirá la cobertura real.

### Fase 2: Controladores Core (Semana 2)
*   **Objetivo**: `product_controller.py`
*   **Acción**: 
    1. Implementar tests de integración ligera (similar al smoke test) para este controlador.
    2. Reemplazar mocks permisivos por `MagicMock(spec=ProductController)`.

### Fase 3: Limpieza de UI (Semana 3)
*   **Objetivo**: `ui/dialogs/prep_dialogs.py`
*   **Acción**: verificar si este archivo está en uso. Si es código muerto (residuo de refactorización), eliminarlo. Si es útil, crear al menos un test de instanciación.

## 6. Conclusión
El proyecto tiene una base de tests extensa pero frágil. La combinación de baja cobertura real en módulos críticos y el abuso de mocks hace que refactorizaciones grandes (como la de Fase 3) sean peligrosas. Adoptar la estrategia de "Tests de Integración de Arranque" y "Mocks Estrictos" reducirá drásticamente este riesgo.
