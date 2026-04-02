# -*- coding: utf-8 -*-
import logging
from typing import Any, cast
from dataclasses import asdict

from PyQt6.QtCore import QObject, pyqtSignal

from core.dtos import ProductDTO, ProductIterationDTO, MaterialDTO, PreparationStepDTO, ProductDetailsDTO
from database.database_manager import DatabaseManager

class ProductService(QObject):
    """
    Servicio de dominio para gestionar la lógica relacionada con productos.
    Maneja:
    - Búsqueda y recuperación de detalles de producto.
    - Gestión de iteraciones y materiales.
    - Operaciones CRUD básicas (delegadas al repositorio).
    """
    
    # Señales para notificar cambios a la UI/Controladores
    product_added_signal = pyqtSignal(str)
    product_updated_signal = pyqtSignal()
    product_deleted_signal = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.logger = logging.getLogger("ProductService")

    @property
    def product_repo(self) -> Any:
        return self.db.product_repo

    @property
    def iteration_repo(self) -> Any:
        return self.db.iteration_repo
        
    @property
    def material_repo(self) -> Any:
        return self.db.material_repo

    def get_product_iterations(self, codigo_producto: str) -> list[ProductIterationDTO]:
        return self.iteration_repo.get_product_iterations(codigo_producto)

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
        return self.iteration_repo.add_product_iteration(
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
        return self.iteration_repo.update_product_iteration(
            iteracion_id, responsable, descripcion, tipo_fallo
        )

    def update_product_iteration(
        self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str
    ) -> bool:
        """Alias para compatibilidad con protocolos y controladores."""
        return self.update_product_iteration_details(iteracion_id, responsable, descripcion, tipo_fallo)

    def delete_product_iteration(self, iteracion_id: int) -> bool:
        return self.iteration_repo.delete_product_iteration(iteracion_id)

    def get_all_iterations_with_dates(self) -> list[ProductIterationDTO]:
        return self.iteration_repo.get_all_iterations_with_dates()

    def add_iteration_image(self, iteration_id: int, image_path: str) -> bool:
        return self.iteration_repo.add_image(iteration_id, image_path)

    def delete_iteration_image(self, image_id: int) -> bool:
        return self.iteration_repo.delete_image(image_id)

    def update_iteration_file_path(self, iteration_id: int, column_name: str, file_path: str) -> bool:
        return self.iteration_repo.update_iteration_file_path(iteration_id, column_name, file_path)

    def get_materials_for_product(self, producto_codigo: str) -> list[MaterialDTO]:
        return self.product_repo.get_materials_for_product(producto_codigo)

    def add_material_to_iteration(self, iteracion_id: int, codigo: str, descripcion: str) -> int:
        material_id = self.material_repo.add_material(codigo, descripcion)
        if material_id:
            self.material_repo.link_material_to_iteration(iteracion_id, material_id)
        return material_id

    def get_all_materials_for_selection(self) -> list[MaterialDTO]:
        return self.material_repo.get_all_materials()

    def update_material(self, material_id: int, nuevo_codigo: str, nueva_descripcion: str) -> bool:
        return self.material_repo.update_material(material_id, nuevo_codigo, nueva_descripcion)

    def delete_material_link(self, iteracion_id: int, material_id: int) -> bool:
        return self.material_repo.delete_material_link_from_iteration(iteracion_id, material_id)

    def delete_material(self, material_id: int) -> bool:
        return self.material_repo.delete_material(material_id)

    def link_material_to_product(self, producto_codigo: str, material_id: int) -> bool:
        return self.material_repo.link_material_to_product(producto_codigo, material_id)

    def unlink_material_from_product(self, producto_codigo: str, material_id: int) -> bool:
        return self.material_repo.unlink_material_from_product(producto_codigo, material_id)

    def add_material(self, codigo: str, descripcion: str) -> int | None:
        return self.material_repo.add_material(codigo, descripcion)

    def search_products(self, query: str) -> list[ProductDTO]:
        self.logger.info(f"Buscando productos con query: '{query}'")
        return self.product_repo.search_products(query)

    def get_product_by_code(self, codigo: str) -> ProductDTO | None:
        return self.product_repo.get_product_by_code(codigo)

    def get_latest_products(self, limit: int = 10) -> list[ProductDTO]:
        self.logger.info(f"Obteniendo los últimos {limit} productos.")
        return self.product_repo.get_latest_products(limit)

    def get_product_details(self, codigo: str) -> ProductDetailsDTO:
        return self.product_repo.get_product_details(codigo)

    def add_product(self, data: dict[str, Any], sub_data: list[Any] | None = None) -> str:
        """Valida y añade un producto usando el repositorio."""

        if not data.get("codigo") or not data.get("descripcion"):
            self.logger.error("Error de validación: Código y descripción son obligatorios.")
            return "MISSING_FIELDS"

        if not data.get("tiene_subfabricaciones"):
            try:
                tiempo_str = data.get("tiempo_optimo")
                if tiempo_str is None or str(tiempo_str).strip() == "":
                    raise ValueError("El tiempo óptimo no puede estar vacío.")
                tiempo = float(str(tiempo_str).replace(",", "."))
                if tiempo <= 0:
                    raise ValueError("El tiempo óptimo debe ser un número positivo.")
                data["tiempo_optimo"] = tiempo
            except (ValueError, TypeError):
                self.logger.error(f"Error de validación: Tiempo óptimo inválido para {data.get('codigo')}.")
                return "INVALID_TIME"

        # Pasar los datos al repositorio
        success = self.product_repo.add_product(data, sub_data)
        if success:
            self.product_added_signal.emit(data['codigo'])
            return "SUCCESS"
        else:
            return "DB_ERROR"

    def update_product(self, codigo_original: str, data: dict[str, Any], subfabricaciones: list[Any] | None = None) -> bool:
        success = self.product_repo.update_product(codigo_original, data, subfabricaciones)
        if success:
            self.product_updated_signal.emit()
        return success

    def delete_product(self, codigo: str) -> bool:
        success = self.product_repo.delete_product(codigo)
        if success:
            self.product_deleted_signal.emit()
        return success

