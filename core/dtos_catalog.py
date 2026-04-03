# -*- coding: utf-8 -*-
"""DTOs de catálogo/producción (productos, lotes, pilas, iteraciones)."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class ProductDTO:
    codigo: str
    descripcion: str
    departamento: str = ""
    tipo_trabajador: int = 0
    donde: str = ""
    tiene_subfabricaciones: bool = False
    tiempo_optimo: float = 0.0


@dataclass
class SubfabricacionDTO:
    id: int
    producto_codigo: str
    descripcion: str
    tiempo: float
    tipo_trabajador: int
    maquina_id: int | None


@dataclass
class ProcesoMecanicoDTO:
    id: int
    producto_codigo: str
    nombre: str
    descripcion: str
    tiempo: float
    tipo_trabajador: int


@dataclass
class MaterialDTO:
    id: int
    codigo_componente: str
    descripcion_componente: str


@dataclass
class PilaDTO:
    id: int
    nombre: str
    descripcion: str
    producto_origen_codigo: str | None = None
    unidades: int = 1
    fecha_creacion: datetime | None = None
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class MaterialStatsDTO:
    codigo_componente: str
    frecuencia: int


@dataclass
class ComponenteDTO:
    id: int
    descripcion: str


@dataclass
class FabricacionProductoDTO:
    producto_codigo: str
    cantidad: int
    descripcion: str = ""
    
    def __post_init__(self):
        if self.cantidad < 1:
            self.cantidad = 1


@dataclass
class PreprocesoDTO:
    id: int
    nombre: str
    descripcion: str
    tiempo: float
    componentes: list[MaterialDTO] | list[ComponenteDTO] | list[Any] = field(default_factory=list)
    componentes_ids: list[int] | None = None # Para flujos de creación/edición


@dataclass
class FabricacionDTO:
    id: int
    codigo: str
    descripcion: str
    preprocesos: list[PreprocesoDTO] | None = None
    productos: list[FabricacionProductoDTO] | None = None
    preprocesos_ids: list[int] | None = None # Para flujos de creación/edición


@dataclass
class LoteDTO:
    id: int
    codigo: str
    descripcion: str
    productos: list[ProductDTO] | None = None
    fabricaciones: list[FabricacionDTO] | None = None


@dataclass
class ConfigurationDTO:
    clave: str
    valor: str


@dataclass
class ProductIterationMaterialDTO:
    id: int
    codigo: str
    descripcion: str


@dataclass
class ProductIterationDTO:
    id: int
    producto_codigo: str
    descripcion: str
    fecha_creacion: datetime
    nombre_responsable: str
    tipo_fallo: str = ""
    materiales: list[ProductIterationMaterialDTO] | None = None
    ruta_imagen: str | None = None
    ruta_plano: str | None = None
    producto_descripcion: str = ""


@dataclass
class LabelRangeDTO:
    fabricacion_id: int
    start: int
    end: int
    count: int


@dataclass
class IterationImageDTO:
    id: int
    image_path: str
    description: str | None
    upload_date: datetime | None

