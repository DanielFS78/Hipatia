# -*- coding: utf-8 -*-
"""
Nombre del Módulo: controllers.product.protocols

Descripción: Protocolos de la capa producto: vista, modelo de fachada y contrato del controlador.
"""
from __future__ import annotations

from typing import Protocol, Any, Dict, List, Optional, Tuple
import logging

from core.application_state import ApplicationState
from core.dtos import ProductIterationDTO
from core.protocols import IFabricacionService, IMaterialService, IProductService
from core.services.fabricacion_service import FabricacionService
from core.services.product_service import ProductService

# Reexport para imports existentes `from controllers.product.protocols import ...`
__all__ = [
    "IProductView",
    "IProductService",
    "IFabricacionService",
    "IMaterialService",
    "IProductModel",
    "ProductControllerProtocol",
    "IFabricacionControllerDelegate",
]


class IProductView(Protocol):
    """Vista principal usada por los gestores de producto (p. ej. MainView)."""

    @property
    def pages(self) -> Dict[str, Any]: ...

    def switch_page(self, page_name: str) -> None: ...

    def get_page(self, name: str) -> Any: ...

    def get_products_tab(self) -> Any: ...

    def get_fabrications_tab(self) -> Any: ...

    def show_message(self, title: str, message: str, level: str = "info") -> None: ...

    def show_confirmation_dialog(self, title: str, message: str) -> bool: ...


class IProductModel(Protocol):
    """
    Fachada pasada como `product_model` (p. ej. `AppModel`).

    Los servicios se anotan con las clases concretas para que mypy acepte `AppModel`
    sin depender de la subtipificación nominal QObject+Protocol en todos los casos.
    """

    product_facade: Any
    planning_facade: Any
    product_service: ProductService
    fabricacion_service: FabricacionService
    material_service: ProductService
    machine_service: Any

    def search_products(self, text: str) -> List[Any]: ...

    def get_data_for_calculation(self, producto_codigo: str) -> List[Any]: ...

    def get_all_preprocesos_with_components(self) -> List[Any]: ...

    def get_product_iterations(self, codigo_producto: str) -> List[ProductIterationDTO]: ...


class IFabricacionControllerDelegate(Protocol):
    """Subconjunto de `ProductController` usado por `FabricacionController` (delegación UI)."""

    def show_create_fabricacion_dialog(self) -> None: ...

    def search_fabricaciones(self, text: str) -> list[Any]: ...

    def show_fabricacion_preprocesos(self, fabricacion_id: int) -> None: ...

    def _refresh_fabricaciones_list(self) -> None: ...

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int) -> list[Any]: ...


class ProductControllerProtocol(Protocol):
    """Contrato estructural que cumple ProductController (vista, servicios, estado, callbacks)."""

    app: Any
    db: Any
    model: IProductModel
    view: IProductView
    logger: logging.Logger
    state: ApplicationState
    product_facade: Any
    product_service: IProductService
    material_service: IMaterialService
    fabricacion_service: IFabricacionService
    ui_controller: Any

    def _on_product_search_changed(self, text: str) -> None: ...

    def _on_product_result_selected(self, item: Any) -> None: ...

    def _on_manage_subs_clicked(self) -> None: ...

    def _on_manage_details_clicked(self, product_code: str) -> None: ...

    def _on_manage_procesos_clicked(self) -> None: ...

    def _on_update_product(self, original_codigo: str) -> None: ...

    def _on_delete_product(self, codigo: str) -> None: ...

    def _load_preprocesos_data(self) -> None: ...

    def _refresh_fabricaciones_list(self) -> None: ...

    def _on_fabrication_search_changed(self, text: str) -> None: ...

    def _on_fabrication_result_selected_by_id(self, fabricacion_id: int) -> None: ...

    def handle_add_iteration_image(self, iteration_id: int, file_path: str) -> Tuple[bool, str]: ...

    def on_data_changed(self) -> None: ...
