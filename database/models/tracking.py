"""
Nombre del Módulo: database.models.tracking

Descripción: Define protocolos o tipos principales: ``TrabajoLog``, ``PasoTrazabilidad``, ``IncidenciaLog``, ``IncidenciaAdjunto``. Registro principal de trabajo ejecutado para una fabricacion. Integración típica con: ``sqlalchemy``, ``base``, ``datetime``.
"""

from sqlalchemy import Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .worker import Trabajador
    from .fabrication import Fabricacion
    from .product import Producto
    from .machine import Maquina

from .base import Base
from datetime import datetime, timezone

class TrabajoLog(Base):
    """Registro principal de trabajo ejecutado para una fabricacion."""

    __tablename__ = 'trabajo_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qr_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    orden_fabricacion: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    # Relaciones con otras tablas
    trabajador_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'))
    fabricacion_id: Mapped[int] = mapped_column(Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), nullable=False)
    producto_codigo: Mapped[str] = mapped_column(String, ForeignKey('productos.codigo', ondelete='CASCADE'), nullable=False)

    # Tiempos de producción
    tiempo_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    tiempo_fin: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duracion_segundos: Mapped[Optional[int]] = mapped_column(Integer)

    # Estado del trabajo
    estado: Mapped[str] = mapped_column(String, nullable=False, default='en_proceso')

    # Información adicional
    notas: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones inversas
    trabajador: Mapped[Optional["Trabajador"]] = relationship("Trabajador", back_populates="trabajo_logs")
    fabricacion: Mapped["Fabricacion"] = relationship("Fabricacion", back_populates="trabajo_logs")
    producto: Mapped["Producto"] = relationship("Producto", back_populates="trabajo_logs")
    incidencias: Mapped[List["IncidenciaLog"]] = relationship("IncidenciaLog", back_populates="trabajo_log", cascade="all, delete-orphan")
    pasos_trazabilidad: Mapped[List["PasoTrazabilidad"]] = relationship("PasoTrazabilidad", back_populates="trabajo_log", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TrabajoLog(id={self.id}, qr='{self.qr_code}', estado='{self.estado}')>"

class PasoTrazabilidad(Base):
    """Evento de trazabilidad de un paso concreto dentro de un trabajo."""

    __tablename__ = 'pasos_trazabilidad'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trabajo_log_id: Mapped[int] = mapped_column(Integer, ForeignKey('trabajo_logs.id', ondelete='CASCADE'), nullable=False, index=True)
    trabajador_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'), nullable=True)
    maquina_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('maquinas.id', ondelete='SET NULL'), nullable=True)

    paso_nombre: Mapped[str] = mapped_column(String, nullable=False)
    tipo_paso: Mapped[Optional[str]] = mapped_column(String)

    tiempo_inicio_paso: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    tiempo_fin_paso: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duracion_paso_segundos: Mapped[Optional[int]] = mapped_column(Integer)

    estado_paso: Mapped[str] = mapped_column(String, nullable=False, default='en_proceso')

    trabajo_log: Mapped["TrabajoLog"] = relationship("TrabajoLog", back_populates="pasos_trazabilidad")
    trabajador: Mapped[Optional["Trabajador"]] = relationship("Trabajador")
    maquina: Mapped[Optional["Maquina"]] = relationship("Maquina")

    def __repr__(self) -> str:
        return f"<PasoTrazabilidad(id={self.id}, trabajo_log_id={self.trabajo_log_id}, paso='{self.paso_nombre}')>"

class IncidenciaLog(Base):
    """Incidencia reportada en un trabajo, con estado y resolucion."""

    __tablename__ = 'incidencia_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trabajo_log_id: Mapped[int] = mapped_column(Integer, ForeignKey('trabajo_logs.id', ondelete='CASCADE'), nullable=False)
    trabajador_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'))

    tipo_incidencia: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_reporte: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    estado: Mapped[str] = mapped_column(String, nullable=False, default='abierta')
    resolucion: Mapped[Optional[str]] = mapped_column(Text)
    fecha_resolucion: Mapped[Optional[datetime]] = mapped_column(DateTime)

    trabajo_log: Mapped["TrabajoLog"] = relationship("TrabajoLog", back_populates="incidencias")
    trabajador: Mapped[Optional["Trabajador"]] = relationship("Trabajador", back_populates="incidencias")
    adjuntos: Mapped[List["IncidenciaAdjunto"]] = relationship("IncidenciaAdjunto", back_populates="incidencia", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<IncidenciaLog(id={self.id}, tipo='{self.tipo_incidencia}', estado='{self.estado}')>"

class IncidenciaAdjunto(Base):
    """Adjunto asociado a una incidencia (archivo, tipo y metadatos)."""

    __tablename__ = 'incidencia_adjuntos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incidencia_id: Mapped[int] = mapped_column(Integer, ForeignKey('incidencia_logs.id', ondelete='CASCADE'), nullable=False)

    ruta_archivo: Mapped[str] = mapped_column(String, nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(String, nullable=False)
    tipo_mime: Mapped[Optional[str]] = mapped_column(String)
    tamano_bytes: Mapped[Optional[int]] = mapped_column(Integer)

    fecha_subida: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    incidencia: Mapped["IncidenciaLog"] = relationship("IncidenciaLog", back_populates="adjuntos")

    def __repr__(self) -> str:
        return f"<IncidenciaAdjunto(id={self.id}, archivo='{self.nombre_archivo}')>"
