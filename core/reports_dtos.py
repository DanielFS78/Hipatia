# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.reports_dtos

Descripción: Define protocolos o tipos principales: ``ResultadoBusquedaDTO``, ``OrdenFabricacionResumenDTO``, ``OrdenFabricacionDetalleDTO``, ``PromedioTiempoDTO``, ``TiempoTrabajadorDTO``. DTO para resultados de búsqueda inteligente. Integración típica con: ``datetime``.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ResultadoBusquedaDTO:
    """
    DTO para resultados de búsqueda inteligente.
    Representa un producto, fabricación u orden encontrada.
    """
    tipo: str  # 'producto', 'fabricacion', 'orden'
    codigo: str
    descripcion: str
    fecha_ultimo_uso: Optional[datetime] = None
    total_unidades: int = 0


@dataclass
class OrdenFabricacionResumenDTO:
    """
    DTO para resumen de una Orden de Fabricación.
    Muestra información agregada sin detalles individuales.
    """
    orden_fabricacion: str
    producto_codigo: str
    producto_descripcion: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    cantidad_unidades: int = 0
    tiempo_total_segundos: int = 0
    incidencias_count: int = 0
    estado: str = "en_proceso"  # en_proceso, completado, pausado


@dataclass
class OrdenFabricacionDetalleDTO:
    """
    DTO para detalle completo de una Orden de Fabricación.
    Incluye información extendida para vista de detalle.
    """
    orden_fabricacion: str
    producto_codigo: str
    producto_descripcion: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    cantidad_unidades: int = 0
    tiempo_total_segundos: int = 0
    tiempo_promedio_segundos: float = 0.0
    incidencias_count: int = 0
    trabajadores_involucrados: List[str] = field(default_factory=list)
    estado: str = "en_proceso"


@dataclass
class PromedioTiempoDTO:
    """
    DTO para estadísticas de tiempo promedio de un producto.
    Incluye métricas de dispersión para análisis.
    """
    producto_codigo: str
    producto_descripcion: str
    promedio_segundos: float = 0.0
    desviacion_estandar: float = 0.0
    minimo_segundos: int = 0
    maximo_segundos: int = 0
    total_unidades: int = 0
    periodo_inicio: Optional[datetime] = None
    periodo_fin: Optional[datetime] = None


@dataclass
class TiempoTrabajadorDTO:
    """
    DTO para tiempos promedio por trabajador en un producto.
    Permite comparar rendimiento entre operarios.
    """
    trabajador_id: int
    trabajador_nombre: str
    promedio_segundos: float = 0.0
    minimo_segundos: int = 0
    maximo_segundos: int = 0
    unidades_realizadas: int = 0


@dataclass
class IncidenciaResumenDTO:
    """
    DTO para resumen de incidencias agrupadas por tipo.
    Usado en gráficas de patrón de incidencias.
    """
    tipo_incidencia: str
    cantidad: int = 0
    porcentaje: float = 0.0


@dataclass
class PuntoEvolucionDTO:
    """
    DTO para un punto en la gráfica de evolución temporal.
    Representa el tiempo promedio en un período específico.
    """
    fecha: datetime
    promedio_segundos: float = 0.0
    cantidad_unidades: int = 0


@dataclass
class UnidadTrabajoDTO:
    """
    DTO para detalle de una unidad individual de trabajo.
    Usado en la vista expandida de una orden.
    """
    qr_code: str
    tiempo_inicio: datetime
    tiempo_fin: Optional[datetime] = None
    duracion_segundos: int = 0
    trabajador_nombre: str = ""
    tiene_incidencias: bool = False


@dataclass
class ResumenProductoDTO:
    """
    DTO para resumen estadístico de un producto.
    Información general mostrada al seleccionar un producto.
    """
    producto_codigo: str
    producto_descripcion: str
    total_ordenes: int = 0
    total_unidades: int = 0
    tiempo_promedio_segundos: float = 0.0
    total_incidencias: int = 0
    fecha_primera_produccion: Optional[datetime] = None
    fecha_ultima_produccion: Optional[datetime] = None
