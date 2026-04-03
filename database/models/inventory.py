# database/models/inventory.py

"""
Capa de datos (`inventory`): modelos, repositorios o acceso SQLAlchemy relacionado con este módulo.
"""

from sqlalchemy import Integer, String, ForeignKey, Text, DateTime, Date, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .product import Producto, Preproceso
    from .fabrication import Fabricacion

from .base import Base, producto_material_link, preproceso_material_link, iteracion_material_link, lote_producto_link, lote_fabricacion_link
from datetime import datetime, timezone

class Material(Base):
    """
    Representa un componente físico o materia prima.
    
    Se vincula a productos, preprocesos e iteraciones para gestionar
    la lista de materiales (BOM) necesaria en cada fabricación.
    """
    __tablename__ = 'materiales'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_componente: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    descripcion_componente: Mapped[Optional[str]] = mapped_column(String)

    # Relaciones inversas
    productos: Mapped[List["Producto"]] = relationship("Producto", secondary=producto_material_link, back_populates="materiales")
    preprocesos: Mapped[List["Preproceso"]] = relationship("Preproceso", secondary=preproceso_material_link, back_populates="materiales")

    def __repr__(self) -> str:
        return f"<Material(codigo='{self.codigo_componente}')>"

class Pila(Base):
    """
    Contenedor lógico para planes de producción complejos.
    
    Agrupa múltiples fabricaciones y lotes para realizar simulaciones
    de carga de trabajo y seguimiento de hitos diarios.
    """
    __tablename__ = 'pilas'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    resultados_simulacion: Mapped[Optional[str]] = mapped_column(Text)
    producto_origen_codigo: Mapped[Optional[str]] = mapped_column(String, ForeignKey('productos.codigo'))
    pila_de_calculo_json: Mapped[Optional[str]] = mapped_column(Text)

    # Relaciones
    pasos: Mapped[List["PasoPila"]] = relationship("PasoPila", back_populates="pila", cascade="all, delete-orphan")
    producto_origen: Mapped[Optional["Producto"]] = relationship("Producto")
    bitacora: Mapped[Optional["DiarioBitacora"]] = relationship("DiarioBitacora", back_populates="pila", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pila(id={self.id}, nombre='{self.nombre}')>"

class PasoPila(Base):
    __tablename__ = 'pasos_pila'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pila_id: Mapped[int] = mapped_column(Integer, ForeignKey('pilas.id'), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    datos_paso: Mapped[str] = mapped_column(Text, nullable=False)

    # Relación inversa
    pila: Mapped["Pila"] = relationship("Pila", back_populates="pasos")

    def __repr__(self) -> str:
        return f"<PasoPila(id={self.id}, pila_id={self.pila_id}, orden={self.orden})>"

class DiarioBitacora(Base):
    """
    Registro diario de actividad vinculado a una Pila.
    
    Almacena las entradas de lo planificado vs lo realizado cada día
    de la producción activa.
    """
    __tablename__ = 'diario_bitacora'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pila_id: Mapped[int] = mapped_column(Integer, ForeignKey('pilas.id'), nullable=False, unique=True)

    # Relaciones
    pila: Mapped["Pila"] = relationship("Pila", back_populates="bitacora")
    entradas: Mapped[List["EntradaDiario"]] = relationship("EntradaDiario", back_populates="bitacora", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DiarioBitacora(id={self.id}, pila_id={self.pila_id})>"

class EntradaDiario(Base):
    __tablename__ = 'entrada_diario'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bitacora_id: Mapped[int] = mapped_column(Integer, ForeignKey('diario_bitacora.id'), nullable=False)
    fecha: Mapped[Date] = mapped_column(Date, nullable=False)
    dia_numero: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_previsto: Mapped[Optional[str]] = mapped_column(Text)
    trabajo_realizado: Mapped[Optional[str]] = mapped_column(Text)
    notas: Mapped[Optional[str]] = mapped_column(Text)

    # Relación inversa
    bitacora: Mapped["DiarioBitacora"] = relationship("DiarioBitacora", back_populates="entradas")

    def __repr__(self) -> str:
        return f"<EntradaDiario(id={self.id}, fecha={self.fecha})>"

class Lote(Base):
    """
    Agrupación logística de productos o fabricaciones.
    
    Permite gestionar unidades que deben viajar juntas o que comparten
    una misma prioridad de entrega/procesamiento.
    """
    __tablename__ = 'lotes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones M-M
    productos: Mapped[List["Producto"]] = relationship("Producto", secondary=lote_producto_link)
    fabricaciones: Mapped[List["Fabricacion"]] = relationship("Fabricacion", secondary=lote_fabricacion_link)

    def __repr__(self) -> str:
        return f"<Lote(id={self.id}, codigo='{self.codigo}')>"
