
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: pila.pila_crud_manager
Descripción: Persistencia y consultas de pilas, lotes, bitácora y flujo de trabajo de fabricación.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..base import BaseRepository
from ...models import Pila
from core.dtos import PilaDTO

class PilaCRUDManager(BaseRepository):
    """Gestor DAO para operaciones CRUD básicas de pilas."""

    def get_all_pilas(self) -> List[PilaDTO]:
        def _op(s: Session) -> List[PilaDTO]:
            pilas = s.query(Pila).order_by(Pila.nombre).all()
            return [PilaDTO(id=int(p.id or 0), nombre=str(p.nombre or ""), descripcion=str(p.descripcion or ""), producto_origen_codigo=p.producto_origen_codigo) for p in pilas]
        return self.safe_execute(_op) or []

    def get_all_pilas_with_dates(self) -> List[PilaDTO]:
        import json
        from datetime import datetime
        def _op(session: Session) -> List[PilaDTO]:
            pilas = session.query(Pila).order_by(Pila.fecha_creacion.desc()).all()
            res = []
            for p in pilas:
                start, end = None, None
                if p.resultados_simulacion:
                    try:
                        sim = json.loads(p.resultados_simulacion)
                        dates = []
                        for t in sim:
                            if isinstance(t.get('Inicio'), str): dates.append(datetime.fromisoformat(t['Inicio']))
                            if isinstance(t.get('Fin'), str): dates.append(datetime.fromisoformat(t['Fin']))
                        if dates: start, end = min(dates).date(), max(dates).date()
                    except Exception: pass
                res.append(
                    PilaDTO(
                        id=int(p.id or 0),
                        nombre=str(p.nombre or ""),
                        descripcion=str(p.descripcion or ""),
                        producto_origen_codigo=p.producto_origen_codigo,
                        start_date=start,
                        end_date=end,
                    )
                )
            return res
        return self.safe_execute(_op) or []

    def search_pilas(self, query: str) -> List[PilaDTO]:
        def _op(s: Session) -> List[PilaDTO]:
            pilas = s.query(Pila).filter(or_(Pila.nombre.like(f"%{query}%"), Pila.descripcion.like(f"%{query}%"))).all()
            return [PilaDTO(id=int(p.id or 0), nombre=str(p.nombre or ""), descripcion=str(p.descripcion or ""), producto_origen_codigo=p.producto_origen_codigo) for p in pilas]
        return self.safe_execute(_op) or []

    def find_pilas_by_producto_codigo(self, code: str) -> List[PilaDTO]:
        def _op(s: Session) -> List[PilaDTO]:
            pilas = s.query(Pila).filter_by(producto_origen_codigo=code).order_by(Pila.fecha_creacion.desc()).all()
            return [PilaDTO(id=int(p.id or 0), nombre=str(p.nombre or ""), descripcion=str(p.descripcion or ""), producto_origen_codigo=p.producto_origen_codigo) for p in pilas]
        return self.safe_execute(_op) or []

    def find_pila_by_name(self, name: str) -> Optional[int]:
        def _op(s: Session) -> Optional[int]:
            p = s.query(Pila).filter_by(nombre=name).first()
            return p.id if p else None
        return self.safe_execute(_op)

    def delete_pila(self, pid: int) -> bool:
        def _op(s: Session) -> bool:
            p = s.query(Pila).filter_by(id=pid).first()
            if not p: return False
            s.delete(p); return True
        return self.safe_execute(_op) or False
