
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: pila.pila_bitacora_manager
Descripción: Persistencia y consultas de pilas, lotes, bitácora y flujo de trabajo de fabricación.
"""

from datetime import date
from typing import Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from ..base import BaseRepository
from ...models import DiarioBitacora, EntradaDiario

class PilaBitacoraManager(BaseRepository):
    """Gestor DAO para la bitácora diaria de seguimiento de pilas."""

    def create_diario_bitacora(self, pila_id: int) -> Optional[int]:
        def _op(s: Session) -> Optional[int]:
            b = s.query(DiarioBitacora).filter_by(pila_id=pila_id).first()
            if b: return b.id
            b = DiarioBitacora(pila_id=pila_id); s.add(b); s.flush(); return b.id
        return self.safe_execute(_op)

    def get_diario_bitacora(self, pila_id: int) -> Tuple[Optional[int], List[Tuple[Any, ...]]]:
        def _op(s: Session) -> Tuple[Optional[int], List[Tuple[Any, ...]]]:
            b = s.query(DiarioBitacora).filter_by(pila_id=pila_id).first()
            if not b: return None, []
            entries = s.query(EntradaDiario).filter_by(bitacora_id=b.id).order_by(EntradaDiario.dia_numero).all()
            return b.id, [(e.fecha, e.dia_numero, e.plan_previsto, e.trabajo_realizado, e.notas) for e in entries]
        res = self.safe_execute(_op)
        if res is None:
            return (None, [])
        return res

    def add_diario_evento(self, pila_id: int, fecha: date, dia_numero: int = 1,
                          plan: str = '', trabajo: str = '', notas: str = '',
                          plan_previsto: str = '', trabajo_realizado: str = '') -> bool:
        """Añade o sobreescribe la entrada de un día en la bitácora de la pila."""
        plan_final = plan_previsto or plan
        trabajo_final = trabajo_realizado or trabajo

        def _op(s: Session) -> bool:
            b = s.query(DiarioBitacora).filter_by(pila_id=pila_id).first() or DiarioBitacora(pila_id=pila_id)
            if not b.id: s.add(b); s.flush()
            s.query(EntradaDiario).filter_by(bitacora_id=b.id, fecha=fecha).delete()
            s.add(EntradaDiario(bitacora_id=b.id, fecha=fecha, dia_numero=dia_numero,
                                plan_previsto=plan_final, trabajo_realizado=trabajo_final, notas=notas))
            return True
        return self.safe_execute(_op) or False

    def update_diario_evento(self, bitacora_id: int, fecha: date, plan: str, trabajo: str, notas: str) -> bool:
        def _op(s: Session) -> bool:
            e = s.query(EntradaDiario).filter_by(bitacora_id=bitacora_id, fecha=fecha).first()
            if not e: return False
            e.plan_previsto, e.trabajo_realizado, e.notas = plan, trabajo, notas
            return True
        return self.safe_execute(_op) or False
