# -*- coding: utf-8 -*-
"""
Nombre del Módulo: product.material_manager
Descripción: Gestor encargado de la administración de materiales y componentes del sistema, 
             incluyendo su creación, importación masiva y vinculación con productos.
"""
import logging
import os
from typing import TYPE_CHECKING, Any, Optional, List, Dict
from core.services.data_importer import MaterialImporterFactory

from .protocols import ProductControllerProtocol, IProductView, IMaterialService

class MaterialManager:
    """
    Gestor de materiales y componentes.

    Proporciona funcionalidades para gestionar el catálogo de piezas (componentes), 
    su persistencia y su relación con los productos terminados.
    """

    def __init__(
        self, 
        view: IProductView, 
        material_service: IMaterialService, 
        controller_ref: Optional[ProductControllerProtocol] = None
    ) -> None:
        """
        Inicializa el gestor de materiales.

        Args:
            view: Referencia a la vista principal (IProductView).
            material_service: Servicio lógico de materiales (IMaterialService).
            controller_ref: Referencia opcional al controlador (ProductControllerProtocol).
        """
        self.view = view
        self.material_service = material_service
        self.controller_ref = controller_ref
        self.logger = logging.getLogger("EvolucionTiemposApp")

    def handle_import_materials_to_product(self, product_code: str, file_path: str) -> bool:
        """Gestiona la importación de una lista de materiales desde un archivo."""
        try:
            _, ext = os.path.splitext(file_path)
            factory = MaterialImporterFactory()
            importer = factory.create_importer(ext)
            materials = importer.import_materials(file_path)

            if materials is None:
                self.view.show_message("Error de Formato",
                                       "Invalid Format",
                                       "warning")
                return False

            count = 0
            for material in materials:
                material_id = self.material_service.add_material(material.codigo, material.descripcion)
                if material_id:
                    self.material_service.link_material_to_product(product_code, material_id)
                    count += 1

            self.view.show_message("Éxito", f"Importados {count} materiales.", "info")
            return True
        except ValueError as e:
            self.view.show_message("Error de Formato", str(e), "warning")
            return False
        except Exception as e:
            self.logger.critical(f"Error inesperado durante la importación de materiales: {e}", exc_info=True)
            self.view.show_message("Error Crítico", "Ocurrió un error inesperado al importar los materiales.",
                                   "critical")
            return False

    def handle_add_material_to_product(self, product_code: str, material_code: str, material_desc: str) -> bool:
        """Crea un material y lo vincula al producto."""
        try:
            material_id = self.material_service.add_material(material_code, material_desc)
            if not material_id:
                self.view.show_message("Error", "No se pudo registrar el material.", "critical")
                return False

            if self.material_service.link_material_to_product(product_code, material_id):
                self.view.show_message("Éxito", "Componente añadido correctamente.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo vincular el componente (tal vez ya existe).", "warning")
                return False
        except Exception as e:
            self.logger.error(f"Error añadiendo componente: {e}")
            return False

    def handle_update_material(self, material_id: int, new_code: str, new_desc: str) -> bool:
        """Actualiza los datos de un material."""
        try:
            if self.material_service.update_material(material_id, new_code, new_desc):
                self.view.show_message("Éxito", "Componente actualizado.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo actualizar el componente.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error actualizando material: {e}")
            return False

    def handle_unlink_material_from_product(self, product_code: str, material_id: int) -> bool:
        """Desvincula un material de un producto."""
        try:
            if self.material_service.unlink_material_from_product(product_code, material_id):
                self.view.show_message("Éxito", "Componente desvinculado.", "info")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error desvinculando: {e}")
            return False

    def handle_create_material(self, code: str, desc: str) -> bool:
        """Crea un nuevo material en el sistema."""
        try:
            if self.material_service.add_material(code, desc):
                self.view.show_message("Éxito", f"Componente '{code}' creado.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo crear. El código podría ya existir.", "warning")
                return False
        except Exception as e:
            self.logger.error(f"Error creando material: {e}")
            return False

    def handle_delete_material(self, material_id: int) -> bool:
        """Elimina un material del sistema."""
        try:
            if self.material_service.delete_material(material_id):
                self.view.show_message("Éxito", "Componente eliminado.", "info")
                return True
            else:
                self.view.show_message("Error", "No se pudo eliminar el componente.", "critical")
                return False
        except Exception as e:
            self.logger.error(f"Error eliminando material: {e}")
            return False
