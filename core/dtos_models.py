# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.dtos_models

Descripción: Funciones y datos de apoyo del paquete; conviene enlazar qué controlador o servicio las consume y qué estructuras devuelven (ver firmas al inicio del archivo). Integración típica con: ``datetime``, ``core``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from core.dtos_catalog import (
    ComponenteDTO,
    ConfigurationDTO,
    FabricacionDTO,
    FabricacionProductoDTO,
    IterationImageDTO,
    LabelRangeDTO,
    LoteDTO,
    MaterialDTO,
    MaterialStatsDTO,
    PilaDTO,
    PreprocesoDTO,
    ProcesoMecanicoDTO,
    ProductDTO,
    ProductIterationDTO,
    ProductIterationMaterialDTO,
    SubfabricacionDTO,
)
from core.dtos_flow_camera import (
    CameraConfigDTO,
    CameraDetailDTO,
    CanvasCyclicConnectionFlags,
    FlowCanvasTaskDTO,
    FlowTaskConfigDTO,
    FlowTaskDataDTO,
    FlowItemDTO,
    ProductFlowLibraryProductDTO,
    ProductionFlowStepDTO,
)


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
    producto_codigo: str | None = None


@dataclass
class PreparationStepDTO:
    id: int
    nombre: str
    tiempo_fase: float
    descripcion: str
    es_diario: bool


@dataclass
class WorkerDTO:
    id: int
    nombre_completo: str
    activo: bool
    notas: str
    tipo_trabajador: int


@dataclass
class WorkerAnnotationDTO:
    pila_id: int
    fecha: datetime
    anotacion: str


@dataclass
class WorkerDetailDTO:
    id: int
    nombre_completo: str
    activo: bool
    notas: str
    tipo_trabajador: int
    username: str | None = None
    role: str | None = None


@dataclass
class AuthResponseDTO:
    id: int
    nombre_completo: str
    username: str
    role: str
    activo: bool


@dataclass
class BackupInfoDTO:
    name: str
    path: str
    date: datetime
    size_bytes: int
    size_mb: float
    has_checksum: bool


@dataclass
class SimulationResultTaskDTO:
    Inicio: datetime
    Fin: datetime
    Tarea: str


@dataclass
class CalculationSubPartDTO:
    descripcion: str
    tiempo: float
    tipo_trabajador: int
    requiere_maquina_tipo: str | None = None


@dataclass
class CalculationProductDTO:
    codigo: str
    descripcion: str
    departamento: str
    tipo_trabajador: int
    donde: str
    tiene_subfabricaciones: bool
    tiempo_optimo: float
    sub_partes: list[CalculationSubPartDTO]
    cantidad_en_kit: int = 1
    deadline: datetime | None = None
    fabricacion_id: str | int | None = None
    units_for_this_instance: int = 1


@dataclass(frozen=True)
class FileOperationResultDTO:
    """Resultado de una operación de adjuntar o mover archivos."""
    success: bool
    path_or_error: str


@dataclass(frozen=True)
class ProductDetailsDTO:
    """Detalles completos de un producto y sus subcomponentes."""
    producto: ProductDTO | None
    subfabricaciones: list[SubfabricacionDTO]
    procesos_mecanicos: list[ProcesoMecanicoDTO]

@dataclass(frozen=True)
class QuoteDTO:
    """Frase célebre."""
    quote: str
    author: str


@dataclass(frozen=True)
class AuthorInfoDTO:
    """Información enriquecida de un autor de Wikipedia."""
    summary: str
    image_url: str | None


@dataclass(frozen=True)
class SyncRecordPayloadDTO:
    """Contenedor de datos dinámicos para un registro de sincronización."""
    fields: dict[str, Any]  # Mantiene los pares campo-valor de la fila


@dataclass(frozen=True)
class SyncRecordDTO:
    """Un registro individual para sincronización."""
    action: str  # 'new' o 'updated'
    data: SyncRecordPayloadDTO


@dataclass(frozen=True)
class SyncTableDifferencesDTO:
    """Diferencias detectadas en una tabla específica."""
    table_name: str
    differences: list[SyncRecordDTO]


@dataclass(frozen=True)
class DatabaseComparisonDTO:
    """Resultado completo de la comparación de dos bases de datos."""
    tables: list[SyncTableDifferencesDTO]


@dataclass(frozen=True)
class WorkerFormDataDTO:
    """Datos extraídos del formulario de un trabajador."""
    nombre_completo: str
    activo: bool
    notas: str
    tipo_trabajador: int
    username: str | None
    password: str | None
    confirm_password: str | None
    role: str | None


@dataclass(frozen=True)
class LoteInstanceParametersDTO:
    """Parámetros para instanciar un lote desde UI."""
    identificador: str
    unidades: int
    deadline: date


@dataclass(frozen=True)
class CalculationStepDTO:
    """Representa un paso o item en la sesión de planificación/cálculo."""
    identificador: str
    lote_codigo: str
    unidades: int
    deadline: datetime | None = None
    lote_template_id: int | None = None
    pila_de_calculo_directa: dict[str, Any] | None = None  # Estructura interna de exportación de Pila


__all__ = [
    "MachineDTO",
    "MachineMaintenanceDTO",
    "PreparationGroupDTO",
    "PreparationStepDTO",
    "WorkerDTO",
    "WorkerAnnotationDTO",
    "WorkerDetailDTO",
    "AuthResponseDTO",
    "BackupInfoDTO",
    "SimulationResultTaskDTO",
    "CalculationSubPartDTO",
    "CalculationProductDTO",
    "ProductDTO",
    "SubfabricacionDTO",
    "ProcesoMecanicoDTO",
    "MaterialDTO",
    "PilaDTO",
    "MaterialStatsDTO",
    "ComponenteDTO",
    "FabricacionProductoDTO",
    "PreprocesoDTO",
    "FabricacionDTO",
    "LoteDTO",
    "ConfigurationDTO",
    "ProductIterationMaterialDTO",
    "ProductIterationDTO",
    "LabelRangeDTO",
    "IterationImageDTO",
    "FlowTaskDataDTO",
    "FlowTaskConfigDTO",
    "ProductionFlowStepDTO",
    "FlowCanvasTaskDTO",
    "FlowItemDTO",
    "CameraConfigDTO",
    "CameraDetailDTO",
    "CanvasCyclicConnectionFlags",
    "ProductFlowLibraryProductDTO",
    "FileOperationResultDTO",
    "ProductDetailsDTO",
    "QuoteDTO",
    "AuthorInfoDTO",
    "SyncRecordDTO",
    "SyncRecordPayloadDTO",
    "SyncTableDifferencesDTO",
    "DatabaseComparisonDTO",
    "WorkerFormDataDTO",
    "LoteInstanceParametersDTO",
    "CalculationStepDTO",
]

