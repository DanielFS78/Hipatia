# -*- coding: utf-8 -*-
"""
Nombre del Módulo: preproceso.fabricacion_manager

Descripción: Define protocolos o tipos principales: ``FabricacionManager``. Gestor DAO para la entidad Fabricacion. Integración típica con: ``sqlalchemy``, ``models``, ``core``, ``base``.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from ...models import Fabricacion, Preproceso
from core.dtos import FabricacionDTO, PreprocesoDTO, FabricacionProductoDTO
from ..base import BaseRepository


class FabricacionManager(BaseRepository):
    """
    Gestor DAO para la entidad Fabricacion.
    Hereda de BaseRepository para aprovechar el patrón de ejecución segura `safe_execute`.
    
    Esta clase implementa la Fase 12C (DTO-First), eliminando el paso de diccionarios
    o tuplas crudas entre la base de datos y las capas superiores. Todas las
    operaciones de lectura y escritura se normalizan mediante `FabricacionDTO`.
    """

    def get_all_fabricaciones(self) -> List[FabricacionDTO]:
        """
        Obtiene todas las fabricaciones registradas en formato DTO.
        
        Realiza una consulta ordenada por ID descendente para mostrar primero las
        más recientes. Cada registro de SQLAlchemy se mapea a un `FabricacionDTO`
        para garantizar el aislamiento de la capa de persistencia.
        """
        def _operation(session: Session) -> List[FabricacionDTO]:
            fabricaciones = session.query(Fabricacion).order_by(Fabricacion.id.desc()).all()
            
            results = []
            for f in fabricaciones:
                results.append(FabricacionDTO(
                    id=f.id,
                    codigo=f.codigo or "",
                    descripcion=f.descripcion or ""
                ))
            return results

        return self.safe_execute(_operation) or []

    def get_products_for_fabricacion(self, fabricacion_id: int) -> List[FabricacionProductoDTO]:
        """
        Recupera la lista de productos asociados a una fabricación específica.
        
        Utiliza SQL directo a la tabla puente `fabricacion_productos` para optimizar
        la recuperación. Cada fila se encapsula en un `FabricacionProductoDTO` que
        incluye el código del producto y la cantidad asignada.
        """
        def _operation(session: Session) -> List[FabricacionProductoDTO]:
            sql_query = text("""
                SELECT producto_codigo, cantidad
                FROM fabricacion_productos
                WHERE fabricacion_id = :fab_id
                ORDER BY producto_codigo
            """)

            result = session.execute(sql_query, {"fab_id": fabricacion_id}).fetchall()
            return [
                FabricacionProductoDTO(producto_codigo=row[0], cantidad=row[1]) 
                for row in result
            ]

        return self.safe_execute(_operation) or []

    def add_product_to_fabricacion(self, fabricacion_id: int, producto_codigo: str, cantidad: int = 1) -> bool:
        """Añade un producto a una fabricación o actualiza su cantidad si ya existe."""
        def _operation(session: Session) -> bool:
            try:
                sql_insert_or_replace = text("""
                    INSERT OR REPLACE INTO fabricacion_productos
                    (fabricacion_id, producto_codigo, cantidad)
                    VALUES (:fab_id, :prod_code, :qty)
                """)

                session.execute(sql_insert_or_replace, {
                    "fab_id": fabricacion_id,
                    "prod_code": producto_codigo,
                    "qty": cantidad
                })
                return True
            except IntegrityError:
                session.rollback()
                return False
            except Exception:
                session.rollback()
                return False

        return self.safe_execute(_operation) or False

    def set_products_for_fabricacion(self, fabricacion_id: int, products: List[FabricacionProductoDTO]) -> bool:
        """
        Sobrescribe completamente la lista de productos de una fabricación.
        
        Implementa una operación atómica de 'limpiar y reemplazar':
        1. Elimina todas las asociaciones actuales de la fabricación mediante SQL DELETE.
        2. Inserta los nuevos productos contenidos en la lista de `FabricacionProductoDTO`.
        Si ocurre algún error, se realiza un rollback automático para mantener la integridad.
        """
        def _operation(session: Session) -> bool:
            try:
                delete_sql = text("DELETE FROM fabricacion_productos WHERE fabricacion_id = :fab_id")
                session.execute(delete_sql, {"fab_id": fabricacion_id})

                if products:
                    insert_sql = text("""
                        INSERT INTO fabricacion_productos (fabricacion_id, producto_codigo, cantidad)
                        VALUES (:fab_id, :prod_code, :qty)
                    """)
                    for p in products:
                        session.execute(insert_sql, {
                            "fab_id": fabricacion_id,
                            "prod_code": p.producto_codigo,
                            "qty": p.cantidad
                        })
                return True
            except Exception:
                session.rollback()
                return False

        return self.safe_execute(_operation) or False

    def get_fabricacion_by_codigo(self, codigo: str) -> Optional[FabricacionDTO]:
        """Busca una única Orden de Fabricación por su código exacto."""
        def _operation(session: Session) -> Optional[FabricacionDTO]:
            fab = session.query(Fabricacion).filter(Fabricacion.codigo == codigo).first()
            if fab:
                return FabricacionDTO(id=fab.id, codigo=fab.codigo, descripcion=fab.descripcion or "")
            return None

        return self.safe_execute(_operation)

    def search_fabricaciones(self, query: str) -> List[FabricacionDTO]:
        """Busca fabricaciones por código o descripción."""
        def _operation(session: Session) -> List[FabricacionDTO]:
            results = session.query(Fabricacion).filter(
                or_(
                    Fabricacion.codigo.ilike(f"%{query}%"),
                    Fabricacion.descripcion.ilike(f"%{query}%")
                )
            ).order_by(Fabricacion.id.desc()).all()
            return [FabricacionDTO(id=f.id, codigo=f.codigo or "", descripcion=f.descripcion or "") for f in results]

        return self.safe_execute(_operation) or []

    def get_fabricacion_by_id(self, fabricacion_id: int) -> Optional[FabricacionDTO]:
        """Obtiene una fabricación con sus preprocesos."""
        def _operation(session: Session) -> Optional[FabricacionDTO]:
            fabricacion = session.query(Fabricacion).options(
                joinedload(Fabricacion.preprocesos)
            ).filter_by(id=fabricacion_id).first()

            if fabricacion:
                preprocesos = [
                    PreprocesoDTO(id=p.id, nombre=p.nombre, descripcion=p.descripcion or "", tiempo=p.tiempo, componentes=[]) 
                    for p in fabricacion.preprocesos
                ]
                return FabricacionDTO(id=fabricacion.id, codigo=fabricacion.codigo, descripcion=fabricacion.descripcion or "", preprocesos=preprocesos)
            return None

        return self.safe_execute(_operation)

    def create_fabricacion_with_preprocesos(self, data: FabricacionDTO) -> bool:
        """Crea una fabricación y le asigna sus preprocesos."""
        def _operation(session: Session) -> bool:
            nueva_fabricacion = Fabricacion(codigo=data.codigo, descripcion=data.descripcion)
            if data.preprocesos_ids:
                preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(data.preprocesos_ids)).all()
                nueva_fabricacion.preprocesos = preprocesos
            session.add(nueva_fabricacion)
            return True

        return self.safe_execute(_operation) or False

    def update_fabricacion_and_preprocesos(self, fabricacion_id: int, data: FabricacionDTO, preproceso_ids: Optional[List[int]]) -> bool:
        """Actualiza los datos de una fabricación y su lista de preprocesos."""
        def _operation(session: Session) -> bool:
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not fabricacion: return False
            fabricacion.codigo = data.codigo
            fabricacion.descripcion = data.descripcion
            if preproceso_ids is not None:
                nuevos_preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(preproceso_ids)).all()
                fabricacion.preprocesos = nuevos_preprocesos
            return True

        return self.safe_execute(_operation) or False

    def delete_fabricacion(self, fabricacion_id: int) -> bool:
        """Elimina una fabricación de la base de datos."""
        def _operation(session: Session) -> bool:
            from ...models import fabricacion_preproceso_link
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if fabricacion:
                session.execute(fabricacion_preproceso_link.delete().where(fabricacion_preproceso_link.c.fabricacion_id == fabricacion_id))
                session.delete(fabricacion)
                return True
            return False

        return self.safe_execute(_operation) or False

    def get_latest_fabricaciones(self, limit: int = 5) -> List[FabricacionDTO]:
        """Obtiene las últimas fabricaciones añadidas."""
        def _operation(session: Session) -> List[FabricacionDTO]:
            fabricaciones = session.query(Fabricacion).order_by(Fabricacion.id.desc()).limit(limit).all()
            return [FabricacionDTO(id=f.id, codigo=f.codigo or "", descripcion=f.descripcion or "") for f in fabricaciones]
        
        return self.safe_execute(_operation) or []

    def get_preprocesos_by_fabricacion(self, fabricacion_id: int) -> List[PreprocesoDTO]:
        """Obtiene los preprocesos de una fabricación."""
        def _operation(session: Session) -> List[PreprocesoDTO]:
            f = session.query(Fabricacion).options(joinedload(Fabricacion.preprocesos)).filter_by(id=fabricacion_id).first()
            if f:
                return [PreprocesoDTO(id=p.id, nombre=p.nombre, descripcion=p.descripcion or "", tiempo=p.tiempo, componentes=[]) for p in f.preprocesos]
            return []
        
        return self.safe_execute(_operation) or []

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: List[int]) -> bool:
        """Actualiza solamente la lista de preprocesos de una fabricación."""
        def _operation(session: Session) -> bool:
            fabricacion = session.query(Fabricacion).filter_by(id=fabricacion_id).first()
            if not fabricacion: return False
            nuevos_preprocesos = session.query(Preproceso).filter(Preproceso.id.in_(preproceso_ids)).all()
            fabricacion.preprocesos = nuevos_preprocesos
            return True

        return self.safe_execute(_operation) or False
