# database/repositories/pila/pila_workflow_manager.py

"""
Capa de datos (`pila_workflow_manager`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

import json
import copy
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union, Any, cast
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import Pila, PasoPila
from core.utils.pila_serializer import PilaJSONEncoder, decode_pila_json
from core.dtos import PilaDTO
from .pila_base_manager import PilaBaseManager

class PilaWorkflowManager(BaseRepository):
    """Gestor DAO para la lógica de negocio y persistencia de flujos de trabajo (Pilas)."""

    def __init__(self, session_factory, base_manager: PilaBaseManager):
        super().__init__(session_factory)
        self.base_manager = base_manager

    def save_pila(self, nombre: str, descripcion: str, pila_de_calculo: dict, production_flow: list,
                    simulation_results: list, producto_origen_codigo=None) -> Union[int, str, bool]:
        def _operation(session: Session) -> Union[int, str, bool]:
            if session.query(Pila).filter_by(nombre=nombre).first(): return "UNIQUE_CONSTRAINT"
            flow_copy = copy.deepcopy(production_flow)
            self.base_manager.convert_indices_to_ids(flow_copy)
            for step in flow_copy:
                task_data = step.get('task', {})
                if 'canvas_unique_id' in task_data: del task_data['canvas_unique_id']
                if 'original_task_id' in task_data:
                    if 'id' not in task_data: task_data['id'] = task_data['original_task_id']
                    del task_data['original_task_id']

            nueva_pila = Pila(nombre=nombre, descripcion=descripcion,
                             pila_de_calculo_json=json.dumps(pila_de_calculo, ensure_ascii=False, cls=PilaJSONEncoder),
                             resultados_simulacion=json.dumps(simulation_results, ensure_ascii=False, cls=PilaJSONEncoder) if simulation_results else None,
                             producto_origen_codigo=producto_origen_codigo, fecha_creacion=datetime.now())
            session.add(nueva_pila); session.flush()
            for orden, step in enumerate(flow_copy):
                session.add(PasoPila(pila_id=nueva_pila.id, orden=orden, datos_paso=json.dumps(step, ensure_ascii=False, cls=PilaJSONEncoder)))
            return nueva_pila.id
        return self.safe_execute(_operation) or False

    def update_pila(self, pila_id: int, nombre=None, descripcion=None, pila_de_calculo=None, production_flow=None, simulation_results=None) -> Union[bool, str]:
        def _operation(session: Session):
            p = session.query(Pila).filter_by(id=pila_id).first()
            if not p: return False
            if nombre:
                if nombre != p.nombre and session.query(Pila).filter_by(nombre=nombre).first(): return "UNIQUE_CONSTRAINT"
                p.nombre = nombre
            if descripcion is not None: p.descripcion = descripcion
            if pila_de_calculo is not None: p.pila_de_calculo_json = json.dumps(pila_de_calculo, ensure_ascii=False, cls=PilaJSONEncoder)
            if simulation_results is not None: p.resultados_simulacion = json.dumps(simulation_results, ensure_ascii=False, cls=PilaJSONEncoder)
            if production_flow is not None:
                flow_copy = copy.deepcopy(production_flow)
                self.base_manager.convert_indices_to_ids(flow_copy)
                for step in flow_copy:
                    task_data = step.get('task', {})
                    if 'canvas_unique_id' in task_data:
                        del task_data['canvas_unique_id']
                    if 'original_task_id' in task_data:
                        if 'id' not in task_data:
                            task_data['id'] = task_data['original_task_id']
                        del task_data['original_task_id']
                session.query(PasoPila).filter_by(pila_id=pila_id).delete()
                for orden, step in enumerate(flow_copy):
                    session.add(PasoPila(pila_id=pila_id, orden=orden, datos_paso=json.dumps(step, ensure_ascii=False, cls=PilaJSONEncoder)))

            return True
        return self.safe_execute(_operation) or False

    def load_pila(self, pila_id: int) -> Tuple[Optional[PilaDTO], Optional[Dict], Optional[List], Optional[List]]:
        def _operation(session: Session):
            pila = session.query(Pila).filter_by(id=pila_id).first()
            if not pila: return None, None, None, None
            try:
                calc = json.loads(pila.pila_de_calculo_json, object_hook=decode_pila_json) if pila.pila_de_calculo_json else {}
            except Exception:
                calc = {}
            u = calc.pop('unidades', 1)
            meta = PilaDTO(
                id=pila.id,
                nombre=pila.nombre,
                descripcion=str(pila.descripcion or ""),
                unidades=u,
                producto_origen_codigo=pila.producto_origen_codigo,
                fecha_creacion=pila.fecha_creacion
            )
            try:
                sim = json.loads(pila.resultados_simulacion, object_hook=decode_pila_json) if pila.resultados_simulacion else []
            except Exception:
                sim = []
            pasos_db = session.query(PasoPila).filter_by(pila_id=pila_id).order_by(PasoPila.orden).all()
            flow = []
            for paso in pasos_db:
                if paso.datos_paso:
                    try:
                        flow.append(json.loads(paso.datos_paso, object_hook=decode_pila_json))
                    except Exception:
                        pass
            self.base_manager.convert_ids_to_indices(flow)
            return meta, calc, flow, sim
        res = self.safe_execute(_operation)
        return cast(Tuple[Optional[PilaDTO], Optional[Dict], Optional[List], Optional[List]], res or (None, None, None, None))
