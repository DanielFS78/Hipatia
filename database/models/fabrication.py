# database/models/fabrication.py

"""
Nombre del Módulo: database.models.fabrication

Descripción: Define protocolos o tipos principales: ``Fabricacion``, ``FabricacionContador``. Entidad principal que representa una Orden de Fabricación (OF). Integración típica con: ``sqlalchemy``, ``base``.
"""

from sqlalchemy import Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .product import Preproceso
    from .worker import Trabajador
    from .tracking import TrabajoLog

from .base import Base, fabricacion_preproceso_link, trabajador_fabricacion_link

class Fabricacion(Base):
    """
    Entidad principal que representa una Orden de Fabricación (OF).
    
    Vincula un conjunto de productos y preprocesos para su ejecución en planta,
    gestionando la trazabilidad y los operarios asignados.
    
    Atributos (Columnas):
        - id (int): Identificador único autoincremental.
        - codigo (str): Código único de la orden (ej: OF-2024-001).
        - descripcion (str, optional): Breve descripción o notas de la orden.
        
    Relaciones:
        - preprocesos: Lista de preprocesos asociados (Many-to-Many).
        - trabajadores_asignados: Operarios vinculados a esta OF (Many-to-Many).
        - trabajo_logs: Registro cronológico de actividades en planta (One-to-Many).
    """
    __tablename__ = 'fabricaciones'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String)

    # Relación M-M con Preproceso
    preprocesos: Mapped[List["Preproceso"]] = relationship("Preproceso",
                                secondary=fabricacion_preproceso_link,
                                back_populates="fabricaciones")

    # Relaciones de trazabilidad
    trabajadores_asignados: Mapped[List["Trabajador"]] = relationship(
        "Trabajador",
        secondary=trabajador_fabricacion_link,
        back_populates="fabricaciones_asignadas"
    )
    trabajo_logs: Mapped[List["TrabajoLog"]] = relationship("TrabajoLog", back_populates="fabricacion", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Fabricacion(id={self.id}, codigo='{self.codigo}')>"

class FabricacionContador(Base):
    """
    Contador para numeración correlativa de etiquetas de unidad en una fabricación.
    
    Permite garantizar que cada unidad física de un lote tenga un ID único incremental.
    
    Atributos (Columnas):
        - fabricacion_id (int): FK hacia 'fabricaciones'. Parte de la PK.
        - ultimo_numero_unidad (int): Último correlativo generado (ej: 42 para la unidad 42).
        
    Relaciones:
        - fabricacion: Acceso al objeto Fabricación padre.
    """
    __tablename__ = 'fabricacion_contadores'

    fabricacion_id: Mapped[int] = mapped_column(Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), primary_key=True)
    ultimo_numero_unidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relación para integridad referencial
    fabricacion: Mapped["Fabricacion"] = relationship("Fabricacion")

    def __repr__(self) -> str:
        return f"<FabricacionContador(fabricacion_id={self.fabricacion_id}, ultimo={self.ultimo_numero_unidad})>"
