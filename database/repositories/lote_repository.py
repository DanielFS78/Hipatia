# database/repositories/lote_repository.py
"""
Repositorio para la gestión de plantillas de Lote.
"""
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from datetime import datetime

from .base import BaseRepository
from ..models import Lote, Producto, Fabricacion
from core.dtos import LoteDTO, ProductDTO, FabricacionDTO


class LoteRepository(BaseRepository):
    """
    Gestiona las operaciones CRUD para el modelo Lote utilizando SQLAlchemy.
    """

    def create_lote(self, data: Dict[str, Any]) -> Optional[int]:
        """Crea una nueva plantilla de Lote y asocia sus componentes."""

        def _operation(session):
            # Crea la instancia principal del Lote
            nuevo_lote = Lote(
                codigo=data['codigo'],
                descripcion=data['descripcion']
            )

            # Asocia los productos seleccionados
            if data.get('product_codes'):
                productos = session.query(Producto).filter(Producto.codigo.in_(data['product_codes'])).all()
                nuevo_lote.productos = productos

            # Asocia las fabricaciones seleccionadas
            if data.get('fabricacion_ids'):
                fabricaciones = session.query(Fabricacion).filter(Fabricacion.id.in_(data['fabricacion_ids'])).all()
                nuevo_lote.fabricaciones = fabricaciones

            session.add(nuevo_lote)
            session.flush()  # Para obtener el ID antes del commit final
            return nuevo_lote.id

        return self.safe_execute(_operation)

    def get_lote_details(self, lote_id: int) -> Optional[LoteDTO]:
        """Obtiene los detalles de una plantilla de Lote, incluyendo sus componentes."""

        def _operation(session):
            lote = session.query(Lote).options(
                joinedload(Lote.productos),
                joinedload(Lote.fabricaciones)
            ).filter_by(id=lote_id).first()

            if not lote:
                return None
            
            products_dtos = [
                ProductDTO(codigo=p.codigo, descripcion=p.descripcion) 
                for p in lote.productos
            ]
            
            fabs_dtos = [
                FabricacionDTO(id=f.id, codigo=f.codigo, descripcion=f.descripcion)
                for f in lote.fabricaciones
            ]

            return LoteDTO(
                id=lote.id,
                codigo=lote.codigo,
                descripcion=lote.descripcion,
                productos=products_dtos,
                fabricaciones=fabs_dtos
            )

        return self.safe_execute(_operation)

    def search_lotes(self, query: str) -> List[LoteDTO]:
        """Busca plantillas de Lote por código o descripción."""

        def _operation(session):
            lotes = session.query(Lote).filter(
                or_(
                    Lote.codigo.ilike(f"%{query}%"),
                    Lote.descripcion.ilike(f"%{query}%")
                )
            ).order_by(Lote.codigo).all()
            
            return [
                LoteDTO(
                    id=lote.id, 
                    codigo=lote.codigo, 
                    descripcion=lote.descripcion,
                    productos=[],
                    fabricaciones=[]
                ) 
                for lote in lotes
            ]

        return self.safe_execute(_operation) or []

    def update_lote(self, lote_id: int, data: Dict[str, Any]) -> bool:
        """Actualiza una plantilla de Lote existente."""

        def _operation(session):
            lote = session.query(Lote).filter_by(id=lote_id).first()
            if not lote:
                return False

            # Actualizar datos básicos
            lote.codigo = data['codigo']
            lote.descripcion = data['descripcion']

            # Actualizar relaciones
            if 'product_codes' in data:
                productos = session.query(Producto).filter(Producto.codigo.in_(data['product_codes'])).all()
                lote.productos = productos

            if 'fabricacion_ids' in data:
                fabricaciones = session.query(Fabricacion).filter(Fabricacion.id.in_(data['fabricacion_ids'])).all()
                lote.fabricaciones = fabricaciones

            return True

        return self.safe_execute(_operation) or False

    def delete_lote(self, lote_id: int) -> bool:
        """Elimina una plantilla de Lote."""

        def _operation(session):
            lote = session.query(Lote).filter_by(id=lote_id).first()
            if lote:
                session.delete(lote)
                return True
            return False

        return self.safe_execute(_operation) or False