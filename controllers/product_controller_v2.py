# -*- coding: utf-8 -*-
"""
Nombre del Módulo: product_controller_v2.py
Descripción: Controlador centralizado para la gestión de productos, fabricaciones y 
             preprocesos. Actúa como fachada (Facade) delegando en gestores especializados.
"""
import logging
from typing import Any, List, Dict, Tuple
from PyQt6.QtCore import QObject
from .product.protocols import (
    ProductControllerProtocol, IProductView, IProductModel, 
    IProductService, IFabricacionService, IMaterialService
)
from .product.product_manager import ProductManager
from .product.fabricacion_manager import FabricacionManager
from .product.preproceso_manager import PreprocesoManager
from .product.material_manager import MaterialManager

class ProductController(QObject):
    """
    Controlador para la gestión de productos, fabricaciones y preprocesos.
    Fachada que orquesta la lógica distribuida en Managers especializados.
    """
    app: Any
    db: Any
    model: IProductModel
    view: IProductView
    product_facade: Any
    product_service: IProductService
    fabricacion_service: IFabricacionService
    material_service: IMaterialService
    ui_controller: Any
    logger: logging.Logger
    state: Any
    
    def __init__(self, app_controller: Any) -> None:
        """
        Inicializa el controlador de productos V2.

        Args:
            app_controller: Referencia al controlador principal de la aplicación.
        """
        # Inicialización de QObject requerida para señales
        super().__init__()
        
        self.app = app_controller
        self.db = app_controller.db
        self.model = app_controller.model
        self.view = app_controller.view
        self.product_facade = app_controller.model.product_facade
        self.product_service = self.product_facade.service
        self.fabricacion_service = app_controller.model.fabricacion_service
        self.material_service = app_controller.model.material_service
        self.ui_controller = app_controller.ui_controller
        self.logger = logging.getLogger("EvolucionTiemposApp")
        
        from core.di_container import DIContainer
        from core.application_state import ApplicationState
        self.state = DIContainer.get_instance().resolve(ApplicationState)
        
        self.logger.info(">>> PRODUCT CONTROLLER V2 (REFACTORIZADO) CARGADO <<<")

        # Instanciar Gestores (Composición)
        self.product_manager = ProductManager(self.app, self.model, self.view, self.product_facade, self.state, self)
        self.fabricacion_manager = FabricacionManager(
            self.app,
            self.view,
            self.fabricacion_service,
            self.product_facade,
            self.model.planning_facade,
            self.state,
            self,
        )
        self.preproceso_manager = PreprocesoManager(self.view, self.fabricacion_service, self.material_service, self)
        self.material_manager = MaterialManager(self.view, self.material_service, self)

    def on_data_changed(self) -> None:
        """Puente requerido por protocolos: notifica cambios de datos a la UI."""
        if self.ui_controller is not None:
            self.ui_controller.on_data_changed()

    def _connect_products_signals(self) -> None:
        """Delega la conexión de señales al gestor correspondiente."""
        self.product_manager._connect_products_signals()

    # PRODUCT MANAGER
    def _on_product_search_changed(self, text: str) -> None:
        return self.product_manager._on_product_search_changed(text)

    def _on_search_or_add_pressed(self, text: str) -> None:
        return self.product_manager._on_search_or_add_pressed(text)

    def _on_product_result_selected(self, item: Any) -> None:
        return self.product_manager._on_product_result_selected(item)

    def _on_update_product(self, original_codigo: str) -> None:
        return self.product_manager._on_update_product(original_codigo)

    def _on_delete_product(self, codigo: str) -> None:
        return self.product_manager._on_delete_product(codigo)

    def _on_calc_product_result_selected(self, item: Any) -> None:
        return self.product_manager._on_calc_product_result_selected(item)

    def _on_manage_details_clicked(self, product_code: str) -> None:
        return self.product_manager._on_manage_details_clicked(product_code)

    def _on_manage_subs_clicked(self) -> None:
        return self.product_manager._on_manage_subs_clicked()

    def _on_manage_procesos_clicked(self) -> None:
        return self.product_manager._on_manage_procesos_clicked()

    def handle_add_product_iteration(self, product_code: str, data: Any) -> bool:
        return self.product_manager.handle_add_product_iteration(product_code, data)

    def handle_update_product_iteration(
        self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str
    ) -> bool:
        return self.product_manager.handle_update_product_iteration(
            iteracion_id, responsable, descripcion, tipo_fallo
        )

    def handle_delete_product_iteration(self, iteration_id: int) -> bool:
        return self.product_manager.handle_delete_product_iteration(iteration_id)

    def handle_add_iteration_image(self, iteration_id: int, file_path: str) -> Tuple[bool, str]:
        return self.product_manager.handle_add_iteration_image(iteration_id, file_path)

    def handle_delete_iteration_image(self, image_id: int) -> bool:
        return self.product_manager.handle_delete_iteration_image(image_id)

    # FABRICACION MANAGER
    def _on_fabrication_search_changed(self, text: str) -> None:
        return self.fabricacion_manager._on_fabrication_search_changed(text)

    def show_create_fabricacion_dialog(self) -> None:
        return self.fabricacion_manager.show_create_fabricacion_dialog()

    def search_fabricaciones(self, query: str) -> list[Any]:
        return self.fabricacion_manager.search_fabricaciones(query)

    def _on_fabrication_result_selected(self, item: Any) -> None:
        return self.fabricacion_manager._on_fabrication_result_selected(item)

    def _on_update_fabricacion(self, fabricacion_id: int) -> bool:
        return self.fabricacion_manager._on_update_fabricacion(fabricacion_id)

    def _on_delete_fabricacion(self, fabricacion_id: int) -> bool:
        return self.fabricacion_manager._on_delete_fabricacion(fabricacion_id)

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None:
        return self.fabricacion_manager.show_fabricacion_preprocesos(fabricacion_id)

    def show_fabricacion_products(self, fabricacion_id: int) -> None:
        return self.fabricacion_manager.show_fabricacion_products(fabricacion_id)

    def _on_fabrication_result_selected_by_id(self, fabricacion_id: int) -> None:
        return self.fabricacion_manager._on_fabrication_result_selected_by_id(fabricacion_id)

    def _refresh_fabricaciones_list(self) -> None:
        return self.fabricacion_manager._refresh_fabricaciones_list()

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int) -> List[Any]:
        return self.fabricacion_manager.get_fabricacion_products_for_calculation(fabricacion_id)

    # PREPROCESO MANAGER
    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> List[Dict[str, Any]]:
        return self.preproceso_manager.get_preprocesos_by_fabricacion(fabricacion_id)

    def _load_preprocesos_data(self) -> None:
        return self.preproceso_manager._load_preprocesos_data()

    def show_add_preproceso_dialog(self) -> None:
        return self.preproceso_manager.show_add_preproceso_dialog()

    def show_edit_preproceso_dialog(self, preproceso_data: Any) -> None:
        return self.preproceso_manager.show_edit_preproceso_dialog(preproceso_data)

    def delete_preproceso(self, preproceso_id: int, preproceso_nombre: str) -> None:
        return self.preproceso_manager.delete_preproceso(preproceso_id, preproceso_nombre)

    # MATERIAL MANAGER
    def handle_import_materials_to_product(self, product_code: str, file_path: str) -> bool:
        return self.material_manager.handle_import_materials_to_product(product_code, file_path)

    def handle_add_material_to_product(self, product_code: str, material_code: str, material_desc: str) -> bool:
        return self.material_manager.handle_add_material_to_product(product_code, material_code, material_desc)

    def handle_update_material(self, material_id: int, new_code: str, new_desc: str) -> bool:
        return self.material_manager.handle_update_material(material_id, new_code, new_desc)

    def handle_unlink_material_from_product(self, product_code: str, material_id: int) -> bool:
        return self.material_manager.handle_unlink_material_from_product(product_code, material_id)

    def handle_create_material(self, code: str, desc: str) -> bool:
        return self.material_manager.handle_create_material(code, desc)

    def handle_delete_material(self, material_id: int) -> bool:
        return self.material_manager.handle_delete_material(material_id)

