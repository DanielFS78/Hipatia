# Reporte de Limpieza: AppController

**Fecha:** 27 de Diciembre, 2025
**Archivo:** `controllers/app_controller.py`
**Objetivo:** Eliminar código muerto y métodos no utilizados detectados durante la fase de análisis y refactorización.

## Resumen de Cambios

Se han eliminado un total de **11 métodos** que fueron identificados como código muerto (sin referencias o desconectados).

### Métodos Eliminados

#### Grupo 1: Métodos Huérfanos (Sin Referencias)
Estos métodos fueron identificados inicialmente por el usuario y verificados mediante búsqueda en el código base.

1.  `_on_lote_fabricacion_selected`: Antigua lógica para poblar lotes desde fabricaciones.
2.  `_on_lote_product_search_changed`: Búsqueda de productos no conectada a la UI actual.
3.  `_on_pila_item_search_changed`: Búsqueda obsoleta para items de pila.
4.  `_on_prep_step_selected_in_list`: Manejador de selección de fases de preparación no utilizado.
5.  `_on_remove_product_from_lote_clicked`: Lógica de eliminación desconectada.
6.  `_on_save_prep_step_clicked`: Guardado de fases de preparación no referenciado.
7.  `_set_edit_search_type`: Helper de búsqueda no utilizado.
8.  `get_fabricacion_preprocesos_for_calculation`: Método de utilidad para cálculos no invocado.

#### Grupo 2: Métodos Duplicados o Similares
Identificados durante una segunda pasada de análisis de patrones `_on_*`.

9.  `_on_add_product_to_lote_clicked`: Lógica manual de adición de productos al lote sin conexión a señal.
10. `_on_fabrication_search_changed`: Método duplicado (Línea ~2313) que no estaba siendo utilizado.
11. `_on_product_search_changed` (Duplicado): Una definición antigua (Línea ~2319) que estaba "sombreando" la definición correcta y en uso (Línea ~2970).

## Métodos Verificados (Mantenidos)

Se verificó específicamente el grupo de métodos relacionados con **"Lote Template"**, confirmándose que **SÍ están en uso** y correctamente conectados:

-   `_on_add_product_to_lote_template`
-   `_on_add_fab_to_lote_template`
-   `_on_save_lote_template_clicked`
-   `_on_update_lote_template_clicked`
-   `_on_delete_lote_template_clicked`

## Conclusión

La limpieza ha reducido el tamaño de `app_controller.py` y eliminado ruido cognitivo, facilitando el mantenimiento futuro y reduciendo la posibilidad de errores por código obsoleto.
