from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class MachineDTO:
    id: int
    nombre: str
    departamento: str
    tipo_proceso: str
    activa: bool

@dataclass
class MachineMaintenanceDTO:
    maintenance_date: date
    notes: str

@dataclass
class PreparationGroupDTO:
    id: int
    nombre: str
    descripcion: str
    producto_codigo: Optional[str] = None

@dataclass
class PreparationStepDTO:
    id: int
    nombre: str
    tiempo_fase: float
    descripcion: str
    es_diario: bool

@dataclass
class WorkerDTO:
    """DTO para datos de trabajadores."""
    id: int
    nombre_completo: str
    activo: bool
    notas: str
    tipo_trabajador: int

@dataclass
class WorkerAnnotationDTO:
    """DTO para anotaciones de trabajadores."""
    pila_id: int
    fecha: datetime
    anotacion: str

@dataclass
class ProductDTO:
    """DTO para datos de productos."""
    codigo: str
    descripcion: str
    departamento: str = ""
    tipo_trabajador: int = 0
    donde: str = ""
    tiene_subfabricaciones: bool = False
    tiempo_optimo: float = 0.0

@dataclass
class SubfabricacionDTO:
    """DTO para subfabricaciones de un producto."""
    id: int
    producto_codigo: str
    descripcion: str
    tiempo: float
    tipo_trabajador: int
    maquina_id: Optional[int]

@dataclass
class ProcesoMecanicoDTO:
    """DTO para procesos mecánicos de un producto."""
    id: int
    producto_codigo: str
    nombre: str
    descripcion: str
    tiempo: float
    tipo_trabajador: int

@dataclass
class MaterialDTO:
    """DTO para materiales de un producto."""
    id: int
    codigo_componente: str
    descripcion_componente: str

@dataclass
class PilaDTO:
    """DTO para datos de una pila."""
    id: int
    nombre: str
    descripcion: str
    producto_origen_codigo: Optional[str] = None
    # Campos opcionales para cuando se listan con fechas (get_all_pilas_with_dates)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

@dataclass
class MaterialStatsDTO:
    """DTO para estadísticas de uso de materiales."""
    codigo_componente: str
    frecuencia: int
@dataclass
class ComponenteDTO:
    """DTO simplificado para componentes en vistas de resumen."""
    id: int
    descripcion: str

@dataclass
class FabricacionProductoDTO:
    """DTO para productos asociados a una fabricación."""
    producto_codigo: str
    cantidad: int

@dataclass
class PreprocesoDTO:
    """DTO para datos de preprocesos."""
    id: int
    nombre: str
    descripcion: str
    tiempo: float
    componentes: list  # Can be List[MaterialDTO] or List[ComponenteDTO]

@dataclass
class FabricacionDTO:
    """DTO para datos de fabricaciones."""
    id: int
    codigo: str
    descripcion: str
    preprocesos: list = None # Can be List[PreprocesoDTO]

@dataclass
class LoteDTO:
    """DTO para plantillas de lote."""
    id: int
    codigo: str
    descripcion: str
    productos: list = None # List[ProductDTO]
    fabricaciones: list = None # List[FabricacionDTO]

@dataclass
class ConfigurationDTO:
    """DTO para pares clave-valor de configuración."""
    clave: str
    valor: str

@dataclass
class ProductIterationMaterialDTO:
    """DTO para materiales dentro de una iteración de producto."""
    id: int
    codigo: str
    descripcion: str

@dataclass
class ProductIterationDTO:
    """DTO para iteraciones de producto (historial de cambios)."""
    id: int
    producto_codigo: str
    descripcion: str  # Descripción de la iteración/cambio
    fecha_creacion: datetime
    nombre_responsable: str
    tipo_fallo: str = ""
    materiales: list = None # List[ProductIterationMaterialDTO]
    ruta_imagen: Optional[str] = None
    ruta_plano: Optional[str] = None
    producto_descripcion: str = "" # Descripción del producto (para listados)


@dataclass
class LabelRangeDTO:
    """DTO para rango de etiquetas asignado."""
    fabricacion_id: int
    start: int
    end: int
    count: int

