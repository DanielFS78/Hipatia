# database/repositories/material_repository.py
"""
Repositorio para gestiÃ³n de materiales/componentes.
"""
from typing import List, Tuple, Optional

from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from .base import BaseRepository
from ..models import Material, Producto, ProductIteration, producto_material_link, iteracion_material_link
from core.dtos import MaterialDTO, MaterialStatsDTO


class MaterialRepository(BaseRepository):
    """
    Repositorio para gestiÃ³n de materiales (componentes).
    """

    def _get_default_error_value(self):
        """Valor por defecto en caso de error."""
        # Devolver [] para listas, False para operaciones booleanas, None para IDs
        # Esto depende del mÃ©todo especÃ­fico, ajustaremos segÃºn sea necesario.
        # Por ahora, None es un buen valor general.
        return None

    def get_all_materials(self) -> List[MaterialDTO]:
        """
        Obtiene todos los materiales disponibles.

        Returns:
            Lista de MaterialDTO con los datos de cada material.
        """

        def _operation(session):
            materials = session.query(Material).order_by(
                Material.codigo_componente # Ordenar por cÃ³digo es mÃ¡s Ãºtil
            ).all()

            # Devolver DTOs
            return [
                MaterialDTO(
                    id=m.id,
                    codigo_componente=m.codigo_componente,
                    descripcion_componente=m.descripcion_componente
                ) for m in materials
            ]

        return self.safe_execute(_operation) or []

    def add_material(self, codigo_componente: str,
                     descripcion_componente: str) -> Optional[int]:
        """
        AÃ±ade un nuevo material si no existe, o retorna su ID si ya existe.

        Args:
            codigo_componente: CÃ³digo del material
            descripcion_componente: DescripciÃ³n del material

        Returns:
            ID del material o None si error
        """

        def _operation(session):
            # Buscar si ya existe por cÃ³digo (que es UNIQUE)
            existing = session.query(Material).filter_by(
                codigo_componente=codigo_componente
            ).first()

            if existing:
                # Si existe, actualizamos la descripciÃ³n por si ha cambiado
                if existing.descripcion_componente != descripcion_componente:
                    existing.descripcion_componente = descripcion_componente
                    self.logger.info(
                        f"Material '{codigo_componente}' ya existe (ID {existing.id}), descripciÃ³n actualizada.")
                else:
                    self.logger.info(f"Material '{codigo_componente}' ya existe (ID {existing.id}), sin cambios.")
                return existing.id

            # Crear nuevo si no existe
            material = Material(
                codigo_componente=codigo_componente,
                descripcion_componente=descripcion_componente
            )
            session.add(material)
            session.flush()  # Para obtener el ID

            self.logger.info(f"Material '{codigo_componente}' aÃ±adido con ID {material.id}")
            return material.id

        # Manejo especÃ­fico de error de unicidad fuera de safe_execute
        try:
            return self.safe_execute(_operation)
        except IntegrityError:
            self.logger.warning(
                f"Error de integridad al aÃ±adir material '{codigo_componente}', posiblemente duplicado concurrente.")
            # Intentar obtener el ID de nuevo por si se creÃ³ justo ahora por otro proceso
            session = self.get_session()
            if session:
                existing = session.query(Material).filter_by(codigo_componente=codigo_componente).first()
                session.close()
                if existing:
                    return existing.id
            return None  # Devolver None si falla
        except Exception as e:
            self.logger.error(f"Error inesperado en add_material: {e}")
            return None  # Devolver None en otros errores

    def link_material_to_product(self, producto_codigo: str, material_id: int) -> bool:
        """
        Crea un enlace entre un producto y un material.

        Args:
            producto_codigo: CÃ³digo del producto
            material_id: ID del material

        Returns:
            True si se creÃ³ el enlace o ya existÃ­a, False si error
        """

        def _operation(session):
            producto = session.query(Producto).filter_by(codigo=producto_codigo).first()
            material = session.query(Material).filter_by(id=material_id).first()

            if not producto or not material:
                self.logger.warning(f"No se encontrÃ³ producto '{producto_codigo}' o material ID {material_id}.")
                return False

            # Comprobar si la relaciÃ³n ya existe para evitar errores
            if material in producto.materiales:
                self.logger.info(f"El material ID {material_id} ya estÃ¡ vinculado al producto '{producto_codigo}'.")
                return True  # Consideramos Ã©xito si ya existe

            # AÃ±adir la relaciÃ³n
            producto.materiales.append(material)
            self.logger.info(f"Material ID {material_id} vinculado a producto '{producto_codigo}'.")
            return True

        return self.safe_execute(_operation) or False

    def unlink_material_from_product(self, producto_codigo: str, material_id: int) -> bool:
        """
        Elimina el enlace entre un producto y un material.

        Args:
            producto_codigo: CÃ³digo del producto
            material_id: ID del material

        Returns:
            True si se eliminÃ³ el enlace o no existÃ­a, False si error
        """

        def _operation(session):
            producto = session.query(Producto).options(
                joinedload(Producto.materiales)  # Cargar materiales para poder quitarlo
            ).filter_by(codigo=producto_codigo).first()
            material = session.query(Material).filter_by(id=material_id).first()

            if not producto:
                self.logger.warning(f"No se encontrÃ³ producto '{producto_codigo}' para desvincular material.")
                return False
            if not material:
                self.logger.warning(f"No se encontrÃ³ material ID {material_id} para desvincular.")
                return True  # No existe el material, consideramos Ã©xito

            # Comprobar si la relaciÃ³n existe antes de intentar quitarla
            if material in producto.materiales:
                producto.materiales.remove(material)
                self.logger.info(f"Material ID {material_id} desvinculado del producto '{producto_codigo}'.")
            else:
                self.logger.info(f"El material ID {material_id} no estaba vinculado al producto '{producto_codigo}'.")

            return True

        return self.safe_execute(_operation) or False

    def update_material(self, material_id: int, nuevo_codigo: str, nueva_descripcion: str) -> bool:
        """
        Actualiza el cÃ³digo y la descripciÃ³n de un material existente.

        Args:
            material_id: ID del material a actualizar
            nuevo_codigo: Nuevo cÃ³digo para el material
            nueva_descripcion: Nueva descripciÃ³n para el material

        Returns:
            True si se actualizÃ³, False si no se encontrÃ³ o error
        """

        def _operation(session):
            material = session.query(Material).filter_by(id=material_id).first()

            if not material:
                self.logger.warning(f"No se encontrÃ³ material con ID {material_id} para actualizar.")
                return False

            # Verificar si el nuevo cÃ³digo ya existe en otro material
            if nuevo_codigo != material.codigo_componente:
                existing = session.query(Material).filter(
                    Material.codigo_componente == nuevo_codigo,
                    Material.id != material_id
                ).first()
                if existing:
                    self.logger.error(
                        f"Error: El cÃ³digo '{nuevo_codigo}' ya estÃ¡ en uso por el material ID {existing.id}.")
                    # Lanzar una excepciÃ³n especÃ­fica o devolver un cÃ³digo de error
                    # Por simplicidad, devolvemos False y logueamos el error.
                    # En una implementaciÃ³n mÃ¡s robusta, se podrÃ­a lanzar IntegrityError.
                    return False  # Indicar fallo por duplicado

            material.codigo_componente = nuevo_codigo
            material.descripcion_componente = nueva_descripcion
            self.logger.info(f"Material ID {material_id} actualizado a cÃ³digo '{nuevo_codigo}'.")
            return True

        # Ejecutar la operación. safe_execute manejará el rollback en caso de IntegrityError si no lo capturamos antes.
        return self.safe_execute(_operation) or False

    def delete_material(self, material_id: int) -> bool:
        """
        Elimina un material del sistema.

        Args:
            material_id: ID del material a eliminar

        Returns:
            True si se eliminó, False si no se encontró o hay error (ej. restricciones FK)
        """

        def _operation(session):
            material = session.query(Material).filter_by(id=material_id).first()

            if not material:
                self.logger.warning(f"No se encontró material con ID {material_id} para eliminar.")
                return False

            # Intentar eliminar - si hay FK constraints, fallará
            try:
                session.delete(material)
                session.flush()  # Forzar el delete para capturar errores de FK
                self.logger.info(f"Material ID {material_id} eliminado del sistema.")
                return True
            except Exception as e:
                self.logger.error(f"No se pudo eliminar material ID {material_id}: {e}")
                return False

        return self.safe_execute(_operation) or False

    def link_material_to_iteration(self, iteracion_id: int, material_id: int) -> bool:
        """
        Crea un enlace entre una iteraciÃ³n de producto y un material.

        Args:
            iteracion_id: ID de la iteraciÃ³n
            material_id: ID del material

        Returns:
            True si se creÃ³ el enlace o ya existÃ­a, False si error
        """

        def _operation(session):
            iteracion = session.query(ProductIteration).filter_by(id=iteracion_id).first()
            material = session.query(Material).filter_by(id=material_id).first()

            if not iteracion or not material:
                self.logger.warning(f"No se encontrÃ³ iteraciÃ³n ID {iteracion_id} o material ID {material_id}.")
                return False

            # Comprobar si la relaciÃ³n ya existe
            if material in iteracion.materiales:
                self.logger.info(f"El material ID {material_id} ya estÃ¡ vinculado a la iteraciÃ³n {iteracion_id}.")
                return True

            iteracion.materiales.append(material)
            self.logger.info(f"Material ID {material_id} vinculado a iteraciÃ³n {iteracion_id}.")
            return True

        return self.safe_execute(_operation) or False

    def delete_material_link_from_iteration(self, iteracion_id: int, material_id: int) -> bool:
        """
        Elimina el enlace entre una iteraciÃ³n y un material.
        (Renombrado desde delete_material_link para claridad)

        Args:
            iteracion_id: ID de la iteraciÃ³n
            material_id: ID del material a desvincular

        Returns:
            True si se eliminÃ³ o no existÃ­a, False si error
        """

        def _operation(session):
            iteracion = session.query(ProductIteration).options(
                joinedload(ProductIteration.materiales)  # Cargar materiales
            ).filter_by(id=iteracion_id).first()
            material = session.query(Material).filter_by(id=material_id).first()

            if not iteracion:
                self.logger.warning(f"No se encontrÃ³ iteraciÃ³n ID {iteracion_id}.")
                return False  # O True si consideramos que no hacer nada es Ã©xito? False parece mejor.
            if not material:
                self.logger.warning(f"No se encontrÃ³ material ID {material_id}.")
                return True  # El material no existe, enlace imposible, consideramos Ã©xito.

            if material in iteracion.materiales:
                iteracion.materiales.remove(material)
                self.logger.info(f"Material ID {material_id} desvinculado de la iteraciÃ³n {iteracion_id}.")
            else:
                self.logger.info(f"Material ID {material_id} no estaba vinculado a la iteraciÃ³n {iteracion_id}.")

            return True

        return self.safe_execute(_operation) or False

    def get_problematic_components_stats(self, limit: int = 10) -> List[MaterialStatsDTO]:
        """
        Obtiene estadÃƒÂ­sticas de componentes problemÃƒÂ¡ticos.
        Cuenta la frecuencia con la que cada material aparece en iteraciones de productos.
        Los componentes que aparecen en mÃƒÂ¡s iteraciones se consideran mÃƒÂ¡s "problemÃƒÂ¡ticos".

        Args:
            limit: NÃƒÂºmero mÃƒÂ¡ximo de resultados a devolver (default 10)

        Returns:
            Lista de MaterialStatsDTO ordenadas por frecuencia descendente
        """

        def _operation(session):
            from sqlalchemy import func

            # Query que cuenta cuÃƒÂ¡ntas veces aparece cada material en iteraciones
            result = session.query(
                Material.codigo_componente,
                func.count(Material.id).label('frecuencia')
            ).join(
                iteracion_material_link,
                Material.id == iteracion_material_link.c.material_id
            ).group_by(
                Material.codigo_componente
            ).order_by(
                func.count(Material.id).desc()
            ).limit(limit).all()

            # Convertir a lista de DTOs
            return [
                MaterialStatsDTO(
                    codigo_componente=row.codigo_componente,
                    frecuencia=int(row.frecuencia)
                ) for row in result
            ]

        return self.safe_execute(_operation) or []