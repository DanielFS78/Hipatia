# database/repositories/material_repository.py
"""
Repositorio para la gestión de materiales y componentes.
Consolidado mediante absorción del mixin de enlaces.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import Material, ProductIteration

if TYPE_CHECKING:
    from core.dtos import MaterialDTO, MaterialStatsDTO


class MaterialRepository(BaseRepository):
    """
    Repositorio para gestión de materiales.
    Maneja la persistencia y relaciones de componentes industriales.
    """

    def get_all_materials(self) -> List[MaterialDTO]:
        """Obtiene todos los materiales registrados como DTOs."""

        def _operation(session: Session) -> List[MaterialDTO]:
            from core.dtos import MaterialDTO
            materials = session.query(Material).all()
            return [
                MaterialDTO(
                    id=m.id,
                    codigo_componente=m.codigo_componente,
                    descripcion_componente=m.descripcion_componente or ""
                ) for m in materials
            ]

        return self.safe_execute(_operation) or []

    def get_material_by_code(self, codigo: str) -> Optional[MaterialDTO]:
        """Busca un material por su código único."""

        def _operation(session: Session) -> Optional[MaterialDTO]:
            from core.dtos import MaterialDTO
            m = session.query(Material).filter_by(codigo_componente=codigo).first()
            if not m:
                return None
            return MaterialDTO(
                id=m.id,
                codigo_componente=m.codigo_componente,
                descripcion_componente=m.descripcion_componente or ""
            )

        return self.safe_execute(_operation)

    def search_materials(self, term: str) -> List[MaterialDTO]:
        """
        Busca materiales por código o descripción.
        Si el término es None o vacío, devuelve todos.
        Si el término tiene menos de 2 caracteres (y no es vacío), devuelve vacío.
        """
        if term is not None and 0 < len(term) < 2:
            return []

        def _operation(session: Session) -> List[MaterialDTO]:
            from sqlalchemy import or_
            from core.dtos import MaterialDTO

            query = session.query(Material)
            if term:
                query = query.filter(
                    or_(
                        Material.codigo_componente.ilike(f"%{term}%"),
                        Material.descripcion_componente.ilike(f"%{term}%"),
                    )
                )

            materials = query.limit(50).all()
            return [
                MaterialDTO(
                    id=m.id,
                    codigo_componente=m.codigo_componente,
                    descripcion_componente=m.descripcion_componente or ""
                ) for m in materials
            ]

        return self.safe_execute(_operation) or []

    # =========================================================================
    # OPERACIONES CRUD (GESTIÓN)
    # =========================================================================

    def add_material(self, codigo: str, descripcion: str) -> Optional[int]:
        """Añade un material o actualiza su descripción si ya existe."""

        def _operation(session: Session) -> Optional[int]:
            material = session.query(Material).filter_by(codigo_componente=codigo).first()
            if material:
                if material.descripcion_componente != descripcion:
                    material.descripcion_componente = descripcion
                return material.id

            nuevo = Material(codigo_componente=codigo, descripcion_componente=descripcion)
            session.add(nuevo)
            session.flush()
            return nuevo.id

        return self.safe_execute(_operation)

    def update_material(self, material_id: int, nuevo_codigo: str, nueva_descripcion: str) -> bool:
        """Actualiza el código y descripción de un material."""

        def _operation(session: Session) -> bool:
            material = session.query(Material).filter_by(id=material_id).first()
            if not material:
                return False

            # Verificar si el nuevo código ya lo tiene otro material
            existente = session.query(Material).filter_by(codigo_componente=nuevo_codigo).first()
            if existente and existente.id != material_id:
                self.logger.warning(f"No se puede actualizar material al código {nuevo_codigo} (ya existe).")
                return False

            material.codigo_componente = nuevo_codigo
            material.descripcion_componente = nueva_descripcion
            return True

        return self.safe_execute(_operation) or False

    def delete_material(self, material_id: int) -> bool:
        """Elimina un material por su ID."""

        def _operation(session: Session) -> bool:
            material = session.query(Material).filter_by(id=material_id).first()
            if not material:
                return False
            session.delete(material)
            return True

        return self.safe_execute(_operation) or False

    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================

    def get_problematic_components_stats(self, limit: int = 10) -> List[MaterialStatsDTO]:
        """Obtiene estadísticas de componentes más frecuentes en iteraciones de fallo."""

        def _operation(session: Session) -> List[MaterialStatsDTO]:
            from sqlalchemy import func
            from core.dtos import MaterialStatsDTO
            from ..models.base import iteracion_material_link

            # Query para contar apariciones de cada material en iteraciones
            # se usa la tabla de enlace iteracion_material_link
            counts = (
                session.query(
                    Material.codigo_componente,
                    func.count(iteracion_material_link.c.iteracion_id).label("frecuencia")
                )
                .join(iteracion_material_link, Material.id == iteracion_material_link.c.material_id)
                .group_by(Material.codigo_componente)
                .order_by(func.count(iteracion_material_link.c.iteracion_id).desc())
                .limit(limit)
                .all()
            )

            return [MaterialStatsDTO(codigo_componente=r[0], frecuencia=r[1]) for r in counts]

        return self.safe_execute(_operation) or []

    # =========================================================================
    # GESTIÓN DE ENLACES (MIXIN ABSORBIDO)
    # =========================================================================

    def link_material_to_product(self, producto_codigo: str, material_id: int) -> bool:
        """Vincula un material a un producto."""

        def _operation(session: Session) -> bool:
            from ..models import Producto
            from sqlalchemy.orm import joinedload

            producto = session.query(Producto).options(
                joinedload(Producto.materiales)
            ).filter_by(codigo=producto_codigo).first()

            material = session.query(Material).filter_by(id=material_id).first()

            if not producto or not material:
                return False

            if material not in producto.materiales:
                producto.materiales.append(material)
            return True

        return self.safe_execute(_operation) or False

    def unlink_material_from_product(self, producto_codigo: str, material_id: int) -> bool:
        """Desvincula un material de un producto."""

        def _operation(session: Session) -> bool:
            from ..models import Producto
            from sqlalchemy.orm import joinedload

            producto = session.query(Producto).options(
                joinedload(Producto.materiales)
            ).filter_by(codigo=producto_codigo).first()

            if not producto:
                return False

            material = session.query(Material).filter_by(id=material_id).first()
            if not material:
                return True # Idempotencia

            if material in producto.materiales:
                producto.materiales.remove(material)
            return True

        return self.safe_execute(_operation) or False

    def link_material_to_iteration(self, iteracion_id: int, material_id: int) -> bool:
        """Vincula un material a una iteración específica."""

        def _operation(session: Session) -> bool:
            from sqlalchemy.orm import joinedload

            iteracion = (
                session.query(ProductIteration)
                .options(joinedload(ProductIteration.materiales))
                .filter_by(id=iteracion_id)
                .first()
            )
            material = session.query(Material).filter_by(id=material_id).first()
            if not iteracion or not material:
                self.logger.warning(f"No se pudo vincular Material {material_id} a Iteración {iteracion_id}.")
                return False
            if material not in iteracion.materiales:
                iteracion.materiales.append(material)
                self.logger.info(f"Material {material_id} vinculado a la iteración {iteracion_id}.")
            return True

        return self.safe_execute(_operation) or False

    def delete_material_link_from_iteration(self, iteracion_id: int, material_id: int) -> bool:
        """Desvincula un material de una iteración (alias para unlink_material_from_iteration)."""
        return self.unlink_material_from_iteration(iteracion_id, material_id)

    def unlink_material_from_iteration(self, iteracion_id: int, material_id: int) -> bool:
        """Desvincula un material de una iteración."""

        def _operation(session: Session) -> bool:
            from sqlalchemy.orm import joinedload

            iteracion = (
                session.query(ProductIteration)
                .options(joinedload(ProductIteration.materiales))
                .filter_by(id=iteracion_id)
                .first()
            )
            material = session.query(Material).filter_by(id=material_id).first()
            if not iteracion:
                self.logger.warning(f"No se encontró iteración ID {iteracion_id}.")
                return False
            if not material:
                self.logger.warning(f"No se encontró material ID {material_id}.")
                return True
            if material in iteracion.materiales:
                iteracion.materiales.remove(material)
                self.logger.info(f"Material ID {material_id} desvinculado de la iteración {iteracion_id}.")
            else:
                self.logger.info(f"Material ID {material_id} no estaba vinculado a la iteración {iteracion_id}.")
            return True

        return self.safe_execute(_operation) or False

    def _get_default_error_value(self) -> None:
        return None