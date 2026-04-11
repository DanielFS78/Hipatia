
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: machine.crud_manager
Descripción: Acceso a datos de máquinas (CRUD, mantenimiento, preparación y estadísticas).
"""

from typing import List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..base import BaseRepository
from ...models import Maquina
from core.dtos import MachineDTO

class MachineCRUDManager(BaseRepository):
    """
    Gestor DAO para operaciones CRUD básicas de máquinas.
    
    Proporciona métodos para listar, añadir, actualizar y eliminar registros de
    maquinaria en la base de datos, convirtiéndolos automáticamente a DTOs.
    """

    def get_all_machines(self, include_inactive: bool = False) -> List[MachineDTO]:
        def _operation(session: Session) -> List[MachineDTO]:
            query = session.query(Maquina)
            if not include_inactive: query = query.filter(Maquina.activa == True)
            maquinas = query.order_by(Maquina.nombre).all()
            return [MachineDTO(id=int(m.id or 0), nombre=m.nombre or "", departamento=m.departamento or "", 
                               tipo_proceso=m.tipo_proceso or "", activa=bool(m.activa)) for m in maquinas]
        return self.safe_execute(_operation) or []

    def get_latest_machines(self, limit: int = 10) -> List[MachineDTO]:
        def _operation(session: Session) -> List[MachineDTO]:
            maquinas = session.query(Maquina).order_by(Maquina.id.desc()).limit(limit).all()
            return [MachineDTO(id=int(m.id or 0), nombre=m.nombre or "", departamento=m.departamento or "", 
                               tipo_proceso=m.tipo_proceso or "", activa=bool(m.activa)) for m in maquinas]
        return self.safe_execute(_operation) or []

    def get_machines_by_process_type(self, tipo_proceso: str) -> List[MachineDTO]:
        def _operation(session: Session) -> List[MachineDTO]:
            maquinas = session.query(Maquina).filter(Maquina.tipo_proceso == tipo_proceso, Maquina.activa == True).order_by(Maquina.nombre).all()
            return [MachineDTO(id=int(m.id or 0), nombre=m.nombre or "", departamento=m.departamento or "", 
                               tipo_proceso=m.tipo_proceso or "", activa=bool(m.activa)) for m in maquinas]
        return self.safe_execute(_operation) or []

    def get_distinct_machine_processes(self) -> List[str]:
        def _operation(session: Session) -> List[str]:
            result = session.query(Maquina.tipo_proceso).filter(Maquina.tipo_proceso.isnot(None), Maquina.tipo_proceso != '').distinct().order_by(Maquina.tipo_proceso).all()
            return [row[0] for row in result]
        return self.safe_execute(_operation) or []

    def add_machine(self, nombre: str, departamento: str, tipo_proceso: str, activa: bool = True, machine_id: Optional[int] = None) -> Union[bool, str]:
        def _operation(session: Session) -> Union[bool, str]:
            target = None
            if machine_id is not None:
                target = session.query(Maquina).filter_by(id=machine_id).first()
            if target is None:
                target = session.query(Maquina).filter_by(nombre=nombre).first()
            
            if target:
                if machine_id is None or target.id == machine_id:
                    target.nombre, target.departamento, target.tipo_proceso, target.activa = nombre, departamento, tipo_proceso, activa
                    return True
                return False
            else:
                try:
                    session.add(Maquina(nombre=nombre, departamento=departamento, tipo_proceso=tipo_proceso, activa=activa))
                    session.flush()
                    return True
                except IntegrityError:
                    session.rollback()
                    existing = session.query(Maquina).filter_by(nombre=nombre).first()
                    return True if existing else "UNIQUE_CONSTRAINT"
        res = self.safe_execute(_operation)
        return res if isinstance(res, str) else (res or False)

    def update_machine(self, machine_id: int, nombre: str, departamento: str, tipo_proceso: str, activa: bool) -> bool:
        def _operation(session: Session) -> bool:
            m = session.query(Maquina).filter_by(id=machine_id).first()
            if not m: return False
            m.nombre, m.departamento, m.tipo_proceso, m.activa = nombre, departamento, tipo_proceso, activa
            return True
        return self.safe_execute(_operation) or False

    def delete_machine(self, machine_id: int) -> bool:
        def _operation(session: Session) -> bool:
            m = session.query(Maquina).filter_by(id=machine_id).first()
            if not m: return False
            session.delete(m); return True
        return self.safe_execute(_operation) or False
