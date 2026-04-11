# database/models/worker.py

"""
Nombre del Módulo: database.models.worker

Descripción: Define protocolos o tipos principales: ``Trabajador``, ``TrabajadorPilaAnotacion``. Modelo que representa a un operario o administrador del sistema. Integración típica con: ``sqlalchemy``, ``base``, ``datetime``.
"""

from sqlalchemy import Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .tracking import IncidenciaLog, TrabajoLog
    from .inventory import Pila
    from .fabrication import Fabricacion
from .base import Base, trabajador_fabricacion_link
from datetime import datetime, timezone

class Trabajador(Base):
    """
    Modelo que representa a un operario o administrador del sistema.
    
    Gestiona la autenticación, roles por departamento y la vinculación
    con los registros de trabajo e incidencias en planta.
    
    Diccionario de Datos:
        - tipo_trabajador (int): Nivel de capacidad técnica para asignaciones automáticas.
          1 = Operario Básico (operaciones estándar).
          2 = Especialista (maquinaria específica).
          3 = Experto (resolver cuellos de botella y supervisión global).
          El optimizador equiparará este nivel con el mínimo exigido por Producto.
    """
    __tablename__ = 'trabajadores'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notas: Mapped[Optional[str]] = mapped_column(Text)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String)
    role: Mapped[Optional[str]] = mapped_column(String)
    tipo_trabajador: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Relaciones
    anotaciones: Mapped[List["TrabajadorPilaAnotacion"]] = relationship("TrabajadorPilaAnotacion", back_populates="trabajador", cascade="all, delete-orphan")

    # Relaciones de trazabilidad
    fabricaciones_asignadas: Mapped[List["Fabricacion"]] = relationship(
        "Fabricacion",
        secondary=trabajador_fabricacion_link,
        back_populates="trabajadores_asignados"
    )
    trabajo_logs: Mapped[List["TrabajoLog"]] = relationship("TrabajoLog", back_populates="trabajador")
    incidencias: Mapped[List["IncidenciaLog"]] = relationship("IncidenciaLog", back_populates="trabajador")

    def __repr__(self) -> str:
        return f"<Trabajador(id={self.id}, nombre='{self.nombre_completo}')>"

class TrabajadorPilaAnotacion(Base):
    __tablename__ = 'trabajador_pila_anotaciones'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    worker_id: Mapped[int] = mapped_column(Integer, ForeignKey('trabajadores.id'), nullable=False)
    pila_id: Mapped[int] = mapped_column(Integer, ForeignKey('pilas.id'), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    anotacion: Mapped[str] = mapped_column(Text, nullable=False)

    # Relaciones inversas
    trabajador: Mapped["Trabajador"] = relationship("Trabajador", back_populates="anotaciones")
    pila: Mapped["Pila"] = relationship("Pila")

    def __repr__(self) -> str:
        return f"<TrabajadorPilaAnotacion(id={self.id}, worker_id={self.worker_id})>"
