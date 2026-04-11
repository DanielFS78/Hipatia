# database/models/product.py

"""
Nombre del Módulo: database.models.product

Descripción: Define protocolos o tipos principales: ``Producto``, ``Preproceso``, ``Subfabricacion``, ``ProcesoMecanico``, ``ProductIteration``. Modelo que representa un Producto en el catálogo. Integración típica con: ``sqlalchemy``, ``base``, ``datetime``.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .inventory import Material
    from .fabrication import Fabricacion
    from .machine import Maquina

from .base import Base, producto_material_link, iteracion_material_link
from datetime import datetime, timezone

class Producto(Base):
    """
    Modelo que representa un Producto en el catálogo.
    
    Almacena la configuración base, tiempos de fabricación estimados y
    relaciones con subfabricaciones, materiales e iteraciones.
    
    Atributos (Columnas):
        - codigo (str): PK. Identificador único del producto.
        - descripcion (str): Nombre descriptivo del producto.
        - departamento (str): Área productiva responsable (ej: Mecanizado).
        - tipo_trabajador (int): Mínimo nivel de habilidad requerido. 
          [Diccionario de Datos] 
          1 = Operario Básico/Junior (tareas rutinarias).
          2 = Especialista/Mid (manejo de maquinaria compleja).
          3 = Experto/Senior (calidad, configuración pesada o supervisión).
        - donde (str, optional): Ubicación física o referencia de almacenamiento.
        - tiene_subfabricaciones (bool): Indica si depende de otros componentes.
        - tiempo_optimo (float, optional): Tiempo de fabricación estimado por unidad.
        
    Relaciones:
        - subfabricaciones: Lista de componentes dependientes.
        - materiales: Materias primas asociadas.
        - procesos_mecanicos: Pasos de máquina específicos.
        - iteraciones: Historial de cambios y control de calidad.
    """
    __tablename__ = 'productos'

    codigo: Mapped[str] = mapped_column(String, primary_key=True)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    departamento: Mapped[str] = mapped_column(String, nullable=False)
    tipo_trabajador: Mapped[int] = mapped_column(Integer, nullable=False)
    donde: Mapped[Optional[str]] = mapped_column(String)
    tiene_subfabricaciones: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tiempo_optimo: Mapped[Optional[float]] = mapped_column(Float)

    # Relaciones
    subfabricaciones: Mapped[List["Subfabricacion"]] = relationship("Subfabricacion", back_populates="producto", cascade="all, delete-orphan")
    materiales: Mapped[List["Material"]] = relationship("Material", secondary=producto_material_link, back_populates="productos")
    procesos_mecanicos: Mapped[List["ProcesoMecanico"]] = relationship("ProcesoMecanico", back_populates="producto", cascade="all, delete-orphan")
    iteraciones: Mapped[List["ProductIteration"]] = relationship("ProductIteration", back_populates="producto", cascade="all, delete-orphan")

    # Relación de trazabilidad (importación diferida vía string)
    trabajo_logs = relationship("TrabajoLog", back_populates="producto", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Producto(codigo='{self.codigo}', descripcion='{self.descripcion}')>"

class Preproceso(Base):
    """
    Modelo para tareas preparatorias reutilizables.
    
    Define trabajos que no son procesos mecánicos de máquina pero
    consumen tiempo y recursos de operario (ej. limpieza, rebabado).
    
    Atributos (Columnas):
        - id (int): PK autoincremental.
        - nombre (str): Nombre único del proceso.
        - descripcion (str, optional): Texto detallado del trabajo.
        - tiempo (float): Tiempo estimado de ejecución.
        - tipo_trabajador (int): Nivel de habilidad requerido.
        
    Relaciones:
        - materiales: Consumibles necesarios para el preproceso.
        - fabricaciones: Órdenes de fabricación que incluyen este paso.
    """
    __tablename__ = 'preprocesos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    tiempo: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tipo_trabajador: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Importada de .base
    from .base import preproceso_material_link, fabricacion_preproceso_link
    
    materiales: Mapped[List["Material"]] = relationship("Material",
                                secondary=preproceso_material_link,
                                back_populates="preprocesos")

    fabricaciones: Mapped[List["Fabricacion"]] = relationship("Fabricacion",
                                 secondary=fabricacion_preproceso_link,
                                 back_populates="preprocesos")

    # ✅ PROPIEDAD PARA COMPATIBILIDAD HACIA ATRÁS
    @property
    def componentes(self) -> List["Material"]:
        return self.materiales

    @componentes.setter
    def componentes(self, value: List["Material"]) -> None:
        """Setter para mantener compatibilidad."""
        self.materiales = value

    def __repr__(self) -> str:
        return f"<Preproceso(id={self.id}, nombre='{self.nombre}')>"

class Subfabricacion(Base):
    """
    Define un componente que forma parte de un producto pero que
    tiene su propio flujo de procesos o es una pieza independiente.
    
    Atributos (Columnas):
        - id (int): PK autoincremental.
        - producto_codigo (str): FK hacia 'productos'.
        - descripcion (str): Nombre del componente.
        - tiempo (float): Tiempo de fabricación.
        - tipo_trabajador (int): Nivel de habilidad requerido.
        - maquina_id (int, optional): FK hacia 'maquinas' (si aplica).
        
    Relaciones:
        - producto: Referencia al Producto padre.
        - maquina: Máquina específica asignada.
    """
    __tablename__ = 'subfabricaciones'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_codigo: Mapped[str] = mapped_column(String, ForeignKey('productos.codigo'), nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    tiempo: Mapped[float] = mapped_column(Float, nullable=False)
    tipo_trabajador: Mapped[int] = mapped_column(Integer, nullable=False)
    maquina_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('maquinas.id'), nullable=True)
    maquina: Mapped[Optional["Maquina"]] = relationship("Maquina")

    # Relación inversa
    producto: Mapped["Producto"] = relationship("Producto", back_populates="subfabricaciones")

    def __repr__(self) -> str:
        return f"<Subfabricacion(id={self.id}, producto='{self.producto_codigo}')>"

class ProcesoMecanico(Base):
    """
    Representa una operación de máquina específica (fresado, torneado, etc.)
    vinculada a un producto con un tiempo de ejecución calculado.
    
    Atributos (Columnas):
        - id (int): PK autoincremental.
        - producto_codigo (str): FK hacia 'productos'.
        - nombre (str): Nombre de la operación.
        - descripcion (str): Detalles técnicos del proceso.
        - tiempo (float): Tiempo de máquina por unidad.
        - tipo_trabajador (int): Nivel de habilidad de operario.
        
    Relaciones:
        - producto: Producto al que pertenece esta operación.
    """
    __tablename__ = 'procesos_mecanicos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_codigo: Mapped[str] = mapped_column(String, ForeignKey('productos.codigo'), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    tiempo: Mapped[float] = mapped_column(Float, nullable=False)
    tipo_trabajador: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relación inversa
    producto: Mapped["Producto"] = relationship("Producto", back_populates="procesos_mecanicos")

    def __repr__(self) -> str:
        return f"<ProcesoMecanico(id={self.id}, nombre='{self.nombre}')>"

class ProductIteration(Base):
    """
    Registro histórico de cambios en un producto.
    
    Almacena revisiones de diseño, responsables, planos y fotos
    de piezas reales fabricadas para control de calidad.
    
    Atributos (Columnas):
        - id (int): PK autoincremental.
        - producto_codigo (str): FK hacia 'productos'.
        - fecha_creacion (datetime): Fecha de la revisión.
        - nombre_responsable (str): Quién realizó el cambio.
        - descripcion_cambio (str): Motivo o detalle de la iteración.
        - ruta_imagen (str): Enlace a foto de la pieza fabricada.
        - tipo_fallo (str): Categorización de error si aplica.
        - ruta_plano (str): Enlace al dibujo técnico.
        
    Relaciones:
        - producto: Producto objeto de la iteración.
        - materiales: Versión específica de materiales en esta iteración.
    """
    __tablename__ = 'iteraciones_producto'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_codigo: Mapped[str] = mapped_column(String, ForeignKey('productos.codigo', ondelete='CASCADE'), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    nombre_responsable: Mapped[str] = mapped_column(String, nullable=False)
    descripcion_cambio: Mapped[Optional[str]] = mapped_column(Text)
    ruta_imagen: Mapped[Optional[str]] = mapped_column(String)
    tipo_fallo: Mapped[Optional[str]] = mapped_column(String)
    ruta_plano: Mapped[Optional[str]] = mapped_column(String)

    # Relaciones
    producto: Mapped["Producto"] = relationship("Producto", back_populates="iteraciones")
    materiales: Mapped[List["Material"]] = relationship("Material", secondary=iteracion_material_link, backref="iteraciones")

    def __repr__(self) -> str:
        return f"<ProductIteration(id={self.id}, producto='{self.producto_codigo}')>"
