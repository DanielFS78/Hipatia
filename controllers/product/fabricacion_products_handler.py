# -*- coding: utf-8 -*-
"""
Nombre del Módulo: fabricacion_products_handler
Descripción: Coordinación de productos asociados a fabricaciones (diálogo y datos
             para cálculo). Extraído en B4.5 desde lógica que antes estaba acoplada al controlador de producto.
"""

from __future__ import annotations

import logging
from typing import List, Protocol, cast

from PyQt6.QtWidgets import QDialog, QWidget

from core.dtos import CalculationProductDTO
from ui.dialogs import ProductsSelectionDialog

from .protocols import IProductView, IProductService, IFabricacionService


class IPlanningCalculationProvider(Protocol):
    """Solo la parte de planificación necesaria para armar DTOs de cálculo."""

    def get_data_for_calculation(self, producto_codigo: str) -> List[CalculationProductDTO]: ...


class FabricacionProductsHandler:
    """
    Colaborador con composición: gestión de productos de una fabricación y
    preparación para el motor de cálculo.
    """

    def __init__(
        self,
        view: IProductView,
        logger: logging.Logger,
        fabricacion_service: IFabricacionService,
        product_facade: IProductService,
        planning_facade: IPlanningCalculationProvider,
    ) -> None:
        self._view = view
        self._logger = logger
        self._fabricacion_service = fabricacion_service
        self._product_facade = product_facade
        self._planning_facade = planning_facade

    def show_fabricacion_products(self, fabricacion_id: int) -> None:
        """Muestra el diálogo para asignar/editar productos de una fabricación."""
        try:
            fabricacion_dto = self._fabricacion_service.get_fabricacion_by_id(fabricacion_id)
            if not fabricacion_dto:
                return
            fabricacion_tuple = (fabricacion_dto.id, fabricacion_dto.codigo, fabricacion_dto.descripcion)

            all_products = self._product_facade.search_products("")
            assigned_products = self._fabricacion_service.get_products_for_fabricacion(fabricacion_id)

            code_desc_map = {p.codigo: p.descripcion for p in all_products}
            for p in assigned_products:
                if not getattr(p, "descripcion", None) and p.producto_codigo in code_desc_map:
                    p.descripcion = code_desc_map[p.producto_codigo]

            dialog = ProductsSelectionDialog(
                fabricacion_tuple, all_products, assigned_products, cast(QWidget, self._view)
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                products_dtos = dialog.get_products_data()
                if self._fabricacion_service.set_products_for_fabricacion(fabricacion_id, products_dtos):
                    self._view.show_message("Éxito", "Productos configurados con éxito", "info")
                    self.refresh_fabrication_display(fabricacion_id)
                else:
                    self._view.show_message("Error", "No se pudieron actualizar los productos.", "critical")
        except Exception as e:
            self._view.show_message("Error", f"Error inesperado: {e}", "critical")
            self._logger.error(f"Error gestión productos fabricación: {e}", exc_info=True)

    def refresh_fabrication_display(self, fabricacion_id: int) -> None:
        """Refresca la visualización de la fabricación en la pestaña usando el ID."""
        try:
            fabrications_page = self._view.get_fabrications_tab()
            if not fabrications_page:
                return
            fabricacion_data = self._fabricacion_service.get_fabricacion_by_id(fabricacion_id)
            if fabricacion_data:
                preprocesos = fabricacion_data.preprocesos or []
                products = self._fabricacion_service.get_products_for_fabricacion(fabricacion_id)
                for p in products:
                    try:
                        details = self._product_facade.get_product_details(p.producto_codigo)
                        if details and details.producto:
                            p.descripcion = details.producto.descripcion
                    except Exception as e:
                        self._logger.warning(
                            "No se pudo obtener la descripción para el producto '%s': %s",
                            p.producto_codigo,
                            e,
                        )
                        p.descripcion = "Descripción no disponible"
                fabricacion_data.productos = products
                fabrications_page.display_fabricacion_form(fabricacion_data, preprocesos)
        except Exception as e:
            self._logger.error(f"Error al refrescar fabricación: {e}")

    def get_fabricacion_products_for_calculation(self, fabricacion_id: int) -> List[CalculationProductDTO]:
        """
        Obtiene y prepara los productos de una fabricación para el motor de cálculo.
        Retorna una lista de CalculationProductDTO.
        """
        try:
            fabricacion_products = self._fabricacion_service.get_products_for_fabricacion(fabricacion_id)
            calculation_data: List[CalculationProductDTO] = []

            for fp_dto in fabricacion_products:
                product_dtos = self._planning_facade.get_data_for_calculation(
                    fp_dto.producto_codigo
                )
                if product_dtos:
                    dto = product_dtos[0]
                    dto.cantidad_en_kit = fp_dto.cantidad
                    calculation_data.append(dto)

            return calculation_data
        except Exception as e:
            self._logger.error(f"Error productos fabricación para cálculo: {e}")
            return []
