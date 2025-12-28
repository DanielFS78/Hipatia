from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, date

@dataclass
class FabricacionAsignadaDTO:
    """DTO para fabricaciones asignadas a un trabajador."""
    id: int
    codigo: str
    descripcion: str
    fecha_asignacion: Optional[datetime]
    estado: str
    productos: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class IncidenciaAdjuntoDTO:
    """DTO para adjuntos de una incidencia."""
    id: int
    ruta_archivo: str
    tipo_archivo: str

@dataclass
class IncidenciaLogDTO:
    """DTO para incidencias registradas."""
    id: int
    tipo_incidencia: str
    descripcion: str
    fecha_reporte: datetime
    estado: str
    resolucion: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    adjuntos: List[IncidenciaAdjuntoDTO] = field(default_factory=list)
    # Campos opcionales para visualización
    trabajador_nombre: Optional[str] = None

@dataclass
class PasoTrazabilidadDTO:
    """DTO para pasos de trazabilidad (sellos)."""
    id: int
    trabajo_log_id: int  # Campo nuevo necesario para relaciones
    paso_nombre: str
    tipo_paso: str
    estado_paso: str
    tiempo_inicio_paso: datetime
    tiempo_fin_paso: Optional[datetime] = None
    duracion_paso_segundos: Optional[int] = None
    maquina_id: Optional[int] = None
    maquina_nombre: Optional[str] = None
    trabajador_nombre: Optional[str] = None

@dataclass
class TrabajoLogDTO:
    """DTO para el log principal de trabajo (Pasaporte)."""
    id: int
    qr_code: str
    estado: str
    tiempo_inicio: datetime
    trabajador_id: int
    fabricacion_id: int
    producto_codigo: str
    
    tiempo_fin: Optional[datetime] = None
    duracion_segundos: Optional[int] = None
    notas: Optional[str] = None
    trabajador_nombre: Optional[str] = None
    fabricacion_codigo: Optional[str] = None
    fabricacion_descripcion: Optional[str] = None
    producto_descripcion: Optional[str] = None
    orden_fabricacion: Optional[str] = None
    
    incidencias: List[IncidenciaLogDTO] = field(default_factory=list)
