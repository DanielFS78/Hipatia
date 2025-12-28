# -*- coding: utf-8 -*-
import logging
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QDialog, QMessageBox, QPushButton

from ui.dialogs import (
    CreateFabricacionDialog, 
    ProcesosMecanicosDialog, 
    SubfabricacionesDialog,
    PreprocesosSelectionDialog,
    ProductsSelectionDialog,
    PreprocesoDialog,
    ProductDetailsDialog
)
from ui.widgets import GestionDatosWidget, AddProductWidget
import os
from importer import MaterialImporterFactory

class ProductController(QObject):
    """
    Controlador para la gestión de productos, fabricaciones y preprocesos.
    Delegado del AppController principal.
    """
    
    def __init__(self, app_controller):
        super().__init__()
        self.app = app_controller
        self.db = app_controller.db
        self.model = app_controller.model
        self.view = app_controller.view
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.logger.info(">>> PRODUCT CONTROLLER V2 LOADED SUCCESSFULLY <<<")
        self.logger = logging.getLogger("EvolucionTiemposApp")

    # =================================================================================
    # PRODUCTOS
    # =================================================================================

    def _on_product_search_changed(self, text):
        """Maneja la búsqueda en la pestaña de Productos."""
        products_page = self.view.pages["gestion_datos"].productos_tab
        results = self.model.product_repo.search_products(text)
        products_page.update_search_results(results)

    def _on_product_result_selected(self, item):
        """Maneja la selección de un producto en la lista."""
        product_code = item.data(Qt.ItemDataRole.UserRole)
        products_page = self.view.pages["gestion_datos"].productos_tab

        prod_data, sub_data_raw, procesos_data_raw = self.model.product_repo.get_product_details(product_code)
        if prod_data:
            products_page.display_product_form(prod_data, sub_data_raw)
            procesos_data = [
                {
                    "id": p.id, "nombre": p.nombre, "descripcion": p.descripcion, 
                    "tiempo": p.tiempo, "tipo_trabajador": p.tipo_trabajador
                } for p in procesos_data_raw
            ]
            products_page.current_procesos_mecanicos = procesos_data
        else:
            self.view.show_message("Error", f"No se encontraron detalles para el producto {product_code}.", "warning")
            products_page.clear_edit_area()

    def _on_save_product_clicked(self):
        add_product_page = self.view.pages["add_product"]
        data = add_product_page.get_data()

        result = self.model.add_product(data, data.get("sub_partes"))

        if result == "SUCCESS":
            self.view.show_message("Éxito", f"Producto '{data['codigo']}' guardado.", "info")
            add_product_page.clear_form()
            self.app._on_data_changed()

        elif result == "INVALID_TIME":
            self.view.show_message(
                "Error de Validación",
                "Para productos sin subfabricaciones, el campo 'Tiempo Óptimo' es obligatorio y debe ser un número mayor que cero.",
                "critical"
            )
        elif result == "MISSING_FIELDS":
            self.view.show_message("Error de Validación", "El código y la descripción son campos obligatorios.", "critical")
        elif result == "DB_ERROR":
            self.view.show_message("Error al Guardar", "No se pudo guardar el producto.\nEs posible que el código ya exista en la base de datos.", "critical")
        else:
            self.view.show_message("Error Desconocido", "Ocurrió un error inesperado al guardar el producto.", "critical")

    def _on_update_product(self, original_codigo):
        """Actualiza un producto existente en la base de datos."""
        edit_page = self.view.pages["gestion_datos"].productos_tab
        new_data = edit_page.get_product_form_data()
        new_data["procesos_mecanicos"] = edit_page.current_procesos_mecanicos

        sub_fabricaciones = new_data.get("sub_partes", [])

        if new_data["tiene_subfabricaciones"]:
            if sub_fabricaciones:
                new_data["tiempo_optimo"] = sum(sub['tiempo'] for sub in sub_fabricaciones)
            else:
                self.logger.warning(f"Producto '{new_data['codigo']}' marcado con subfabricaciones pero no tiene ninguna definida")
                new_data["tiempo_optimo"] = 0.0
        else:
            if "tiempo_optimo" not in new_data or new_data["tiempo_optimo"] is None:
                new_data["tiempo_optimo"] = 0.0
            sub_fabricaciones = []

        procesos_mecanicos = new_data.get("procesos_mecanicos", [])
        if procesos_mecanicos:
            try:
                tiempo_procesos = sum(float(proceso['tiempo']) for proceso in procesos_mecanicos)
                new_data["tiempo_optimo"] = float(new_data.get("tiempo_optimo", 0)) + tiempo_procesos
            except (ValueError, TypeError, KeyError) as e:
                self.logger.error(f"Error calculando tiempo de procesos mecánicos: {e}")

        self.logger.info(f"💾 Guardando producto {original_codigo}. Tiene Subfabs: {new_data['tiene_subfabricaciones']}")
        
        if self.model.update_product(original_codigo, new_data, sub_fabricaciones):
            self.view.show_message("Éxito", "Producto actualizado.", "info")
            self.app._on_data_changed()
        else:
            self.view.show_message("Error", "No se pudo actualizar el producto.", "critical")

    def _on_delete_product(self, codigo):
        if self.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el producto {codigo}?"):
             if self.model.delete_product(codigo): 
                 self.view.show_message("Éxito", "Producto eliminado.", "info")
                 self.app._on_data_changed()
             else:
                 self.view.show_message("Error", "No se pudo eliminar el producto.", "critical")

    def _on_manage_subs_for_new_product(self, current_subs):
        add_product_page = self.view.pages["add_product"]
        available_machines = self.model.get_all_machines(include_inactive=False)
        dialog = SubfabricacionesDialog(current_subs, available_machines, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_subs = dialog.get_updated_subfabricaciones()
            add_product_page.subfabricaciones_temp = updated_subs

    def _on_manage_procesos_for_new_product(self, current_procesos):
        add_product_page = self.view.pages["add_product"]
        dialog = ProcesosMecanicosDialog(current_procesos, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_procesos = dialog.get_updated_procesos_mecanicos()
            add_product_page.procesos_mecanicos_temp = updated_procesos

    def _on_calc_product_result_selected(self, item):
        calc_page = self.view.pages["calculate"]
        codigo = item.data(Qt.ItemDataRole.UserRole)
        texto_completo = item.text()
        self.app._selected_product_for_calc = codigo
        self.app._selected_product_for_calc_desc = texto_completo
        calc_page.set_selected_product(texto_completo)

    def _on_fabrication_search_changed(self, text):
        """Maneja el cambio de texto en la búsqueda de fabricaciones."""
        if 'gestion_datos' not in self.view.pages:
            return

        gestion_page = self.view.pages["gestion_datos"]
        if not hasattr(gestion_page, 'fabricaciones_tab'):
            return

        fab_page = gestion_page.fabricaciones_tab
        results = self.model.preproceso_repo.search_fabricaciones(text)
        fab_page.update_search_results(results)

    # =================================================================================
    # FABRICACIONES
    # =================================================================================

    def show_create_fabricacion_dialog(self):
        """Muestra el diálogo para crear fabricación con preprocesos y productos."""
        dialog_key = "create_fabricacion"
        
        if self.app.active_dialogs.get(dialog_key) and self.app.active_dialogs[dialog_key].isVisible():
            self.app.active_dialogs[dialog_key].activateWindow()
            self.app.active_dialogs[dialog_key].raise_()
            return

        self.logger.info("Mostrando diálogo para crear fabricación con preprocesos y productos.")
        try:
            all_preprocesos = self.app.model.get_all_preprocesos_with_components()
            all_products = self.model.product_repo.search_products("")  # Obtener todos los productos
            
            if not all_preprocesos and not all_products:
                self.view.show_message("Información", "No hay preprocesos ni productos. Cree alguno antes.", "info")
                return

            dialog = CreateFabricacionDialog(all_preprocesos, all_products, self.view)
            self.app.active_dialogs[dialog_key] = dialog

            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_fabricacion_data()
                
                # 1. Crear la fabricación con preprocesos
                success = self.model.preproceso_repo.create_fabricacion_with_preprocesos(data)
                
                if success:
                    # 2. Si hay productos, vincularlos a la fabricación recién creada
                    if data.get('productos'):
                        # Obtener el ID de la fabricación recién creada
                        fab_dto = self.model.preproceso_repo.get_fabricacion_by_codigo(data['codigo'])
                        if fab_dto:
                            self.model.preproceso_repo.set_products_for_fabricacion(
                                fab_dto.id, 
                                data['productos']
                            )
                    
                    self.view.show_message("Éxito", f"Fabricación '{data['codigo']}' creada.", "info")
                    
                    # Actualizar búsqueda si estamos en esa vista
                    if hasattr(self.view, 'pages') and 'gestion_datos' in self.view.pages:
                        page = self.view.pages['gestion_datos'].fabricaciones_tab
                        self._on_fabrication_search_changed(page.search_entry.text())
                    
                    self.app._on_data_changed()
                else:
                    self.view.show_message("Error", "No se pudo crear. El código podría ya existir.", "critical")

        except Exception as e:
            self.logger.error(f"Error crítico en creación de fabricación: {e}", exc_info=True)
            self.view.show_message("Error Crítico", f"Error inesperado: {e}", "critical")
        finally:
             self.app.active_dialogs[dialog_key] = None

    def search_fabricaciones(self, query: str):
        """Busca fabricaciones usando el repositorio de preprocesos."""
        try:
            return self.model.preproceso_repo.search_fabricaciones(query)
        except Exception as e:
            self.logger.error(f"Error buscando fabricaciones a través del repositorio: {e}")
            return []

    def _on_fabrication_result_selected(self, item):
        """Maneja la selección de una fabricación en la lista."""
        try:
            fabricacion_id = item.data(Qt.ItemDataRole.UserRole)
            fabrications_page = self.view.pages["gestion_datos"].fabricaciones_tab
            
            fabricacion_data = self.model.preproceso_repo.get_fabricacion_by_id(fabricacion_id)
            if fabricacion_data:
                preprocesos = fabricacion_data.preprocesos or []
                fabrications_page.display_fabricacion_form(fabricacion_data, preprocesos)
            else:
                self.view.show_message("Error", f"No se encontraron detalles para la fabricación ID {fabricacion_id}.", "warning")
                fabrications_page.clear_edit_area()
        except Exception as e:
            self.logger.error(f"Error al seleccionar fabricación: {e}", exc_info=True)

    def _on_update_fabricacion(self, fabricacion_id):
        """Actualiza una fabricación existente."""
        try:
            self.logger.info(f"Actualizando fabricación ID: {fabricacion_id}")
            
            fabrications_page = self.view.pages["gestion_datos"].fabricaciones_tab
            data = fabrications_page.get_fabricacion_form_data()
            
            if not data:
                return False

            if self.model.preproceso_repo.update_fabricacion_and_preprocesos(fabricacion_id, data, None):
                self.view.show_message("Éxito", "Fabricación actualizada.", "info")
                self.app._on_data_changed()
                self._refresh_fabricaciones_list()
                return True
            else:
                self.view.show_message("Error", "No se pudo actualizar la fabricación.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error actualizando fabricación: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            return False

    def _on_delete_fabricacion(self, fabricacion_id):
        """Elimina una fabricación."""
        try:
            if self.view.show_confirmation_dialog("Confirmar Eliminación", 
                    "¿Está seguro de que desea eliminar esta fabricación?"):
                if self.model.preproceso_repo.delete_fabricacion(fabricacion_id):
                    self.view.show_message("Éxito", "Fabricación eliminada.", "info")
                    self.app._on_data_changed()
                    self._refresh_fabricaciones_list()
                    # Limpiar el área de edición tras borrar
                    self.view.pages["gestion_datos"].fabricaciones_tab.clear_edit_area()
                    return True
                else:
                    self.view.show_message("Error", "No se pudo eliminar la fabricación.", "critical")
                    return False
        except Exception as e:
            self.logger.error(f"Error eliminando fabricación: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            return False
        return False

    def _on_manage_details_clicked(self, product_code):
        """Maneja el clic para ver detalles completos de un producto."""
        try:
            # CORRECCIÓN: Pasar 'self' (el controlador) en lugar de 'self.model'
            dialog = ProductDetailsDialog(product_code, self, self.view)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error mostrando detalles del producto: {e}", exc_info=True)
            self.view.show_message("Error", f"Error al mostrar detalles: {e}", "critical")

    def show_fabricacion_preprocesos(self, fabricacion_id: int):
        """Muestra el diálogo para asignar/editar preprocesos de una fabricación."""
        try:
            # Usar repositorio en lugar de DB manager legacy
            fabricacion_dto = self.model.preproceso_repo.get_fabricacion_by_id(fabricacion_id)
            if not fabricacion_dto:
                self.view.show_message("Error", "Fabricación no encontrada.", "critical")
                return

            # Convertir DTO a tupla para compatibilidad con el diálogo legacy
            fabricacion_tuple = (fabricacion_dto.id, fabricacion_dto.codigo, fabricacion_dto.descripcion)
            
            all_preprocesos = self.model.get_all_preprocesos_with_components()
            # Obtener IDs ya asignados
            assigned_preprocesos = self.model.preproceso_repo.get_preprocesos_by_fabricacion(fabricacion_id)
            assigned_ids = [p.id for p in assigned_preprocesos]

            dialog = PreprocesosSelectionDialog(
                fabricacion_tuple, all_preprocesos, assigned_ids, self.view
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_ids = dialog.get_selected_preprocesos()
                if self.model.preproceso_repo.update_fabricacion_preprocesos(fabricacion_id, selected_ids):
                    self.view.show_message("Éxito", f"Preprocesos actualizados para la fabricación '{fabricacion_tuple[1]}'.", "info")
                    self._refresh_fabricaciones_list()
                    # También refrescar el formulario actual para ver los cambios en la lista de la derecha
                    self._on_fabrication_result_selected_by_id(fabricacion_id)
        except Exception as e:
            self.logger.error(f"Error mostrando gestión de preprocesos: {e}", exc_info=True)
            self.view.show_message("Error", f"No se pudo abrir la gestión de preprocesos: {e}", "critical")

    def show_fabricacion_products(self, fabricacion_id: int):
        """Muestra el diálogo para asignar/editar productos de una fabricación."""
        try:
            fabricacion_dto = self.model.preproceso_repo.get_fabricacion_by_id(fabricacion_id)
            if not fabricacion_dto: return

            fabricacion_tuple = (fabricacion_dto.id, fabricacion_dto.codigo, fabricacion_dto.descripcion)
            
            # Obtener todos los productos y los asignados
            all_products = self.model.product_repo.search_products("")
            assigned_products = self.model.preproceso_repo.get_products_for_fabricacion(fabricacion_id)
            
            # Obtener descripción para productos asignados (ya que el DTO base podría no tenerla si viene de SQL raw)
            code_desc_map = {p.codigo: p.descripcion for p in all_products}
            for p in assigned_products:
                if not getattr(p, 'descripcion', None) and p.producto_codigo in code_desc_map:
                    p.descripcion = code_desc_map[p.producto_codigo]

            dialog = ProductsSelectionDialog(
                fabricacion_tuple, all_products, assigned_products, self.view
            )
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                 products_list = dialog.get_products_data() # Lista de (codigo, cantidad)
                 if self.model.preproceso_repo.set_products_for_fabricacion(fabricacion_id, products_list):
                      self.view.show_message("Éxito", "Productos de fabricación actualizados.", "info")
                      self._on_fabrication_result_selected_by_id(fabricacion_id)
                 else:
                      self.view.show_message("Error", "No se pudieron actualizar los productos.", "critical")

        except Exception as e:
            self.logger.error(f"Error gestionando productos de fabricación: {e}", exc_info=True)
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")

    def _on_fabrication_result_selected_by_id(self, fabricacion_id):
        """Similar a _on_fabrication_result_selected pero usando ID directamente."""
        try:
            fabrications_page = self.view.pages["gestion_datos"].fabricaciones_tab
            fabricacion_data = self.model.preproceso_repo.get_fabricacion_by_id(fabricacion_id)
            if fabricacion_data:
                preprocesos = fabricacion_data.preprocesos or []
                
                # Fetch products and attach to data
                products = self.model.preproceso_repo.get_products_for_fabricacion(fabricacion_id)
                # Enrich with description using a quick lookup or product repo
                # Optimization: Fetch all needed descriptions in one go if possible, or one by one
                for p in products:
                    try:
                        # Assuming get_product_details returns tuple (ProductDTO, ...)
                        details = self.model.product_repo.get_product_details(p.producto_codigo)
                        if details and details[0]:
                            p.descripcion = details[0].descripcion
                    except:
                        p.descripcion = "Descripción no disponible"
                
                fabricacion_data.productos = products
                
                fabrications_page.display_fabricacion_form(fabricacion_data, preprocesos)
        except Exception as e:
            self.logger.error(f"Error al refrescar visualización de fabricación: {e}")

    def _refresh_fabricaciones_list(self):
        try:
            if hasattr(self.view, 'pages') and 'gestion_datos' in self.view.pages:
                gestion_page = self.view.pages["gestion_datos"]
                if hasattr(gestion_page, 'fabricaciones_tab'):
                    current_text = gestion_page.fabricaciones_tab.search_entry.text()
                    self._on_fabrication_search_changed(current_text)
        except Exception as e:
            self.logger.error(f"Error refrescando lista de fabricaciones: {e}")

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int):
        try:
            fabricacion_products = self.model.db.preproceso_repo.get_products_for_fabricacion(fabricacion_id)
            calculation_data = []
            for fp_dto in fabricacion_products:
                product_data = self.model.get_data_for_calculation(fp_dto.producto_codigo)
                if product_data:
                    product_info = product_data[0].copy()
                    product_info['cantidad_en_kit'] = fp_dto.cantidad
                    calculation_data.append(product_info)
            return calculation_data
        except Exception as e:
            self.logger.error(f"Error obteniendo productos de fabricación para cálculo: {e}")
            return []

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int):
        try:
            if not hasattr(self, 'preproceso_repo'):
                from database.repositories import PreprocesoRepository
                self.preproceso_repo = PreprocesoRepository(self.model.db.SessionLocal)

            preprocesos = self.preproceso_repo.get_preprocesos_by_fabricacion(fabricacion_id)
            result = []
            for preproceso in preprocesos:
                result.append({
                    'id': preproceso.id,
                    'nombre': preproceso.nombre,
                    'descripcion': preproceso.descripcion or '',
                    'componentes': [(comp.id, comp.descripcion_componente) for comp in preproceso.componentes]
                })
            return result
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos de fabricación: {e}")
            return []

    # =================================================================================
    # PREPROCESOS
    # =================================================================================

    def _load_preprocesos_data(self):
        """Carga o recarga los datos de preprocesos y los muestra en la tabla."""
        self.logger.info("Cargando datos de preprocesos...")
        try:
            preprocesos_widget = self.view.pages.get("preprocesos")
            if not preprocesos_widget:
                self.logger.warning("Widget de preprocesos no encontrado en las páginas.")
                return

            preprocesos_data = self.model.get_all_preprocesos_with_components()
            preprocesos_widget.load_preprocesos_data(preprocesos_data)

        except Exception as e:
            self.logger.error(f"Error cargando datos de preprocesos: {e}")
            preprocesos_widget = self.view.pages.get("preprocesos")
            if preprocesos_widget:
                preprocesos_widget.load_preprocesos_data([])

    def show_add_preproceso_dialog(self):
        """Muestra el diálogo para crear un nuevo preproceso, pasándole los materiales."""
        self.logger.info("Mostrando diálogo para añadir preproceso.")
        try:
            all_materials = self.model.get_all_materials_for_selection()
            dialog = PreprocesoDialog(all_materials=all_materials, controller=self, parent=self.view)
            if dialog.exec():
                data = dialog.get_data()
                if data and self.model.create_preproceso(data):
                    self.view.show_message("Éxito", f"Preproceso '{data['nombre']}' creado.", "info")
                    self._load_preprocesos_data()
                elif data:
                    self.view.show_message("Error", "No se pudo crear el preproceso. El nombre podría ya existir.", "critical")
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de crear preproceso: {e}", exc_info=True)

    def show_edit_preproceso_dialog(self, preproceso_data):
        """Muestra el diálogo para editar un preproceso, pasándole los materiales."""
        self.logger.info(f"Mostrando diálogo para editar preproceso ID: {preproceso_data.id}")
        try:
            all_materials = self.model.get_all_materials_for_selection()
            self.logger.info(f"Instanciando PreprocesoDialog con controller: {self}")
            dialog = PreprocesoDialog(preproceso_existente=preproceso_data, all_materials=all_materials, controller=self, parent=self.view)
            if dialog.exec():
                new_data = dialog.get_data()
                if new_data and self.model.update_preproceso(preproceso_data.id, new_data):
                    self.view.show_message("Éxito", f"Preproceso '{new_data['nombre']}' actualizado.", "info")
                    self._load_preprocesos_data()
                elif new_data:
                    self.view.show_message("Error", "No se pudo actualizar el preproceso.", "critical")
        except Exception as e:
            self.logger.error(f"Error mostrando diálogo de editar preproceso: {e}", exc_info=True)

    def delete_preproceso(self, preproceso_id: int, preproceso_nombre: str):
        """Solicita confirmación y elimina un preproceso."""
        self.logger.info(f"Iniciando proceso de eliminación para preproceso ID: {preproceso_id}")
        
        reply = self.view.show_confirmation_dialog(
            'Confirmar Eliminación',
            f"¿Estás seguro de que quieres eliminar el preproceso '{preproceso_nombre}'?\n\nEsta acción no se puede deshacer."
        )

        if reply:
            try:
                if self.model.delete_preproceso(preproceso_id):
                    self.view.show_message("Éxito", f"El preproceso '{preproceso_nombre}' ha sido eliminado.", "info")
                    self._load_preprocesos_data()
                else:
                    self.view.show_message("Error de Eliminación", "No se pudo eliminar el preproceso.", "critical")
            except Exception as e:
                self.logger.error(f"Error eliminando preproceso: {e}")
                self.view.show_message("Error", f"Error al eliminar el preproceso: {e}", "critical")

    # =================================================================================
    # GESTIÓN DE EDICIÓN (Subfabricaciones / Procesos / Detalles)
    # =================================================================================

    def _on_manage_subs_clicked(self):
        """Maneja el clic para gestionar las sub-fabricaciones de un producto en edición."""
        try:
            edit_page = self.view.pages.get("gestion_datos").productos_tab
            if not hasattr(edit_page, 'current_subfabricaciones'):
                self.view.show_message("Error", "No se ha seleccionado un producto para editar.", "warning")
                return
            available_machines = self.model.get_all_machines(include_inactive=False)
            current_subs = edit_page.current_subfabricaciones
            dialog = SubfabricacionesDialog(current_subs, available_machines, self.view)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                edit_page.current_subfabricaciones = dialog.get_updated_subfabricaciones()
        except AttributeError:
            self.logger.error("Error al acceder a la pestaña de productos en manage_subs.")
            self.view.show_message("Error Interno", "No se pudo acceder a la pestaña de productos.", "critical")

    def _on_manage_procesos_clicked(self):
        """Maneja el clic del botón de gestionar procesos mecánicos en edición."""
        try:
            edit_page = self.view.pages.get("gestion_datos").productos_tab
            if not hasattr(edit_page, 'current_procesos_mecanicos'):
                self.view.show_message("Error", "No se ha seleccionado un producto para editar.", "warning")
                return
            current_procesos = edit_page.current_procesos_mecanicos
            dialog = ProcesosMecanicosDialog(current_procesos, self.view)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                edit_page.current_procesos_mecanicos = dialog.get_updated_procesos_mecanicos()
        except AttributeError:
            self.logger.error("Error al acceder a la pestaña de productos en manage_procesos.")
            self.view.show_message("Error Interno", "No se pudo acceder a la pestaña de productos.", "critical")

        dialog.exec()
        self.app._on_data_changed()

    def _connect_products_signals(self):
        """Conecta las señales del widget de gestión de Productos."""
        gestion_datos_page = self.view.pages.get("gestion_datos")
        if isinstance(gestion_datos_page, GestionDatosWidget):
            products_page = gestion_datos_page.productos_tab
            products_page.search_entry.textChanged.connect(self._on_product_search_changed)
            products_page.results_list.itemClicked.connect(self._on_product_result_selected)
            products_page.manage_subs_signal.connect(self._on_manage_subs_clicked)
            products_page.manage_details_signal.connect(self._on_manage_details_clicked)
            products_page.manage_procesos_signal.connect(self._on_manage_procesos_clicked)
            products_page.save_product_signal.connect(self._on_update_product)
            products_page.delete_product_signal.connect(self._on_delete_product)
        self.logger.debug("Señales de 'Gestión Productos' conectadas.")

    def handle_add_product_iteration(self, product_code, data):
        """
        Gestiona la lógica para añadir una nueva iteración de producto.
        """
        self.logger.info(f"Solicitando añadir nueva iteración para el producto {product_code}.")

        responsable = data.get("responsable")
        descripcion = data.get("descripcion")
        tipo_fallo = data.get("tipo_fallo", "No especificado")
        ruta_plano_origen = data.get("ruta_plano_origen")

        if not all([product_code, responsable, descripcion]):
            self.view.show_message("Datos incompletos", "El responsable y la descripción son obligatorios.", "warning")
            return False

        iteracion_id = self.model.add_product_iteration(
            product_code, responsable, descripcion, tipo_fallo,
            materiales_list=[], ruta_plano=None
        )

        if not iteracion_id:
            self.view.show_message("Error", "No se pudo crear la iteración en la base de datos.", "critical")
            return False

        if ruta_plano_origen:
            success, final_plano_path = self.app.handle_attach_file(
                "iteration", iteracion_id, ruta_plano_origen, "plano"
            )
            if success:
                self.model.db.update_iteration_file_path(iteracion_id, 'ruta_plano', final_plano_path)

        self.view.show_message("Éxito", "Nueva iteración añadida correctamente.", "info")
        return True

    def handle_update_product_iteration(self, iteracion_id, responsable, descripcion, tipo_fallo):
        self.logger.info(f"Solicitando actualización para iteración ID {iteracion_id}.")
        success = self.model.update_product_iteration(iteracion_id, responsable, descripcion, tipo_fallo)
        if not success:
            self.view.show_message("Error", "No se pudo actualizar la iteración en la base de datos.", "critical")
        return success

    def handle_delete_product_iteration(self, iteration_id):
        self.logger.info(f"Solicitando eliminación de la iteración ID {iteration_id}.")
        if not iteration_id:
            return False
        return self.model.delete_product_iteration(iteration_id)

    def handle_import_materials_to_product(self, product_code, file_path):
        """
        Gestiona la importación de una lista de materiales desde un archivo.
        """
        self.logger.info(f"Iniciando importación de materiales desde '{file_path}' para el producto '{product_code}'.")
        try:
            _, file_extension = os.path.splitext(file_path)
            factory = MaterialImporterFactory()
            importer = factory.create_importer(file_extension)

            materials = importer.import_materials(file_path)

            if materials is None:
                self.view.show_message("Error de Importación",
                                       "No se pudieron leer los materiales del archivo. Revise el formato y el log.",
                                       "critical")
                return False

            count = 0
            for material in materials:
                material_id = self.model.db.material_repo.add_material(material.codigo, material.descripcion)
                if material_id:
                    self.model.link_material_to_product(product_code, material_id)
                    count += 1

            self.view.show_message("Éxito", f"Se han importado y vinculado {count} materiales al producto.", "info")
            return True

        except ValueError as e:
            self.logger.error(f"Error de formato de archivo: {e}")
            self.view.show_message("Error de Formato", str(e), "warning")
            return False
        except Exception as e:
            self.logger.critical(f"Error inesperado durante la importación de materiales: {e}", exc_info=True)
            self.view.show_message("Error Crítico", "Ocurrió un error inesperado al importar los materiales.",
                                   "critical")
            return False
            return False

    def handle_add_material_to_product(self, product_code, material_code, material_desc):
        """
        Crea un nuevo material (si no existe) y lo vincula al producto.
        """
        self.logger.info(f"Añadiendo material {material_code} al producto {product_code}")
        try:
            # 1. Crear o buscar el material
            material_id = self.model.db.material_repo.add_material(material_code, material_desc)
            if not material_id:
                self.view.show_message("Error", "No se pudo registrar el material.", "critical")
                return False

            # 2. Vincular al producto
            if self.model.link_material_to_product(product_code, material_id):
                self.view.show_message("Éxito", "Componente añadido correctamente.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo vincular el componente (tal vez ya existe).", "warning")
                return False
        except Exception as e:
            self.logger.error(f"Error añadiendo componente: {e}")
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            return False

    def handle_update_material(self, material_id, new_code, new_desc):
        """Actualiza los datos de un material."""
        try:
            if self.model.db.material_repo.update_material(material_id, new_code, new_desc):
                self.view.show_message("Éxito", "Componente actualizado.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo actualizar el componente.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error actualizando material: {e}")
            return False

    def handle_unlink_material_from_product(self, product_code, material_id):
        """Desvincula un material de un producto."""
        try:
            if self.model.unlink_material_from_product(product_code, material_id):
                self.view.show_message("Éxito", "Componente eliminado del producto.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo eliminar el componente.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error desvinculando material: {e}")
            return False

    def handle_add_iteration_image(self, iteration_id, file_path):
        """
        Añade una imagen a la galería de la iteración.
        """
        self.logger.info(f"Añadiendo imagen a iteración {iteration_id}")
        
        # Usamos un sufijo único para evitar colisiones
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        
        success, final_path = self.app.handle_attach_file(
            f"iteration_imgs/{iteration_id}", unique_suffix, file_path, "img"
        )
        
        if success:
            if self.model.db.iteration_repo.add_image(iteration_id, final_path):
                # También actualizamos la imagen principal si no hay ninguna (para compatibilidad)
                iteracion = self.model.db.iteration_repo.get_product_iterations_by_id_or_similar(iteration_id)
                if iteracion and not iteracion.ruta_imagen:
                    self.model.db.iteration_repo.update_iteration_file_path(iteration_id, 'ruta_imagen', final_path)
                
                return True, "Imagen añadida correctamente."
            else:
                return False, "Error al guardar en base de datos."
        else:
            return False, "Error al copiar el archivo."

    def handle_delete_iteration_image(self, image_id):
        """Elimina una imagen de la galería."""
        return self.model.db.iteration_repo.delete_image(image_id)

    def handle_image_attachment(self, iteration_id, file_path):
        """
        LEGACY/COMPATIBILIDAD: Se redirige a handle_add_iteration_image.
        Gestiona la actualización de la imagen para una iteración existente.
        """
        return self.handle_add_iteration_image(iteration_id, file_path)
    def handle_create_material(self, code, desc):
        """Crea un nuevo material en el sistema."""
        try:
            material_id = self.model.db.material_repo.add_material(code, desc)
            if material_id:
                self.view.show_message("Éxito", f"Componente '{code}' creado.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo crear. El código podría ya existir.", "warning")
                return False
        except Exception as e:
            self.logger.error(f"Error creando material: {e}")
            self.view.show_message("Error", f"Error inesperado: {e}", "critical")
            return False

    def handle_delete_material(self, material_id):
        """Elimina un material del sistema."""
        try:
            # Primero verificamos si está en uso (opcional, pero recomendable)
            # Por ahora delegamos al repo que manejará la integridad referencial si está configurada,
            # o simplemente lo borramos.
            if self.model.db.material_repo.delete_material(material_id):
                self.view.show_message("Éxito", "Componente eliminado del sistema.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo eliminar el componente.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error eliminando material: {e}")
            return False
