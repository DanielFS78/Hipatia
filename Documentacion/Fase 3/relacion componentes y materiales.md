# Relación: Componentes, Materiales y Productos

Este documento describe la arquitectura actual (Fase 3) de la gestión de Materiales, Componentes y su relación con Productos y Preprocesos en el sistema *Evolución Tiempos*.

## 1. Entidades Principales

### 1.1 Material (`MaterialDTO`)
Representa la materia prima base o componente elemental. Es la entidad **global** catalogada.
- **Tabla BD**: `materiales` (probablemente, gestionada por `MaterialRepository`).
- **Atributos**: `id`, `codigo_componente`, `descripcion_componente`.
- **Gestión**: Centralizada en `MaterialRepository`.

### 1.2 Producto (`ProductDTO`)
El artículo final fabricado.
- **Relación con Materiales**: 
    - Un producto puede tener un listado de materiales asociados (BOM).
    - Esta relación se gestiona mediante la tabla de enlace (probablemente `producto_materiales`).
- **Iteraciones**: Un producto tiene iteraciones (`ProductIterationDTO`), las cuales también pueden tener materiales específicos vinculados.

### 1.3 Preproceso (`PreprocesoDTO`)
Una fase intermedia de preparación o sub-montaje.
- **Relación con Materiales**:
    - Un preproceso se compone de uno o varios materiales.
    - **Tabla enlace**: `preproceso_materiales`.
    - **Gestión**: `PreprocesoRepository` gestiona la definición del preproceso, pero usa referencias a `Material` existentes.

## 2. Flujo de Datos y Controladores

### 2.1 Repositorios
*   **`MaterialRepository`**: 
    *   `add_material(code, desc)`: Crea nuevos materiales globales.
    *   `update_material(...)`: Edita definición global.
    *   `delete_material(id)`: Elimina del sistema (con posibles chequeos de integridad).
    *   `get_all_materials()`: Obtiene el catálogo completo.

*   **`PreprocesoRepository`**:
    *   `get_all_preprocesos_with_components()`: Carga preprocesos y sus materiales vinculados.
    *   `create_preproceso(data)`: Guarda un preproceso y sus vínculos con materiales.
    *   `update_preproceso(id, data)`: Actualiza y regenera vínculos.

### 2.2 Controladores
*   **`AppController`**: Inicializa repositorios y delega.
*   **`ProductController`**: 
    *   Actúa como fachada para la UI de gestión de productos y preprocesos.
    *   **Métodos Clave**:
        *   `handle_create_material(...)`: Delega en `MaterialRepository`.
        *   `handle_update_material(...)`: Delega en `MaterialRepository`.
        *   `handle_delete_material(...)`: Delega en `MaterialRepository`.
        *   `show_edit_preproceso_dialog(...)`: Instancia `PreprocesoDialog` y le pasa `self` (el controlador) para permitir que el diálogo llame a los métodos `handle_*`.

### 2.3 Interfaz de Usuario (UI)
*   **`PreprocesoDialog` (`ui/dialogs/prep_dialogs.py`)**:
    *   Recibe `all_materials` para mostrar la lista de selección.
    *   **NUEVO**: Recibe `controller` (`ProductController`) para permitir la creación/edición/borrado de materiales *in-situ*.
    *   **Eventos**:
        *   `_on_add_material`: Llama a `controller.handle_create_material`.
        *   `_on_edit_material`: Llama a `controller.handle_update_material`.
        *   `_on_delete_material`: Llama a `controller.handle_delete_material`.

## 3. Análisis del Problema Actual

Se ha identificado que, al abrir el `PreprocesoDialog` desde la edición de un preproceso, la variable `self.controller` dentro del diálogo es `None`.

**Ruta de Llamada (Teórica):**
1. `PreprocesosWidget._on_edit_clicked` -> Llama a `self.controller.show_edit_preproceso_dialog(sel)`.
2. `ProductController.show_edit_preproceso_dialog(preproceso_data)`:
    - Obtiene materiales.
    - Instancia `PreprocesoDialog(..., controller=self, ...)`.
    - Ejecuta el diálogo.

**Evidencia de Logs**:
- `ProductController` ("Mostrando diálogo...") se ejecuta.
- `PreprocesoDialog` recibe `None` en `__init__`.

**Diagnóstico**:
Existe una discrepancia entre el código que creemos que se está ejecutando en `ProductController` y el que realmente se ejecuta, O BIEN, una sobrescritura de argumentos. Dado que se han verificado los cambios en el archivo, se procederá a depurar la instanciación paso a paso.
