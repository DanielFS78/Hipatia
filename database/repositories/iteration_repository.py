# -*- coding: utf-8 -*-
"""
Nombre del Módulo: iteration_repository
Descripción: Historial de iteraciones de producto, imágenes asociadas y consultas para la UI.

Persistencia y mapeo a DTOs sobre los modelos ``ProductIteration`` y ``Material``.
"""
from __future__ import annotations
from typing import List, Any, Optional, Dict, cast
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import ProductIteration, Material
from core.dtos import ProductIterationDTO, IterationImageDTO
from .iteration_repository_helpers import iteration_to_dto


class IterationRepository(BaseRepository):
    """
    Repositorio para gestión de iteraciones de productos.
    Maneja el historial de cambios, mejoras y gestión de imágenes.
    """

    # =========================================================================
    # CONSULTAS (LECTURA)
    # =========================================================================

    def get_all_iterations_with_dates(self) -> List[ProductIterationDTO]:
        """
        Obtiene todas las iteraciones de todos los productos para la vista de historial.

        Returns:
            Lista de ProductIterationDTO
        """

        def _operation(session: Session) -> List[ProductIterationDTO]:
            from sqlalchemy.orm import joinedload

            iteraciones = session.query(ProductIteration).options(
                joinedload(ProductIteration.producto)
            ).order_by(ProductIteration.fecha_creacion.desc()).all()

            return [
                iteration_to_dto(iteracion, include_materiales=False, include_product_desc=True)
                for iteracion in iteraciones
            ]

        return self.safe_execute(_operation) or []

    def get_product_iterations(self, producto_codigo: str) -> List[ProductIterationDTO]:
        """
        Obtiene todas las iteraciones de un producto con sus materiales.

        Args:
            producto_codigo: Código del producto

        Returns:
            Lista de ProductIterationDTO con materiales
        """

        def _operation(session: Session) -> List[ProductIterationDTO]:
            from sqlalchemy.orm import joinedload

            iteraciones = session.query(ProductIteration).filter_by(
                producto_codigo=producto_codigo
            ).options(
                joinedload(ProductIteration.materiales)
            ).order_by(ProductIteration.fecha_creacion.desc()).all()

            results = []
            for iteracion in iteraciones:
                results.append(iteration_to_dto(iteracion, include_materiales=True))

            return results

        return self.safe_execute(_operation) or []

    def get_product_iterations_by_id_or_similar(self, iteracion_id: int) -> Optional[ProductIterationDTO]:
        """
        Devuelve una iteración por ID.
        """

        def _operation(session: Session) -> Optional[ProductIterationDTO]:
            from sqlalchemy.orm import joinedload

            iteracion = (
                session.query(ProductIteration)
                .filter_by(id=iteracion_id)
                .options(joinedload(ProductIteration.materiales))
                .first()
            )
            if not iteracion:
                return None

            return iteration_to_dto(iteracion, include_materiales=True)

        return self.safe_execute(_operation)

    # =========================================================================
    # OPERACIONES CRUD (GESTIÓN)
    # =========================================================================

    def add_product_iteration(
        self,
        codigo_producto: str,
        responsable: str,
        descripcion: str,
        tipo_fallo: str,
        materiales_list: List[Dict[str, str]],
        ruta_imagen: Optional[str] = None,
        ruta_plano: Optional[str] = None,
    ) -> Optional[int]:
        """Añade una nueva iteración de producto con sus materiales."""

        def _operation(session: Session) -> Optional[int]:
            nueva_iteracion = ProductIteration(
                producto_codigo=codigo_producto,
                nombre_responsable=responsable,
                descripcion_cambio=descripcion,
                tipo_fallo=tipo_fallo,
                ruta_imagen=ruta_imagen,
                ruta_plano=ruta_plano,
            )
            session.add(nueva_iteracion)
            session.flush()

            for material_data in materiales_list:
                material = (
                    session.query(Material)
                    .filter_by(codigo_componente=material_data["codigo"])
                    .first()
                )
                if not material:
                    material = Material(
                        codigo_componente=material_data["codigo"],
                        descripcion_componente=material_data["descripcion"],
                    )
                    session.add(material)
                    session.flush()
                elif material.descripcion_componente != material_data["descripcion"]:
                    material.descripcion_componente = material_data["descripcion"]

                if material not in nueva_iteracion.materiales:
                    nueva_iteracion.materiales.append(material)

            self.logger.info(
                f"Nueva iteración para producto '{codigo_producto}' creada con ID {nueva_iteracion.id}"
            )
            return nueva_iteracion.id

        return self.safe_execute(_operation)

    def update_product_iteration(
        self, iteracion_id: int, responsable: str, descripcion: str, tipo_fallo: str
    ) -> bool:
        """Actualiza los campos de una iteración de producto."""

        def _operation(session: Session) -> bool:
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()
            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id} para actualizar")
                return False
            iteracion.nombre_responsable = responsable
            iteracion.descripcion_cambio = descripcion
            iteracion.tipo_fallo = tipo_fallo
            self.logger.info(f"Iteración ID {iteracion_id} actualizada correctamente")
            return True

        return self.safe_execute(_operation) or False

    def delete_product_iteration(self, iteracion_id: int) -> bool:
        """Elimina una iteración de producto."""

        def _operation(session: Session) -> bool:
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()
            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id} para eliminar")
                return False
            session.delete(iteracion)
            self.logger.info(f"Iteración ID {iteracion_id} eliminada con éxito")
            return True

        return self.safe_execute(_operation) or False

    def update_iteration_image_path(self, iteracion_id: int, ruta_imagen: str) -> bool:
        """Actualiza la ruta de la imagen para una iteración."""

        def _operation(session: Session) -> bool:
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()
            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id}")
                return False
            iteracion.ruta_imagen = ruta_imagen
            self.logger.info(f"Ruta de imagen actualizada para iteración ID {iteracion_id}")
            return True

        return self.safe_execute(_operation) or False

    def update_iteration_file_path(self, iteracion_id: int, column_name: str, file_path: str) -> bool:
        """Actualiza la ruta de un archivo (imagen/plano) para una iteración."""

        def _operation(session: Session) -> bool:
            if column_name not in ["ruta_imagen", "ruta_plano"]:
                self.logger.error(f"Nombre de columna inválido: {column_name}")
                return False
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()
            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id}")
                return False
            setattr(iteracion, column_name, file_path)
            self.logger.info(f"Campo '{column_name}' actualizado para iteración ID {iteracion_id}")
            return True

        return self.safe_execute(_operation) or False

    # =========================================================================
    # GESTIÓN DE IMÁGENES
    # =========================================================================

    def add_image(self, iteration_id: int, image_path: str, description: str | None = None) -> bool:
        """Añade una imagen a una iteración."""

        def _operation(session: Session) -> bool:
            from sqlalchemy import text

            session.execute(
                text("INSERT INTO iteration_images (iteration_id, image_path, description) VALUES (:iid, :path, :desc)"),
                {"iid": iteration_id, "path": image_path, "desc": description},
            )
            self.logger.info(f"Imagen añadida a iteración {iteration_id}")
            return True

        return self.safe_execute(_operation) or False

    def get_images(self, iteration_id: int) -> List[IterationImageDTO]:
        """Obtiene todas las imágenes de una iteración."""

        def _operation(session: Session) -> List[IterationImageDTO]:
            from sqlalchemy import text

            result = session.execute(
                text(
                    "SELECT id, image_path, description, upload_date FROM iteration_images "
                    "WHERE iteration_id = :iid ORDER BY upload_date DESC"
                ),
                {"iid": iteration_id},
            ).fetchall()
            return [IterationImageDTO(id=r[0], image_path=r[1], description=r[2], upload_date=r[3]) for r in result]

        return cast(List[IterationImageDTO], self.safe_execute(_operation) or [])

    def delete_image(self, image_id: int) -> bool:
        """Elimina una imagen de la base de datos."""

        def _operation(session: Session) -> bool:
            from sqlalchemy import text

            session.execute(text("DELETE FROM iteration_images WHERE id = :id"), {"id": image_id})
            self.logger.info(f"Imagen ID {image_id} eliminada")
            return True

        return self.safe_execute(_operation) or False

    def _get_default_error_value(self) -> list[Any]:
        """Valor por defecto en caso de error."""
        return []