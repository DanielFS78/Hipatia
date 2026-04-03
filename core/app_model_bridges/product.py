# -*- coding: utf-8 -*-
"""Puente de compatibilidad para operaciones de producto / iteraciones / materiales."""

from __future__ import annotations

from typing import Any

from core.dtos import (
    MaterialDTO,
    ProductDTO,
    ProductDetailsDTO,
    ProductIterationDTO,
)
from core.facades.product_facade import ProductFacade


class AppModelProductBridge:
    """Delega en :class:`ProductFacade` (API estable hacia el dominio producto)."""

    def __init__(self, product_facade: ProductFacade) -> None:
        self.product_facade = product_facade

    def search_products(self, query: str) -> list[ProductDTO]:
        return self.product_facade.search_products(query)

    def get_latest_products(self, limit: int = 10) -> list[ProductDTO]:
        return self.product_facade.get_latest_products(limit)

    def get_product_details(self, codigo: str) -> ProductDetailsDTO:
        return self.product_facade.get_product_details(codigo)

    def add_product(
        self, data: dict[str, Any], sub_data: list[Any] | None = None
    ) -> str:
        return self.product_facade.add_product(data, sub_data)

    def update_product(
        self,
        codigo_original: str,
        data: dict[str, Any],
        subfabricaciones: list[Any] | None = None,
    ) -> bool:
        return self.product_facade.update_product(codigo_original, data, subfabricaciones)

    def delete_product(self, codigo: str) -> bool:
        return self.product_facade.delete_product(codigo)

    def get_product_iterations(self, codigo_producto: str) -> list[ProductIterationDTO]:
        return self.product_facade.get_product_iterations(codigo_producto)

    def add_product_iteration(
        self,
        codigo_producto: str,
        responsable: str,
        descripcion: str,
        tipo_fallo: str,
        materiales_list: list[dict[str, Any]],
        ruta_imagen: str | None = None,
        ruta_plano: str | None = None,
    ) -> int | None:
        return self.product_facade.add_product_iteration(
            codigo_producto,
            responsable,
            descripcion,
            tipo_fallo,
            materiales_list,
            ruta_imagen,
            ruta_plano,
        )

    def update_product_iteration_details(
        self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str
    ) -> bool:
        return self.product_facade.update_product_iteration_details(
            iteracion_id, responsable, descripcion, tipo_fallo
        )

    def add_iteration_image(self, iteracion_id: int, ruta_imagen: str) -> bool:
        return self.product_facade.add_iteration_image(iteracion_id, ruta_imagen)

    def get_product_iterations_by_id_or_similar(
        self, iteracion_id: int
    ) -> ProductIterationDTO | None:
        return self.product_facade.get_product_iterations_by_id_or_similar(iteracion_id)

    def delete_iteration_image(self, image_id: int) -> bool:
        return self.product_facade.delete_iteration_image(image_id)

    def get_materials_for_product(self, producto_codigo: str) -> list[MaterialDTO]:
        return self.product_facade.get_materials_for_product(producto_codigo)

    def add_material_to_iteration(
        self, iteracion_id: int, codigo: str, descripcion: str
    ) -> int | None:
        return self.product_facade.add_material_to_iteration(iteracion_id, codigo, descripcion)

    def get_all_materials_for_selection(self) -> list[MaterialDTO]:
        return self.product_facade.get_all_materials_for_selection()

    def update_material(
        self, material_id: int, nuevo_codigo: str, nueva_descripcion: str
    ) -> bool:
        return self.product_facade.update_material(material_id, nuevo_codigo, nueva_descripcion)

    def delete_material_link(self, iteracion_id: int, material_id: int) -> bool:
        return self.product_facade.delete_material_link(iteracion_id, material_id)

    def add_material(self, codigo: str, descripcion: str) -> int | None:
        return self.product_facade.add_material(codigo, descripcion)

    def delete_material(self, material_id: int) -> bool:
        return self.product_facade.delete_material(material_id)

    def delete_product_iteration(self, iteracion_id: int) -> bool:
        return self.product_facade.delete_product_iteration(iteracion_id)

    def link_material_to_product(self, producto_codigo: str, material_id: int) -> bool:
        return self.product_facade.link_material_to_product(producto_codigo, material_id)

    def unlink_material_from_product(self, producto_codigo: str, material_id: int) -> bool:
        return self.product_facade.unlink_material_from_product(producto_codigo, material_id)

    def get_all_iterations_with_dates(self) -> list[ProductIterationDTO]:
        return self.product_facade.get_all_iterations_with_dates()
