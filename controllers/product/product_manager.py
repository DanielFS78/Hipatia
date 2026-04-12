# -*- coding: utf-8 -*-
"""
Nombre del Módulo: product.product_manager
Descripción: Gestor central para la administración de productos, incluyendo su creación, 
             edición, eliminación y gestión de iteraciones de diseño.
"""
import logging
from typing import Any, List, Dict, Optional, TYPE_CHECKING, cast
import os
import uuid
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog, QWidget, QMessageBox, QFileDialog
from core.dtos import ProductDetailsDTO
from core.import_manager.adapters.a3rp_excel_adapter import A3RPExcelAdapter
from core.import_manager.dto import BOMImportRole, BOMNodeDTO
from core.import_manager.services.bom_import_service import BOMImportService
from core.security.access_control import require_permission
from core.security.security_service import Permission
from core.validation.validator_service import ValidatorService
from controllers.ui_class_loader import ui_class

BOMImportPreviewDialog = ui_class("ui.dialogs.product.bom_import_preview_dialog", "BOMImportPreviewDialog")
ProductDetailsDialog = ui_class("ui.dialogs", "ProductDetailsDialog")
SubfabricacionesDialog = ui_class("ui.dialogs", "SubfabricacionesDialog")
ProcesosMecanicosDialog = ui_class("ui.dialogs", "ProcesosMecanicosDialog")

from .application_shell import IApplicationShell
from .protocols import ProductControllerProtocol, IProductView, IProductService

class ProductManager:
    """
    Gestor de productos e iteraciones.

    Maneja las operaciones CRUD de productos, la validación de sus datos 
    y la coordinación con los servicios de persistencia e iteraciones.
    """

    def __init__(
        self,
        app: IApplicationShell,
        machine_service: Any,
        view: IProductView,
        product_facade: IProductService,
        state: Any,
        controller_ref: Optional[ProductControllerProtocol] = None,
    ) -> None:
        """
        Inicializa el gestor de productos.

        Args:
            app: Shell del hub (adjuntos, sesión, UI).
            machine_service: Servicio de máquinas para listados en diálogos.
            view: Referencia a la vista principal (IProductView).
            product_facade: Fachada de catálogo / iteraciones (cumple IProductService).
            state: Estado compartido de la aplicación (ApplicationState).
            controller_ref: Referencia opcional al controlador de productos.
        """
        self.app = app
        self.machine_service = machine_service
        self.view = view
        self.product_facade = product_facade
        self.state = state
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")

        # Inyectar servicios de importación
        self.bom_adapter = A3RPExcelAdapter()
        self.bom_service = BOMImportService(self.product_facade)

    def handle_add_product_iteration(self, product_code: str, data: Dict[str, Any]) -> bool:
        """Gestiona la lógica para añadir una nueva iteración de producto."""
        responsable = data.get("responsable")
        descripcion = data.get("descripcion")
        tipo_fallo = data.get("tipo_fallo", "No especificado")
        ruta_plano_origen = data.get("ruta_plano_origen")

        if not all([product_code, responsable, descripcion]):
            self.view.show_message("Datos incompletos", "El responsable y la descripción son obligatorios.", "warning")
            return False

        iteracion_id = self.product_facade.add_product_iteration(
            product_code, str(responsable), str(descripcion), str(tipo_fallo), [], None
        )
        if not iteracion_id:
            self.view.show_message("Error", "No se pudo crear la iteración en la base de datos.", "critical")
            return False

        if ruta_plano_origen:
            result = self.app.handle_attach_file("iteration", iteracion_id, ruta_plano_origen, "plano")
            if result.success:
                self.product_facade.update_iteration_file_path(iteracion_id, "ruta_plano", result.path_or_error)

        self.view.show_message("Éxito", "Nueva iteración añadida correctamente.", "info")
        return True

    def handle_update_product_iteration(
        self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str
    ) -> bool:
        success = self.product_facade.update_product_iteration(iteracion_id, responsable, descripcion, tipo_fallo)
        if not success:
            self.view.show_message("Error", "No se pudo actualizar la iteración en la base de datos.", "critical")
        return success

    def handle_delete_product_iteration(self, iteration_id: int) -> bool:
        return self.product_facade.delete_product_iteration(iteration_id) if iteration_id else False

    def handle_add_iteration_image(self, iteration_id: int, file_path: str) -> tuple[bool, str]:
        """Añade una imagen a la galería de la iteración."""
        unique_suffix = str(uuid.uuid4())[:8]
        result = self.app.handle_attach_file(
            f"iteration_imgs/{iteration_id}", unique_suffix, file_path, "img"
        )
        if result.success:
            if self.product_facade.add_iteration_image(iteration_id, result.path_or_error):
                iteracion = self.product_facade.get_product_iterations_by_id_or_similar(iteration_id)
                if iteracion and not iteracion.ruta_imagen:
                    self.product_facade.update_iteration_file_path(
                        iteration_id, "ruta_imagen", result.path_or_error
                    )
                return True, "Imagen añadida."
            return False, "Error al guardar en base de datos."
        return False, f"Error al copiar el archivo: {result.path_or_error}"

    def handle_delete_iteration_image(self, image_id: int) -> bool:
        return self.product_facade.delete_iteration_image(image_id)

    def _on_product_search_changed(self, text: str) -> None:
        """Maneja la búsqueda en la pestaña de Productos."""
        products_page = self.view.get_products_tab()
        if not products_page: return
        results = self.product_facade.search_products(text)
        products_page.update_search_results(results)

    def _on_product_result_selected(self, item: Any) -> None:
        """Maneja la selección de un producto en la lista."""
        product_code = item.data(Qt.ItemDataRole.UserRole)
        if not product_code: return
        
        products_page = self.view.get_products_tab()
        if not products_page: return
        
        # Guardar el código seleccionado en el estado si es necesario
        if hasattr(self.state, 'selected_product'):
            self.state.selected_product = product_code

        details = self.product_facade.get_product_details(product_code)
        if not details or not details.producto:
            self.view.show_message("Error", f"No se encontraron detalles para el producto {product_code}.", "warning")
            products_page.clear_edit_area()
            return

        prod_data = details.producto
        sub_data_raw = details.subfabricaciones
        procesos_data_raw = details.procesos_mecanicos
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
            self.view.show_message("Error", f"Datos de producto inválidos para {product_code}.", "warning")
            products_page.clear_edit_area()

    def _on_search_or_add_pressed(self, text: str) -> None:
        """
        Maneja la acción de búsqueda o adición desde el ProductsWidget.
        Si el producto existe, lo muestra. Si no, pregunta al usuario si desea crearlo.
        """
        """Maneja el Enter en el campo de búsqueda para buscar o añadir."""
        if not text: return
        
        products_page = self.view.get_products_tab()
        if not products_page: return
        
        # Primero buscar si existe
        product = self.product_facade.get_product_by_code(text)
        if product:
            # Si existe, lo seleccionamos (esto disparará _on_product_result_selected si lo llamamos manualmente o simulamos el click)
            # Para simplificar, obtenemos los detalles directamente
            details = self.product_facade.get_product_details(text)
            if details and details.producto:
                prod_data = details.producto
                sub_data_raw = details.subfabricaciones
                procesos_data_raw = details.procesos_mecanicos
                products_page.display_product_form(prod_data, sub_data_raw)
                products_page.current_procesos_mecanicos = [
                    {
                        "id": p.id, "nombre": p.nombre, "descripcion": p.descripcion, 
                        "tiempo": p.tiempo, "tipo_trabajador": p.tipo_trabajador
                    } for p in procesos_data_raw
                ]
                return

        # Si no existe, preguntar si desea añadirlo
        if self.view.show_confirmation_dialog(
            "Producto no encontrado", 
            f"El producto con código '{text}' no existe.\n¿Desea añadirlo como producto nuevo?"
        ):
            # Al crear uno nuevo, empezamos con lista vacía de subfabricaciones y procesos
            products_page.display_product_form(text, [], is_new=True)

    @staticmethod
    def _final_product_code_from_tree(root: BOMNodeDTO) -> Optional[str]:
        """Código del nodo marcado como producto final (recorrido tolerante a ciclos)."""
        visited: set[int] = set()
        found: Optional[str] = None

        def walk(n: BOMNodeDTO) -> None:
            nonlocal found
            nid = id(n)
            if nid in visited:
                return
            visited.add(nid)
            if (
                n.import_selected
                and n.import_role == BOMImportRole.FINAL_PRODUCT
                and n.codigo_componente
            ):
                found = n.codigo_componente
            for h in n.hijos:
                walk(h)

        walk(root)
        return found

    def _select_product_in_list_and_reload(self, product_code: str) -> None:
        """Selecciona el producto en la lista de resultados y recarga la ficha derecha."""
        products_page = self.view.get_products_tab()
        if products_page is None or not product_code:
            return
        lst = products_page.results_list
        if lst is None:
            return
        for i in range(lst.count()):
            it = lst.item(i)
            if it is None:
                continue
            if it.data(Qt.ItemDataRole.UserRole) == product_code:
                lst.setCurrentItem(it)
                self._on_product_result_selected(it)
                break

    def _on_import_bom(self) -> None:
        """
        Inicia el flujo de importación interactiva de archivos A3RP.
        
        Coordina la selección de archivo, el parseo mediante A3RPExcelAdapter,
        la supervisión del usuario vía BOMImportPreviewDialog y finalmente
        la inyección masiva mediante BOMImportService.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            cast(QWidget, self.view), "Seleccionar archivo de estructura A3RP", "", "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
            
        try:
            # 1. Parsear el archivo con el adaptador
            root_node = self.bom_adapter.parse_file(file_path)
            
            # 2. Mostrar diálogo de supervisión
            dialog = BOMImportPreviewDialog(root_node, cast(QWidget, self.view))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                supervised_tree = dialog.get_supervised_tree()
                
                # 3. Proceder con la inyección
                stats = self.bom_service.import_bom_tree(supervised_tree)
                
                # 4. Feedback
                extra = ""
                if stats.get("subfabricaciones_vinculadas"):
                    extra += f"\n- Subfabricaciones (en producto final): {stats['subfabricaciones_vinculadas']}"
                if stats.get("procesos_mecanicos"):
                    extra += f"\n- Procesos mecánicos nuevos: {stats['procesos_mecanicos']}"
                if stats.get("componentes"):
                    extra += f"\n- Componentes vinculados: {stats['componentes']}"
                # Recargar listado y, si hubo éxito, volver a abrir la ficha del producto final
                # (subfabricaciones, procesos y componentes recién importados).
                self._on_product_search_changed("")
                QMessageBox.information(
                    cast(QWidget, self.view), "Importación Completada",
                    f"Se han procesado los datos correctamente:\n"
                    f"- Nuevos productos: {stats['creados']}\n"
                    f"- Actualizados: {stats['actualizados']}\n"
                    f"- Errores: {stats['errores']}"
                    f"{extra}"
                )
                if stats.get("errores", 0) == 0:
                    final_code = self._final_product_code_from_tree(supervised_tree)
                    if final_code:
                        self._select_product_in_list_and_reload(final_code)

        except Exception as e:
            QMessageBox.critical(cast(QWidget, self.view), "Error en Importación", f"No se pudo importar la estructura:\n{str(e)}")
            self.logger.error(f"Fallo en importación BOM: {e}", exc_info=True)

    def _on_update_product(self, original_codigo: str) -> None:
        """
        Valida y guarda los cambios de un producto (update o create).
        Unifica la lógica de persistencia para edición y creación.
        """
        products_page = self.view.get_products_tab()
        if not products_page: return
        
        new_data = products_page.get_product_form_data()
        sub_fabricaciones = new_data.get("sub_partes", [])
        
        # Validaciones básicas
        if not new_data.get("codigo") or not new_data.get("descripcion"):
            self.view.show_message("Error de Validación", "El código y la descripción son obligatorios.", "warning")
            return

        # Verificar si es creación o actualización
        existing = self.product_facade.get_product_by_code(original_codigo)
        
        if not existing:
            # Es un producto nuevo
            code_validation = ValidatorService.validate_product_code(new_data.get("codigo"))
            if not code_validation.is_valid:
                self.view.show_message("Error de Validación", code_validation.error_message or "Código inválido.", "warning")
                return

            time_validation = ValidatorService.validate_positive_number(str(new_data.get("tiempo_optimo")), "Tiempo Óptimo")
            if not new_data.get("tiene_subfabricaciones") and not time_validation.is_valid:
                self.view.show_message("Error de Validación", time_validation.error_message or "Tiempo inválido.", "warning")
                return

            result = self.product_facade.add_product(new_data, sub_fabricaciones)
            if result == "SUCCESS":
                self.view.show_message("Éxito", f"Producto '{new_data['codigo']}' creado correctamente.", "info")
                self._log_audit('CREATE', new_data['codigo'])
                self.app.ui_controller.on_data_changed()
                # Recargar para mostrarlo en modo edición
                self._on_search_or_add_pressed(new_data['codigo'])
            else:
                self.view.show_message("Error", f"No se pudo crear el producto: {result}", "critical")
        else:
            # Es una actualización
            if new_data["tiene_subfabricaciones"]:
                new_data["tiempo_optimo"] = sum(sub['tiempo'] for sub in sub_fabricaciones) if sub_fabricaciones else 0.0
            
            procesos_mecanicos = new_data.get("procesos_mecanicos", [])
            if procesos_mecanicos:
                try:
                    current_time = float(new_data.get("tiempo_optimo", 0.0))
                    tiempo_procesos = sum(float(proceso.get('tiempo', 0.0)) for proceso in procesos_mecanicos)
                    new_data["tiempo_optimo"] = current_time + tiempo_procesos
                except (ValueError, TypeError, KeyError) as e:
                    self.logger.error(f"Error calculando tiempo de procesos mecánicos: {e}")

            if self.product_facade.update_product(original_codigo, new_data, sub_fabricaciones):
                self.view.show_message("Éxito", "Producto actualizado.", "info")
                self._log_audit('UPDATE', original_codigo)
                self.app.ui_controller.on_data_changed()
            else:
                self.view.show_message("Error", "No se pudo actualizar el producto.", "critical")

    def _log_audit(self, action: str, entity_id: str) -> None:
        """Helper para registrar auditoría."""
        if hasattr(self.app, 'session_controller') and self.app.session_controller:
            user = self.app.session_controller.current_user
            self.app.session_controller.audit_logger.log(
                username=user.username if user else 'System',
                action=action, entity_type='PRODUCT', entity_id=0,
                description=f"Producto {action.lower()}: {entity_id}", 
                user_id=user.id if user else None
            )

    def _on_delete_product(self, codigo: str) -> None:
        if self.view.show_confirmation_dialog("Confirmar Eliminación", f"¿Está seguro de que desea eliminar el producto {codigo}?"):
             if self.product_facade.delete_product(codigo): 
                  self.view.show_message("Éxito", "Producto eliminado.", "info")
                  self._log_audit('DELETE', codigo)
                  self.app.ui_controller.on_data_changed()
                  products_page = self.view.get_products_tab()
                  if products_page: 
                      # En lugar de clear_all que vacía todo, refrescamos la búsqueda actual
                      current_search = products_page.search_entry.text()
                      self._on_product_search_changed(current_search)
                      products_page.clear_edit_area()
             else:
                  self.view.show_message("Error", "No se pudo eliminar el producto.", "critical")

    def _on_manage_subs_for_new_product(self, current_subs: List[Dict[str, Any]]) -> None:
        # Este método era para AddProductWidget, lo redirigimos o eliminamos si ya no se usa
        self._on_manage_subs_clicked()

    def _on_manage_procesos_for_new_product(self, current_procesos: List[Dict[str, Any]]) -> None:
        # Este método era para AddProductWidget, lo redirigimos o eliminamos si ya no se usa
        self._on_manage_procesos_clicked()

    def _on_calc_product_result_selected(self, item: Any) -> None:
        calc_page = self.view.get_page("calculate")
        if not calc_page: return
        codigo = item.data(Qt.ItemDataRole.UserRole)
        texto_completo = item.text()
        if hasattr(self.state, 'selected_product_for_calc'):
            self.state.selected_product_for_calc = codigo
        if hasattr(self.state, 'selected_product_for_calc_desc'):
            self.state.selected_product_for_calc_desc = texto_completo
        
        if hasattr(calc_page, 'set_selected_product'):
            calc_page.set_selected_product(texto_completo)

    @require_permission(Permission.EDIT_PRODUCT)
    def _on_manage_details_clicked(self, product_code: str) -> None:
        """Maneja el clic para ver detalles completos de un producto."""
        try:
            dialog = ProductDetailsDialog(product_code, self.controller_ref, cast(QWidget, self.view))
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error detalles producto: {e}", exc_info=True)
            self.view.show_message("Error", f"Error al mostrar detalles: {e}", "critical")

    @require_permission(Permission.EDIT_PRODUCT)
    def _on_manage_subs_clicked(self) -> None:
        """Maneja el clic para gestionar las sub-fabricaciones de un producto en edición o creación."""
        try:
            edit_page = self.view.get_products_tab()
            if not edit_page or not hasattr(edit_page, 'current_subfabricaciones'):
                self.view.show_message("Error", "No se ha seleccionado un producto.", "warning")
                return
            available_machines = self.machine_service.get_all_machines(include_inactive=False)
            current_subs = edit_page.current_subfabricaciones
            dialog = SubfabricacionesDialog(current_subs, available_machines, cast(QWidget, self.view))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                edit_page.current_subfabricaciones = dialog.get_updated_subfabricaciones()
                # Persistir en BD si el producto ya existe (evita perder cambios al no pulsar "Guardar Cambios").
                codigo_actual = ""
                if hasattr(edit_page, "form_widgets"):
                    cod_widget = edit_page.form_widgets.get("codigo")
                    if cod_widget is not None:
                        text_fn = getattr(cod_widget, "text", None)
                        if callable(text_fn):
                            try:
                                raw = text_fn()
                            except TypeError:
                                raw = None
                            if isinstance(raw, str):
                                codigo_actual = raw.strip()
                if codigo_actual and self.product_facade.get_product_by_code(codigo_actual):
                    self._on_update_product(codigo_actual)
        except Exception as e:
            self.logger.error(f"Error en manage_subs: {e}")
            self.view.show_message("Error", "Ocurrió un error al gestionar subfabricaciones.", "warning")

    @require_permission(Permission.EDIT_PRODUCT)
    def _on_manage_procesos_clicked(self) -> None:
        """Maneja el clic del botón de gestionar procesos mecánicos."""
        try:
            edit_page = self.view.get_products_tab()
            if not edit_page or not hasattr(edit_page, 'current_procesos_mecanicos'):
                self.view.show_message("Error", "No se ha seleccionado un producto.", "warning")
                return
            current_procesos = edit_page.current_procesos_mecanicos
            dialog = ProcesosMecanicosDialog(current_procesos, cast(QWidget, self.view))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                edit_page.current_procesos_mecanicos = dialog.get_updated_procesos_mecanicos()
                # Persistir en BD si el producto ya existe (evita perder cambios al cerrar el diálogo).
                codigo_actual = ""
                if hasattr(edit_page, "form_widgets"):
                    cod_widget = edit_page.form_widgets.get("codigo")
                    if cod_widget is not None:
                        text_fn = getattr(cod_widget, "text", None)
                        if callable(text_fn):
                            try:
                                raw = text_fn()
                            except TypeError:
                                raw = None
                            if isinstance(raw, str):
                                codigo_actual = raw.strip()
                if codigo_actual and self.product_facade.get_product_by_code(codigo_actual):
                    self._on_update_product(codigo_actual)
                self.app.ui_controller.on_data_changed()
        except Exception as e:
            self.logger.error(f"Error en manage_procesos: {e}")
            self.view.show_message("Error", "Ocurrió un error al gestionar procesos.", "warning")

    def _connect_products_signals(self) -> None:
        """Conecta las señales del widget de gestión de Productos."""
        try:
            products_page = self.view.get_products_tab()
            if products_page:
                products_page.search_entry.textChanged.connect(self._on_product_search_changed)
                products_page.search_or_add_signal.connect(self._on_search_or_add_pressed)
                products_page.results_list.itemClicked.connect(self._on_product_result_selected)
                products_page.manage_subs_signal.connect(self._on_manage_subs_clicked)
                products_page.manage_details_signal.connect(self._on_manage_details_clicked)
                products_page.manage_procesos_signal.connect(self._on_manage_procesos_clicked)
                products_page.import_bom_signal.connect(self._on_import_bom)
                products_page.save_product_signal.connect(self._on_update_product)
                products_page.delete_product_signal.connect(self._on_delete_product)
        except Exception as e:
            self.logger.error(f"Error conectando señales de productos: {e}")

