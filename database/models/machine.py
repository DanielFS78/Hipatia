# database/models/machine.py

"""
Capa de datos (`machine`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from sqlalchemy import Integer, String, Boolean, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .product import Producto

from .base import Base

class Maquina(Base):
    """
    Representa un recurso físico (fresa, torno, etc.) en planta.
    
    Gestiona su estado de disponibilidad, departamento y los grupos
    de preparación asociados para el cálculo de tiempos.
    """
    __tablename__ = 'maquinas'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    departamento: Mapped[str] = mapped_column(String, nullable=False)
    tipo_proceso: Mapped[Optional[str]] = mapped_column(String)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    mantenimientos: Mapped[List["MachineMaintenanc"]] = relationship("MachineMaintenanc", back_populates="maquina", cascade="all, delete-orphan")
    grupos_preparacion: Mapped[List["GrupoPreparacion"]] = relationship("GrupoPreparacion", back_populates="maquina", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Maquina(id={self.id}, nombre='{self.nombre}')>"

class MachineMaintenanc(Base):
    __tablename__ = 'machine_maintenance'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey('maquinas.id'), nullable=False)
    maintenance_date: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relación inversa
    maquina: Mapped["Maquina"] = relationship("Maquina", back_populates="mantenimientos")

    def __repr__(self) -> str:
        return f"<MachineMaintenanc(id={self.id}, machine_id={self.machine_id})>"

class GrupoPreparacion(Base):
    """
    Conjunto de pasos de preparación necesarios para una máquina.
    
    Puede ser genérico para la máquina o específico para un producto.
    """
    __tablename__ = 'grupos_preparacion'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    maquina_id: Mapped[int] = mapped_column(Integer, ForeignKey('maquinas.id'), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    producto_codigo: Mapped[Optional[str]] = mapped_column(String, ForeignKey('productos.codigo'))

    # Relaciones
    maquina: Mapped["Maquina"] = relationship("Maquina", back_populates="grupos_preparacion")
    producto: Mapped[Optional["Producto"]] = relationship("Producto")
    pasos: Mapped[List["PreparacionPaso"]] = relationship("PreparacionPaso", back_populates="grupo", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GrupoPreparacion(id={self.id}, nombre='{self.nombre}')>"

class PreparacionPaso(Base):
    """
    Tarea individual dentro de un grupo de preparación.
    
    Incluye el tiempo estimado, si es una tarea diaria o de verificación
    de primera pieza.
    """
    __tablename__ = 'preparacion_pasos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    tiempo_fase: Mapped[float] = mapped_column(Float, nullable=False)
    grupo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('grupos_preparacion.id'))
    es_diario: Mapped[bool] = mapped_column(Boolean, default=False)
    es_verificacion: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relación inversa
    grupo: Mapped[Optional["GrupoPreparacion"]] = relationship("GrupoPreparacion", back_populates="pasos")

    def __repr__(self) -> str:
        return f"<PreparacionPaso(id={self.id}, nombre='{self.nombre}')>"
