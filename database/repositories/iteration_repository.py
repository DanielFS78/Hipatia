# database/repositories/iteration_repository.py
"""
Repositorio para gestión de iteraciones de productos.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseRepository
from ..models import ProductIteration, Material, iteracion_material_link, Producto
from core.dtos import ProductIterationDTO, ProductIterationMaterialDTO


class IterationRepository(BaseRepository):
    """
    Repositorio para gestión de iteraciones de productos.
    Maneja el historial de cambios y mejoras en los productos.
    """

    def get_all_iterations_with_dates(self) -> List[ProductIterationDTO]:
        """
        Obtiene todas las iteraciones de todos los productos para la vista de historial.
        Mantiene compatibilidad con: database_manager.get_all_iterations_with_dates()

        Returns:
            Lista de ProductIterationDTO
        """

        def _operation(session):
            from sqlalchemy.orm import joinedload

            # Query con JOIN a productos para obtener la descripción
            iteraciones = session.query(ProductIteration).options(
                joinedload(ProductIteration.producto)  # Cargar producto relacionado
            ).order_by(ProductIteration.fecha_creacion.desc()).all()

            return [
                ProductIterationDTO(
                    id=iteracion.id,
                    producto_codigo=iteracion.producto_codigo,
                    descripcion=iteracion.descripcion_cambio or "",
                    fecha_creacion=iteracion.fecha_creacion,
                    nombre_responsable=iteracion.nombre_responsable or "",
                    tipo_fallo=iteracion.tipo_fallo or "",
                    materiales=[], # No necesario para esta vista ligera, o cargar si se requiere
                    ruta_imagen=iteracion.ruta_imagen,
                    ruta_plano=iteracion.ruta_plano,
                    producto_descripcion=iteracion.producto.descripcion if iteracion.producto else ''
                ) for iteracion in iteraciones
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

        def _operation(session):
            from sqlalchemy.orm import joinedload

            # Obtener iteraciones con materiales precargados (evita N+1 queries)
            iteraciones = session.query(ProductIteration).filter_by(
                producto_codigo=producto_codigo
            ).options(
                joinedload(ProductIteration.materiales)
            ).order_by(ProductIteration.fecha_creacion.desc()).all()

            results = []
            for iteracion in iteraciones:
                # Convertir materiales a DTOs
                materiales_dtos = [
                    ProductIterationMaterialDTO(
                        id=m.id,
                        codigo=m.codigo_componente,
                        descripcion=m.descripcion_componente
                    )
                    for m in iteracion.materiales
                ]

                results.append(ProductIterationDTO(
                    id=iteracion.id,
                    producto_codigo=iteracion.producto_codigo,
                    descripcion=iteracion.descripcion_cambio or "",
                    fecha_creacion=iteracion.fecha_creacion,
                    nombre_responsable=iteracion.nombre_responsable or "",
                    tipo_fallo=iteracion.tipo_fallo or "",
                    materiales=materiales_dtos,
                    ruta_imagen=iteracion.ruta_imagen,
                    ruta_plano=iteracion.ruta_plano
                    # producto_descripcion no es estrictamente necesario aquí ya que filtramos por producto
                ))

            return results

        return self.safe_execute(_operation) or []

    def add_product_iteration(self, codigo_producto: str, responsable: str, descripcion: str,
                              tipo_fallo: str, materiales_list: List[Dict[str, str]],
                              ruta_imagen: Optional[str] = None,
                              ruta_plano: Optional[str] = None) -> Optional[int]:
        """
        Añade una nueva iteración de producto con sus materiales.
        Mantiene compatibilidad con: database_manager.add_product_iteration()

        Args:
            codigo_producto: Código del producto
            responsable: Nombre del responsable
            descripcion: Descripción del cambio
            tipo_fallo: Tipo de fallo/cambio
            materiales_list: Lista de diccionarios con 'codigo' y 'descripcion' de materiales
            ruta_imagen: Ruta opcional a imagen
            ruta_plano: Ruta opcional a plano

        Returns:
            ID de la iteración creada o None si error
        """

        def _operation(session):
            # Crear la nueva iteración
            nueva_iteracion = ProductIteration(
                producto_codigo=codigo_producto,
                nombre_responsable=responsable,
                descripcion_cambio=descripcion,
                tipo_fallo=tipo_fallo,
                ruta_imagen=ruta_imagen,
                ruta_plano=ruta_plano
                # fecha_creacion se establece automáticamente por el default del modelo
            )
            session.add(nueva_iteracion)
            session.flush()  # Para obtener el ID antes del commit

            # Procesar los materiales
            for material_data in materiales_list:
                # Buscar o crear el material
                material = session.query(Material).filter_by(
                    codigo_componente=material_data['codigo']
                ).first()

                if not material:
                    # Crear nuevo material si no existe
                    material = Material(
                        codigo_componente=material_data['codigo'],
                        descripcion_componente=material_data['descripcion']
                    )
                    session.add(material)
                    session.flush()
                else:
                    # Actualizar descripción si el material ya existe
                    if material.descripcion_componente != material_data['descripcion']:
                        material.descripcion_componente = material_data['descripcion']

                # Vincular material a la iteración
                if material not in nueva_iteracion.materiales:
                    nueva_iteracion.materiales.append(material)

            self.logger.info(
                f"Nueva iteración para producto '{codigo_producto}' creada con ID {nueva_iteracion.id}")
            return nueva_iteracion.id

        return self.safe_execute(_operation)

    def update_product_iteration(self, iteracion_id: int, responsable: str,
                                 descripcion: str, tipo_fallo: str) -> bool:
        """
        Actualiza los campos de una iteración de producto.
        Mantiene compatibilidad con: database_manager.update_product_iteration()

        Args:
            iteracion_id: ID de la iteración a actualizar
            responsable: Nuevo nombre del responsable
            descripcion: Nueva descripción
            tipo_fallo: Nuevo tipo de fallo

        Returns:
            True si se actualizó, False si no se encontró o error
        """

        def _operation(session):
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
        """
        Elimina una iteración de producto.
        Los enlaces con materiales se eliminan automáticamente gracias a la cascade.
        Mantiene compatibilidad con: database_manager.delete_product_iteration()

        Args:
            iteracion_id: ID de la iteración a eliminar

        Returns:
            True si se eliminó, False si no se encontró o error
        """

        def _operation(session):
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()

            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id} para eliminar")
                return False

            # SQLAlchemy y CASCADE se encargan de eliminar los enlaces en iteracion_material_link
            session.delete(iteracion)
            self.logger.info(f"Iteración ID {iteracion_id} eliminada con éxito")
            return True

        return self.safe_execute(_operation) or False

    def update_iteration_image_path(self, iteracion_id: int, ruta_imagen: str) -> bool:
        """
        Actualiza la ruta de la imagen para una iteración.
        Mantiene compatibilidad con: database_manager.update_iteration_image_path()

        Args:
            iteracion_id: ID de la iteración
            ruta_imagen: Nueva ruta de la imagen

        Returns:
            True si se actualizó, False si no se encontró o error
        """

        def _operation(session):
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()

            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id}")
                return False

            iteracion.ruta_imagen = ruta_imagen
            self.logger.info(f"Ruta de imagen actualizada para iteración ID {iteracion_id}")
            return True

        return self.safe_execute(_operation) or False

    def update_iteration_file_path(self, iteracion_id: int, column_name: str, file_path: str) -> bool:
        """
        Actualiza la ruta de un archivo (imagen o plano) para una iteración.
        Mantiene compatibilidad con: database_manager.update_iteration_file_path()

        Args:
            iteracion_id: ID de la iteración
            column_name: Nombre de la columna ('ruta_imagen' o 'ruta_plano')
            file_path: Nueva ruta del archivo

        Returns:
            True si se actualizó, False si no se encontró, columna inválida o error
        """

        def _operation(session):
            # Validación de columna permitida
            if column_name not in ['ruta_imagen', 'ruta_plano']:
                self.logger.error(f"Nombre de columna inválido: {column_name}")
                return False

            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()

            if not iteracion:
                self.logger.warning(f"No se encontró iteración con ID {iteracion_id}")
                return False

            # Actualizar el campo correspondiente usando setattr
            setattr(iteracion, column_name, file_path)
            self.logger.info(f"Campo '{column_name}' actualizado para iteración ID {iteracion_id}")
            return True

        return self.safe_execute(_operation) or False

        return self.safe_execute(_operation) or False

    def add_image(self, iteration_id: int, image_path: str, description: Optional[str] = None) -> bool:
        """
        Añade una imagen a una iteración.
        """
        def _operation(session):
            from sqlalchemy import text
            session.execute(
                text("INSERT INTO iteration_images (iteration_id, image_path, description) VALUES (:iid, :path, :desc)"),
                {"iid": iteration_id, "path": image_path, "desc": description}
            )
            self.logger.info(f"Imagen añadida a iteración {iteration_id}")
            return True
        return self.safe_execute(_operation) or False

    def get_images(self, iteration_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las imágenes de una iteración.
        """
        def _operation(session):
            from sqlalchemy import text
            result = session.execute(
                text("SELECT id, image_path, description, upload_date FROM iteration_images WHERE iteration_id = :iid ORDER BY upload_date DESC"),
                {"iid": iteration_id}
            ).fetchall()
            return [{"id": r[0], "image_path": r[1], "description": r[2], "upload_date": r[3]} for r in result]
        return self.safe_execute(_operation) or []

    def delete_image(self, image_id: int) -> bool:
        """
        Elimina una imagen de la base de datos.
        """
        def _operation(session):
            from sqlalchemy import text
            session.execute(
                text("DELETE FROM iteration_images WHERE id = :id"),
                {"id": image_id}
            )
            self.logger.info(f"Imagen ID {image_id} eliminada")
            return True
        return self.safe_execute(_operation) or False

    def _get_default_error_value(self):
        """Valor por defecto en caso de error."""
        return []