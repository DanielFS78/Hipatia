# database/repositories/machine/preparation_manager.py
"""
Capa de datos (`preparation_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from typing import List, Optional, Union, Dict, Any, cast
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import GrupoPreparacion, PreparacionPaso
from core.dtos import PreparationGroupDTO, PreparationStepDTO

class MachinePreparationManager(BaseRepository):
    """Gestor DAO para la configuración de preparación de máquinas."""

    def add_prep_group(self, machine_id: int, name: str, description: str, producto_codigo: Optional[str] = None) -> Union[int, str, None]:
        def _operation(session: Session) -> Union[int, str, None]:
            if session.query(GrupoPreparacion).filter_by(maquina_id=machine_id, nombre=name).first():
                return "UNIQUE_CONSTRAINT"
            nuevo = GrupoPreparacion(maquina_id=machine_id, nombre=name, descripcion=description, producto_codigo=producto_codigo)
            session.add(nuevo); session.flush(); return nuevo.id
        return self.safe_execute(_operation)

    def get_groups_for_machine(self, machine_id: int) -> List[PreparationGroupDTO]:
        def _operation(session: Session) -> List[PreparationGroupDTO]:
            grupos = session.query(GrupoPreparacion).filter_by(maquina_id=machine_id).order_by(GrupoPreparacion.nombre).all()
            return [PreparationGroupDTO(id=int(g.id or 0), nombre=g.nombre or "", descripcion=g.descripcion or "", producto_codigo=g.producto_codigo) for g in grupos]
        return self.safe_execute(_operation) or []

    def get_group_details(self, group_id: int) -> Optional[PreparationGroupDTO]:
        def _operation(session: Session) -> Optional[PreparationGroupDTO]:
            g = session.query(GrupoPreparacion).filter_by(id=group_id).first()
            if not g: return None
            return PreparationGroupDTO(id=int(g.id or 0), nombre=g.nombre or "", descripcion=g.descripcion or "", producto_codigo=g.producto_codigo)
        return self.safe_execute(_operation)

    def update_prep_group(self, group_id: int, name: str, description: str, producto_codigo: Optional[str] = None) -> bool:
        def _operation(session: Session) -> bool:
            g = session.query(GrupoPreparacion).filter_by(id=group_id).first()
            if not g: return False
            g.nombre, g.descripcion, g.producto_codigo = name, description, producto_codigo
            return True
        return self.safe_execute(_operation) or False

    def delete_prep_group(self, group_id: int) -> bool:
        def _operation(session: Session) -> bool:
            g = session.query(GrupoPreparacion).filter_by(id=group_id).first()
            if not g: return False
            session.delete(g); return True
        return self.safe_execute(_operation) or False

    def add_prep_step(self, group_id: int, name: str, time: float, description: str, is_daily: bool) -> Optional[int]:
        def _operation(session: Session) -> Optional[int]:
            p = PreparacionPaso(grupo_id=group_id, nombre=name, tiempo_fase=cast(Any, time), descripcion=description, es_diario=is_daily)
            session.add(p); session.flush(); return p.id
        return self.safe_execute(_operation)

    def update_prep_step(self, step_id: int, data: Dict[str, Any]) -> bool:
        def _operation(session: Session) -> bool:
            p = session.query(PreparacionPaso).filter_by(id=step_id).first()
            if not p: return False
            p.nombre = data.get('nombre', p.nombre)
            p.tiempo_fase = data.get('tiempo_fase', p.tiempo_fase)
            p.descripcion = data.get('descripcion', p.descripcion)
            p.es_diario = data.get('es_diario', p.es_diario)
            return True
        return self.safe_execute(_operation) or False

    def get_steps_for_group(self, group_id: int) -> List[PreparationStepDTO]:
        def _operation(session: Session) -> List[PreparationStepDTO]:
            pasos = session.query(PreparacionPaso).filter_by(grupo_id=group_id).order_by(PreparacionPaso.id).all()
            return [PreparationStepDTO(id=int(p.id or 0), nombre=p.nombre or "", tiempo_fase=float(p.tiempo_fase or 0.0), descripcion=p.descripcion or "", es_diario=bool(p.es_diario)) for p in pasos]
        return self.safe_execute(_operation) or []

    def delete_prep_step(self, step_id: int) -> bool:
        def _operation(session: Session) -> bool:
            p = session.query(PreparacionPaso).filter_by(id=step_id).first()
            if not p: return False
            session.delete(p); return True
        return self.safe_execute(_operation) or False

    def get_prep_step_details(self, step_id: int) -> Optional[PreparationStepDTO]:
        def _operation(session: Session) -> Optional[PreparationStepDTO]:
            p = session.query(PreparacionPaso).get(step_id)
            if not p: return None
            return PreparationStepDTO(id=int(p.id or 0), nombre=p.nombre or "", tiempo_fase=float(p.tiempo_fase or 0.0), descripcion=p.descripcion or "", es_diario=bool(p.es_diario))
        return cast(Optional[PreparationStepDTO], self.safe_execute(_operation))
