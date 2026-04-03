# Plan de Aislamiento de python-docx

## Objetivo
Eliminar el acoplamiento directo y los mocks de la librería externa `python-docx` en los tests unitarios. En su lugar, se creará una interfaz fuertemente tipada (`IDocumentGenerator`) y un adaptador (`DocxGeneratorAdapter`) que asuma toda la interacción con `python-docx`.

## Archivos Afectados Identificados
Basado en el script de rastreo (`scripts/track_docx_dependencies.py`), los archivos con acoplamiento directo son:
1. `core/label_manager/generator.py` (Contiene lógica directa de inserción de QR y reemplazo en iteradores de párrafos/celdas de python-docx).
2. `core/label_manager/__init__.py` (Importa de forma insegura y exporta `DocumentFactory`).
3. `core/label_manager/manager.py` (Utiliza `DocumentFactory` interactuando con `tables`, `rows`, `cells`).
4. `tests/unit/test_label_manager.py` (Usa mocks directos de `sys.modules['docx']` penalizados).

## Plan de Acción Gradual y Seguro

### Fase 1: Creación de Contratos (Interfaces)
- **Acción**: Definir `IDocumentGenerator` (como `Protocol` o `ABC`) en `core/ports/document_generator.py` o directamente dentro de `core/label_manager`.
- **Qué incluye**: Métodos de alto nivel como `generate_document_with_labels(...)`, `count_placeholders(...)`, `create_sample(...)`.

### Fase 2: Implementación de Adaptador
- **Acción**: Crear `infrastructure/document_generator/docx_adapter.py`.
- **Qué incluye**: Mover a esta clase todas las importaciones de `docx`, la lógica exacta que hay actualmente en `generator.py` y `manager.py` (iterar tablas, celdas y reemplazar).

### Fase 3: Pruebas de Integración reales
- **Acción**: Crear `tests/integration/test_docx_adapter.py`.
- **Beneficio**: Garantizar que el adaptador manipula correctamente un `.docx` real.

### Fase 4: Refactorización de LabelManager
- **Acción**: Modificar `LabelManager` para que reciba en su `__init__` una instancia de `IDocumentGenerator`.
- **Beneficio**: `LabelManager` deja de saber qué es un archivo Word. Solo orquesta.

### Fase 5: Refactorización estricta de Tests (El objetivo principal)
- **Acción**: Actualizar `test_label_manager.py`.
- **Beneficio**: Eliminar los mocks feos (`MockDoc.return_value`, parcheo en sys.modules). Se usará `create_autospec(IDocumentGenerator)`. La suite de calidad no penalizará por librerías externas.

## Estado de Ejecución
- [x] Ejecución de Script de Rastreo
- [x] Plan de implementación y Skill creado
- [x] Fase 1 completada
- [x] Fase 2 completada
- [x] Fase 3 completada
- [x] Fase 4 completada
- [x] Fase 5 completada
