# database/repositories/product_repository.py
"""
Repositorio para la gestión de productos.
Incluye la persistencia de productos y la parte relacionada con fabricación en el mismo repositorio.
"""
from __future__ import annotations
from typing import List, Optional, Any
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models import Producto, Subfabricacion, ProcesoMecanico
from ..models.base import fabricacion_productos
from core.dtos import (
    MaterialDTO,
    ProductDTO,
    ProductDetailsDTO,
    SubfabricacionDTO,
    ProcesoMecanicoDTO,
)
from .product_repository_helpers import (
    to_product_dto,
    to_subfabricacion_dto,
    to_proceso_mecanico_dto,
    to_material_dto,
    normalize_machine_id,
)


class ProductRepository(BaseRepository):
    """
    Repositorio para gestión de productos.
    Maneja la persistencia de artículos, escandallos y relaciones de fabricación.
    """

    def add_product(self, data: dict, sub_data: list | None = None) -> bool:
        """Añade un producto, subfabricaciones y procesos mecánicos."""

        def _operation(session: Session) -> bool:
            p = session.query(Producto).filter_by(codigo=data["codigo"]).first()
            if p:
                self.logger.warning(f"Producto {data['codigo']} ya existe.")
                return False

            # Separar procesos mecánicos si vienen en data
            procesos_data = data.pop("procesos_mecanicos", [])

            nuevo_p = Producto(**data)
            session.add(nuevo_p)
            session.flush()

            # Gestión de subfabricaciones
            if sub_data:
                for sub in sub_data:
                    if hasattr(sub, "descripcion"):
                        nueva_sub = Subfabricacion(
                            producto_codigo=nuevo_p.codigo,
                            descripcion=sub.descripcion,
                            tiempo=sub.tiempo,
                            tipo_trabajador=sub.tipo_trabajador,
                        )
                    else:
                        sub_copy = dict(sub)
                        sub_copy["maquina_id"] = normalize_machine_id(sub_copy.get("maquina_id"))
                        nueva_sub = Subfabricacion(
                            producto_codigo=nuevo_p.codigo,
                            **sub_copy
                        )
                    session.add(nueva_sub)

            # Gestión de procesos mecánicos
            for proc in procesos_data:
                if hasattr(proc, "nombre"):
                    nuevo_proc = ProcesoMecanico(
                        producto_codigo=nuevo_p.codigo,
                        nombre=proc.nombre,
                        descripcion=proc.descripcion,
                        tiempo=proc.tiempo,
                        tipo_trabajador=proc.tipo_trabajador,
                    )
                else:
                    nuevo_proc = ProcesoMecanico(
                        producto_codigo=nuevo_p.codigo,
                        **proc
                    )
                session.add(nuevo_proc)

            self.logger.info(f"Producto {data['codigo']} añadido con éxito.")
            return True

        return self.safe_execute(_operation) or False

    def update_product(self, codigo_original: str, data: dict, sub_data: list | None = None) -> bool:
        """Actualiza un producto, subfabricaciones y procesos mecánicos."""

        def _operation(session: Session) -> bool:
            p = session.query(Producto).filter_by(codigo=codigo_original).first()
            if not p:
                return False

            # Separar procesos mecánicos si vienen en data
            procesos_data = data.pop("procesos_mecanicos", None)

            # Actualizar campos del producto
            for key, value in data.items():
                setattr(p, key, value)

            # Gestionar subfabricaciones (reemplazo total)
            if sub_data is not None:
                session.query(Subfabricacion).filter_by(producto_codigo=codigo_original).delete()
                for sub in sub_data:
                    if hasattr(sub, "descripcion"):
                        nueva_sub = Subfabricacion(
                            producto_codigo=p.codigo,
                            descripcion=sub.descripcion,
                            tiempo=sub.tiempo,
                            tipo_trabajador=sub.tipo_trabajador,
                        )
                    else:
                        sub_copy = dict(sub)
                        sub_copy["maquina_id"] = normalize_machine_id(sub_copy.get("maquina_id"))
                        nueva_sub = Subfabricacion(
                            producto_codigo=p.codigo,
                            **sub_copy
                        )
                    session.add(nueva_sub)

            # Gestionar procesos mecánicos (reemplazo total si se provee)
            if procesos_data is not None:
                session.query(ProcesoMecanico).filter_by(producto_codigo=codigo_original).delete()
                for proc in procesos_data:
                    if hasattr(proc, "nombre"):
                        nuevo_proc = ProcesoMecanico(
                            producto_codigo=p.codigo,
                            nombre=proc.nombre,
                            descripcion=proc.descripcion,
                            tiempo=proc.tiempo,
                            tipo_trabajador=proc.tipo_trabajador,
                        )
                    else:
                        nuevo_proc = ProcesoMecanico(
                            producto_codigo=p.codigo,
                            **proc
                        )
                    session.add(nuevo_proc)

            self.logger.info(f"Producto {codigo_original} actualizado.")
            return True

        return self.safe_execute(_operation) or False

    def delete_product(self, codigo: str) -> bool:
        """Elimina un producto por su código."""

        def _operation(session: Session) -> bool:
            p = session.query(Producto).filter_by(codigo=codigo).first()
            if not p:
                return False
            session.delete(p)
            self.logger.info(f"Producto {codigo} eliminado.")
            return True

        return self.safe_execute(_operation) or False

    def get_all_products(self) -> List[ProductDTO]:
        """Obtiene la lista completa de productos registrados."""

        def _operation(session: Session) -> List[ProductDTO]:
            productos = session.query(Producto).order_by(Producto.codigo).all()
            return [to_product_dto(p) for p in productos]

        return self.safe_execute(_operation) or []

    def get_product_by_code(self, codigo: str) -> Optional[ProductDTO]:
        """Busca un producto por su código único."""

        def _operation(session: Session) -> Optional[ProductDTO]:
            producto = session.query(Producto).filter_by(codigo=codigo).first()
            if not producto:
                return None
            return to_product_dto(producto)

        return self.safe_execute(_operation)

    def get_latest_products(self, limit: int = 10) -> List[ProductDTO]:
        """Obtiene los últimos productos (orden descendente por código)."""

        def _operation(session: Session) -> List[ProductDTO]:
            productos = (
                session.query(Producto).order_by(Producto.codigo.desc()).limit(limit).all()
            )
            return [to_product_dto(p) for p in productos]

        return self.safe_execute(_operation) or []

    def get_product_details(self, codigo_producto: str) -> ProductDetailsDTO:
        """Obtiene detalles, subfabricaciones y procesos de un producto."""

        def _operation(session: Session) -> ProductDetailsDTO:
            p = session.query(Producto).filter_by(codigo=codigo_producto).first()
            p_dto = to_product_dto(p) if p else None

            subfabs = (
                session.query(Subfabricacion).filter_by(producto_codigo=codigo_producto).all()
            )
            procesos = (
                session.query(ProcesoMecanico).filter_by(producto_codigo=codigo_producto).all()
            )

            return ProductDetailsDTO(
                producto=p_dto,
                subfabricaciones=[to_subfabricacion_dto(s) for s in subfabs],
                procesos_mecanicos=[to_proceso_mecanico_dto(pr) for pr in procesos],
            )

        return self.safe_execute(_operation) or ProductDetailsDTO(None, [], [])

    def search_products(self, term: str) -> List[ProductDTO]:
        """
        Busca productos por código o descripción.
        Si el término es None o vacío, devuelve todos.
        Si el término tiene menos de 2 caracteres (y no es vacío), devuelve vacío.
        """
        if term is not None and 0 < len(term) < 2:
            return []

        def _operation(session: Session) -> List[ProductDTO]:
            from sqlalchemy import or_

            query = session.query(Producto)
            if term:
                query = query.filter(
                    or_(
                        Producto.codigo.ilike(f"%{term}%"),
                        Producto.descripcion.ilike(f"%{term}%"),
                    )
                )

            productos = query.order_by(Producto.codigo).limit(50).all()
            return [to_product_dto(p) for p in productos]

        return self.safe_execute(_operation) or []

    def get_materials_for_product(self, producto_codigo: str) -> List[MaterialDTO]:
        """Obtiene la lista de materiales vinculados a un producto."""

        def _operation(session: Session) -> List[MaterialDTO]:
            from sqlalchemy.orm import joinedload
            from core.dtos import MaterialDTO

            p = session.query(Producto).options(
                joinedload(Producto.materiales)
            ).filter_by(codigo=producto_codigo).first()

            if not p:
                return []

            return [to_material_dto(m) for m in p.materiales]

        return self.safe_execute(_operation) or []

    # =========================================================================
    # GESTIÓN DE FABRICACIÓN
    # =========================================================================

    def get_products_by_fabricacion(self, fabricacion_id: int) -> List[ProductDTO]:
        """
        Obtiene los productos asociados a una fabricación.
        Mantiene compatibilidad con DatabaseManager.
        """

        def _operation(session: Session) -> List[ProductDTO]:
            rows = (
                session.query(Producto, fabricacion_productos.c.cantidad)
                .join(fabricacion_productos, Producto.codigo == fabricacion_productos.c.producto_codigo)
                .filter(fabricacion_productos.c.fabricacion_id == fabricacion_id)
                .order_by(Producto.codigo)
                .all()
            )
            return [to_product_dto(p) for p, _cantidad in rows]

        return self.safe_execute(_operation) or []

    def _get_default_error_value(self) -> None:
        return None