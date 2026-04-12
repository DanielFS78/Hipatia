# -*- coding: utf-8 -*-
"""
Nombre del Módulo: preproceso.preproceso_manager

Descripción: Define protocolos o tipos principales: ``PreprocesoManager``. Gestor DAO para la entidad Preproceso. Integración típica con: ``sqlalchemy``, ``models``, ``core``, ``base``.
"""

from typing import List
from sqlalchemy.orm import Session, joinedload
from ...models import Preproceso, Material
from core.dtos import PreprocesoDTO, ComponenteDTO
from ..base import BaseRepository


class PreprocesoManager(BaseRepository):
    """
    Gestor DAO para la entidad Preproceso.
    Hereda de BaseRepository para utilizar safe_execute.
    """

    def get_all_preprocesos(self) -> List[PreprocesoDTO]:
        """Obtiene todos los preprocesos con sus materiales como DTOs."""

        def _operation(session: Session) -> List[PreprocesoDTO]:
            preprocesos_obj = session.query(Preproceso).options(
                joinedload(Preproceso.materiales)
            ).order_by(Preproceso.nombre).all()

            results = []
            for p in preprocesos_obj:
                componentes = [
                    ComponenteDTO(id=c.id, descripcion=c.descripcion_componente or "") 
                    for c in p.materiales
                ]
                dto = PreprocesoDTO(
                    id=p.id,
                    nombre=p.nombre or "",
                    descripcion=p.descripcion or "",
                    tiempo=p.tiempo or 0,
                    componentes=componentes
                )
                results.append(dto)
            return results

        return self.safe_execute(_operation) or []

    def get_preproceso_components(self, preproceso_id: int) -> List[ComponenteDTO]:
        """
        Obtiene los componentes (materiales) asociados a un preproceso específico.
        """

        def _operation(session: Session) -> List[ComponenteDTO]:
            preproceso = session.query(Preproceso).options(
                joinedload(Preproceso.materiales)
            ).filter_by(id=preproceso_id).first()

            if not preproceso:
                if self.logger:
                    self.logger.warning(f"No se encontró preproceso con ID {preproceso_id}")
                return []

            componentes = sorted(
                [ComponenteDTO(id=mat.id, descripcion=mat.descripcion_componente or "") for mat in preproceso.materiales],
                key=lambda x: x.descripcion
            )

            return componentes

        return self.safe_execute(_operation) or []

    def create_preproceso(self, data: PreprocesoDTO) -> bool:
        """Crea un nuevo preproceso y lo asocia con sus materiales."""

        def _operation(session: Session) -> bool:
            nuevo_preproceso = Preproceso(
                nombre=data.nombre,
                descripcion=data.descripcion,
                tiempo=data.tiempo
            )
            if data.componentes_ids:
                materiales = session.query(Material).filter(Material.id.in_(data.componentes_ids)).all()
                nuevo_preproceso.materiales = materiales

            session.add(nuevo_preproceso)
            return True

        return self.safe_execute(_operation) or False

    def update_preproceso(self, preproceso_id: int, data: PreprocesoDTO) -> bool:
        """Actualiza un preproceso existente."""

        def _operation(session: Session) -> bool:
            preproceso = session.query(Preproceso).filter_by(id=preproceso_id).first()
            if not preproceso: return False

            preproceso.nombre = data.nombre
            preproceso.descripcion = data.descripcion
            preproceso.tiempo = data.tiempo

            if data.componentes_ids is not None:
                materiales = session.query(Material).filter(Material.id.in_(data.componentes_ids)).all()
                preproceso.materiales = materiales

            return True

        return self.safe_execute(_operation) or False

    def delete_preproceso(self, preproceso_id: int) -> bool:
        """Elimina un preproceso y sus relaciones."""

        def _operation(session: Session) -> bool:
            preproceso = session.query(Preproceso).filter_by(id=preproceso_id).first()
            if preproceso:
                session.delete(preproceso)
                return True
            return False

        return self.safe_execute(_operation) or False
