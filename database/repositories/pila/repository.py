# -*- coding: utf-8 -*-
"""
Nombre del Módulo: pila.repository
Descripción: Persistencia y consultas de pilas, lotes, bitácora y flujo de trabajo de fabricación.
"""

from datetime import date
from typing import Callable, List, Optional, Tuple, Dict, Any, Union

from sqlalchemy.orm import Session

from ..base import BaseRepository
from .pila_base_manager import PilaBaseManager
from .pila_crud_manager import PilaCRUDManager
from .pila_workflow_manager import PilaWorkflowManager
from .pila_bitacora_manager import PilaBitacoraManager
from core.dtos import PilaDTO

class PilaRepository(BaseRepository):
    """
    Repositorio para la gestión de pilas de producción.
    Implementa el patrón Fachada delegando en DAO Managers especializados.
    """

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        super().__init__(session_factory)
        
        # Composición de gestores
        self.base = PilaBaseManager(session_factory)
        self.crud = PilaCRUDManager(session_factory)
        self.workflow = PilaWorkflowManager(session_factory, self.base)
        self.bitacora = PilaBitacoraManager(session_factory)
        self._sync_managers()

    def _sync_managers(self) -> None:
        for m in [self.base, self.crud, self.workflow, self.bitacora]:
            m.session_factory = self.session_factory

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in ('session_factory', 'safe_execute'):
            if hasattr(self, 'crud'):
                for m in [self.base, self.crud, self.workflow, self.bitacora]:
                    setattr(m, name, value)

    # Delegación: PilaCRUDManager
    def get_all_pilas(self) -> List[PilaDTO]:
        return self.crud.get_all_pilas()

    def get_all_pilas_with_dates(self) -> List[PilaDTO]:
        return self.crud.get_all_pilas_with_dates()

    def search_pilas(self, query: str) -> List[PilaDTO]:
        return self.crud.search_pilas(query)

    def find_pilas_by_producto_codigo(self, code: str) -> List[PilaDTO]:
        return self.crud.find_pilas_by_producto_codigo(code)

    def find_pila_by_name(self, name: str) -> Optional[int]:
        return self.crud.find_pila_by_name(name)

    def delete_pila(self, pid: int) -> bool:
        return self.crud.delete_pila(pid)

    # Delegación: PilaWorkflowManager
    def save_pila(
        self,
        nombre: str,
        descripcion: str,
        pila_de_calculo: Dict[str, Any],
        production_flow: List[Any],
        simulation_results: List[Any],
        producto_origen_codigo: Optional[str] = None,
    ) -> Union[int, str, bool]:
        return self.workflow.save_pila(
            nombre,
            descripcion,
            pila_de_calculo,
            production_flow,
            simulation_results,
            producto_origen_codigo,
        )

    def update_pila(
        self,
        pila_id: int,
        nombre: Optional[str] = None,
        descripcion: Optional[str] = None,
        pila_de_calculo: Optional[Dict[str, Any]] = None,
        production_flow: Optional[List[Any]] = None,
        simulation_results: Optional[List[Any]] = None,
    ) -> Union[bool, str]:
        return self.workflow.update_pila(
            pila_id,
            nombre=nombre,
            descripcion=descripcion,
            pila_de_calculo=pila_de_calculo,
            production_flow=production_flow,
            simulation_results=simulation_results,
        )

    def load_pila(
        self, pila_id: int
    ) -> Tuple[Optional[PilaDTO], Optional[Dict[str, Any]], Optional[List[Any]], Optional[List[Any]]]:
        return self.workflow.load_pila(pila_id)

    # Delegación: PilaBitacoraManager
    def create_diario_bitacora(self, pila_id: int) -> Optional[int]:
        return self.bitacora.create_diario_bitacora(pila_id)

    def get_diario_bitacora(self, pila_id: int) -> Tuple[Optional[int], List[Tuple[Any, ...]]]:
        return self.bitacora.get_diario_bitacora(pila_id)

    def add_diario_evento(
        self,
        pila_id: int,
        fecha: date,
        dia_numero: int = 1,
        plan: str = "",
        trabajo: str = "",
        notas: str = "",
        plan_previsto: str = "",
        trabajo_realizado: str = "",
    ) -> bool:
        return self.bitacora.add_diario_evento(
            pila_id,
            fecha,
            dia_numero=dia_numero,
            plan=plan,
            trabajo=trabajo,
            notas=notas,
            plan_previsto=plan_previsto,
            trabajo_realizado=trabajo_realizado,
        )

    def update_diario_evento(
        self, bitacora_id: int, fecha: date, plan: str, trabajo: str, notas: str
    ) -> bool:
        return self.bitacora.update_diario_evento(bitacora_id, fecha, plan, trabajo, notas)

    # Métodos de utilidad (compatibilidad con tests y lógica interna)
    def _convert_indices_to_ids(self, production_flow: List[Any]) -> None:
        self.base.convert_indices_to_ids(production_flow)

    def _convert_ids_to_indices(self, production_flow: List[Any]) -> None:
        self.base.convert_ids_to_indices(production_flow)
