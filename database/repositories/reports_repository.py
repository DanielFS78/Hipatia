# -*- coding: utf-8 -*-
"""
========================================================================
REPORTS REPOSITORY - REPOSITORIO PARA CONSULTAS DE REPORTES
========================================================================
Este repositorio está especializado en consultas de agregación y análisis
para el módulo de reportes de producción. Se enfoca en operaciones de
solo lectura optimizadas para visualización y análisis de datos.

Principios de diseño:
- Solo lectura: No modifica datos, solo consulta
- Optimizado para agregación: Usa funciones SQL de agregación
- DTOs específicos: Retorna objetos preparados para la UI
========================================================================
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import func, desc, and_, or_, distinct
from sqlalchemy.orm import Session, joinedload

from database.models import (
    TrabajoLog, PasoTrazabilidad, IncidenciaLog,
    Producto, Fabricacion, Trabajador
)
from .base import BaseRepository
from core.reports_dtos import (
    ResultadoBusquedaDTO, OrdenFabricacionResumenDTO, OrdenFabricacionDetalleDTO,
    PromedioTiempoDTO, TiempoTrabajadorDTO, IncidenciaResumenDTO,
    PuntoEvolucionDTO, UnidadTrabajoDTO, ResumenProductoDTO
)


class ReportsRepository(BaseRepository):
    """
    Repositorio especializado en consultas de agregación y análisis
    para el módulo de reportes de producción.
    
    Este repositorio hereda de BaseRepository para utilizar el patrón
    safe_execute para manejo seguro de sesiones.
    """
    
    def __init__(self, session_factory):
        """
        Inicializa el repositorio de reportes.
        
        Args:
            session_factory: Factory de sesiones de SQLAlchemy (SessionLocal)
        """
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.ReportsRepository")
    
    # =========================================================================
    # BÚSQUEDA INTELIGENTE
    # =========================================================================
    
    def buscar_por_codigo(self, query: str, limit: int = 20) -> List[ResultadoBusquedaDTO]:
        """
        Búsqueda inteligente por código o descripción.
        Busca en productos, fabricaciones y órdenes de fabricación.
        
        Args:
            query: Texto a buscar (parcial, case-insensitive)
            limit: Número máximo de resultados
            
        Returns:
            Lista de ResultadoBusquedaDTO ordenados por relevancia
        """
        def _operation(session: Session, **kwargs) -> List[ResultadoBusquedaDTO]:
            results = []
            search_pattern = f"%{query.lower()}%"
            
            # Buscar en Productos
            productos = session.query(Producto).filter(
                or_(
                    func.lower(Producto.codigo).like(search_pattern),
                    func.lower(Producto.descripcion).like(search_pattern)
                )
            ).limit(limit // 3).all()
            
            for p in productos:
                # Obtener última fecha de producción
                ultimo_trabajo = session.query(TrabajoLog.tiempo_inicio).filter(
                    TrabajoLog.producto_codigo == p.codigo
                ).order_by(desc(TrabajoLog.tiempo_inicio)).first()
                
                # Contar unidades
                total_unidades = session.query(func.count(TrabajoLog.id)).filter(
                    TrabajoLog.producto_codigo == p.codigo
                ).scalar() or 0
                
                results.append(ResultadoBusquedaDTO(
                    tipo='producto',
                    codigo=p.codigo,
                    descripcion=p.descripcion or '',
                    fecha_ultimo_uso=ultimo_trabajo[0] if ultimo_trabajo else None,
                    total_unidades=total_unidades
                ))
            
            # Buscar en Órdenes de Fabricación (campo orden_fabricacion en TrabajoLog)
            ordenes = session.query(
                TrabajoLog.orden_fabricacion,
                func.max(TrabajoLog.tiempo_inicio).label('ultima_fecha'),
                func.count(TrabajoLog.id).label('total')
            ).filter(
                TrabajoLog.orden_fabricacion.isnot(None),
                func.lower(TrabajoLog.orden_fabricacion).like(search_pattern)
            ).group_by(TrabajoLog.orden_fabricacion).limit(limit // 3).all()
            
            for orden in ordenes:
                if orden.orden_fabricacion:
                    results.append(ResultadoBusquedaDTO(
                        tipo='orden',
                        codigo=orden.orden_fabricacion,
                        descripcion=f"Orden de Fabricación",
                        fecha_ultimo_uso=orden.ultima_fecha,
                        total_unidades=orden.total
                    ))
            
            # Ordenar por fecha más reciente primero
            results.sort(key=lambda x: x.fecha_ultimo_uso or datetime.min, reverse=True)
            
            return results[:limit]
        
        return self.safe_execute(_operation) or []
    
    # =========================================================================
    # ÓRDENES DE FABRICACIÓN
    # =========================================================================
    
    def obtener_ordenes_por_producto(
        self, 
        producto_codigo: str,
        limit: int = 50
    ) -> List[OrdenFabricacionResumenDTO]:
        """
        Obtiene todas las órdenes de fabricación de un producto,
        ordenadas por fecha (más reciente primero).
        
        Args:
            producto_codigo: Código del producto
            limit: Número máximo de órdenes a retornar
            
        Returns:
            Lista de OrdenFabricacionResumenDTO
        """
        def _operation(session: Session, **kwargs) -> List[OrdenFabricacionResumenDTO]:
            # Obtener descripción del producto una vez
            producto = session.query(Producto).filter(
                Producto.codigo == producto_codigo
            ).first()
            producto_desc = producto.descripcion if producto else ""
            
            # Agrupar trabajos por orden_fabricacion
            ordenes_data = session.query(
                TrabajoLog.orden_fabricacion,
                func.min(TrabajoLog.tiempo_inicio).label('fecha_inicio'),
                func.max(TrabajoLog.tiempo_fin).label('fecha_fin'),
                func.count(TrabajoLog.id).label('cantidad'),
                func.sum(TrabajoLog.duracion_segundos).label('tiempo_total')
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo,
                TrabajoLog.orden_fabricacion.isnot(None)
            ).group_by(
                TrabajoLog.orden_fabricacion
            ).order_by(
                desc('fecha_inicio')
            ).limit(limit).all()
            
            results = []
            for orden_data in ordenes_data:
                # Contar incidencias para esta orden
                incidencias_count = session.query(func.count(IncidenciaLog.id)).join(
                    TrabajoLog
                ).filter(
                    TrabajoLog.producto_codigo == producto_codigo,
                    TrabajoLog.orden_fabricacion == orden_data.orden_fabricacion
                ).scalar() or 0
                
                # Determinar estado
                hay_trabajos_abiertos = session.query(TrabajoLog).filter(
                    TrabajoLog.producto_codigo == producto_codigo,
                    TrabajoLog.orden_fabricacion == orden_data.orden_fabricacion,
                    TrabajoLog.estado.in_(['en_proceso', 'pausado'])
                ).first() is not None
                
                estado = "en_proceso" if hay_trabajos_abiertos else "completado"
                
                results.append(OrdenFabricacionResumenDTO(
                    orden_fabricacion=orden_data.orden_fabricacion or "Sin OF",
                    producto_codigo=producto_codigo,
                    producto_descripcion=producto_desc,
                    fecha_inicio=orden_data.fecha_inicio,
                    fecha_fin=orden_data.fecha_fin,
                    cantidad_unidades=orden_data.cantidad or 0,
                    tiempo_total_segundos=orden_data.tiempo_total or 0,
                    incidencias_count=incidencias_count,
                    estado=estado
                ))
            
            return results
        
        return self.safe_execute(_operation) or []
    
    def obtener_detalle_orden(
        self, 
        orden_fabricacion: str
    ) -> Optional[OrdenFabricacionDetalleDTO]:
        """
        Obtiene el detalle completo de una orden de fabricación.
        
        Args:
            orden_fabricacion: Identificador de la orden
            
        Returns:
            OrdenFabricacionDetalleDTO o None si no existe
        """
        def _operation(session: Session, **kwargs) -> Optional[OrdenFabricacionDetalleDTO]:
            # Obtener datos agregados
            datos = session.query(
                TrabajoLog.producto_codigo,
                func.min(TrabajoLog.tiempo_inicio).label('fecha_inicio'),
                func.max(TrabajoLog.tiempo_fin).label('fecha_fin'),
                func.count(TrabajoLog.id).label('cantidad'),
                func.sum(TrabajoLog.duracion_segundos).label('tiempo_total'),
                func.avg(TrabajoLog.duracion_segundos).label('tiempo_promedio')
            ).filter(
                TrabajoLog.orden_fabricacion == orden_fabricacion
            ).group_by(
                TrabajoLog.producto_codigo
            ).first()
            
            if not datos:
                return None
            
            # Obtener descripción del producto
            producto = session.query(Producto).filter(
                Producto.codigo == datos.producto_codigo
            ).first()
            producto_desc = producto.descripcion if producto else ""
            
            # Contar incidencias
            incidencias_count = session.query(func.count(IncidenciaLog.id)).join(
                TrabajoLog
            ).filter(
                TrabajoLog.orden_fabricacion == orden_fabricacion
            ).scalar() or 0
            
            # Obtener trabajadores únicos
            trabajadores = session.query(
                distinct(Trabajador.nombre_completo)
            ).join(
                TrabajoLog, TrabajoLog.trabajador_id == Trabajador.id
            ).filter(
                TrabajoLog.orden_fabricacion == orden_fabricacion
            ).all()
            
            trabajadores_nombres = [t[0] for t in trabajadores if t[0]]
            
            # Determinar estado
            hay_abiertos = session.query(TrabajoLog).filter(
                TrabajoLog.orden_fabricacion == orden_fabricacion,
                TrabajoLog.estado.in_(['en_proceso', 'pausado'])
            ).first() is not None
            
            return OrdenFabricacionDetalleDTO(
                orden_fabricacion=orden_fabricacion,
                producto_codigo=datos.producto_codigo,
                producto_descripcion=producto_desc,
                fecha_inicio=datos.fecha_inicio,
                fecha_fin=datos.fecha_fin,
                cantidad_unidades=datos.cantidad or 0,
                tiempo_total_segundos=int(datos.tiempo_total or 0),
                tiempo_promedio_segundos=float(datos.tiempo_promedio or 0),
                incidencias_count=incidencias_count,
                trabajadores_involucrados=trabajadores_nombres,
                estado="en_proceso" if hay_abiertos else "completado"
            )
        
        return self.safe_execute(_operation)
    
    # =========================================================================
    # ESTADÍSTICAS DE TIEMPO
    # =========================================================================
    
    def calcular_promedio_tiempo_unidad(
        self, 
        producto_codigo: str,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Optional[PromedioTiempoDTO]:
        """
        Calcula el tiempo promedio por unidad para un producto.
        
        Args:
            producto_codigo: Código del producto
            fecha_inicio: Filtrar desde esta fecha (opcional)
            fecha_fin: Filtrar hasta esta fecha (opcional)
            
        Returns:
            PromedioTiempoDTO con estadísticas de tiempo
        """
        def _operation(session: Session, **kwargs) -> Optional[PromedioTiempoDTO]:
            # Construir query base
            query = session.query(
                func.avg(TrabajoLog.duracion_segundos).label('promedio'),
                func.min(TrabajoLog.duracion_segundos).label('minimo'),
                func.max(TrabajoLog.duracion_segundos).label('maximo'),
                func.count(TrabajoLog.id).label('total')
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo,
                TrabajoLog.duracion_segundos.isnot(None),
                TrabajoLog.duracion_segundos > 0
            )
            
            if fecha_inicio:
                query = query.filter(TrabajoLog.tiempo_inicio >= fecha_inicio)
            if fecha_fin:
                query = query.filter(TrabajoLog.tiempo_inicio <= fecha_fin)
            
            resultado = query.first()
            
            if not resultado or resultado.total == 0:
                return None
            
            # Obtener descripción del producto
            producto = session.query(Producto).filter(
                Producto.codigo == producto_codigo
            ).first()
            producto_desc = producto.descripcion if producto else ""
            
            # Calcular desviación estándar manualmente
            # SQLite no tiene stddev nativo, así que calculamos
            duraciones = session.query(TrabajoLog.duracion_segundos).filter(
                TrabajoLog.producto_codigo == producto_codigo,
                TrabajoLog.duracion_segundos.isnot(None),
                TrabajoLog.duracion_segundos > 0
            )
            if fecha_inicio:
                duraciones = duraciones.filter(TrabajoLog.tiempo_inicio >= fecha_inicio)
            if fecha_fin:
                duraciones = duraciones.filter(TrabajoLog.tiempo_inicio <= fecha_fin)
            
            valores = [d[0] for d in duraciones.all()]
            promedio = resultado.promedio
            
            if len(valores) > 1:
                varianza = sum((x - promedio) ** 2 for x in valores) / len(valores)
                desviacion = varianza ** 0.5
            else:
                desviacion = 0.0
            
            return PromedioTiempoDTO(
                producto_codigo=producto_codigo,
                producto_descripcion=producto_desc,
                promedio_segundos=float(resultado.promedio or 0),
                desviacion_estandar=desviacion,
                minimo_segundos=int(resultado.minimo or 0),
                maximo_segundos=int(resultado.maximo or 0),
                total_unidades=resultado.total,
                periodo_inicio=fecha_inicio,
                periodo_fin=fecha_fin
            )
        
        return self.safe_execute(_operation)
    
    def obtener_tiempos_por_trabajador(
        self, 
        producto_codigo: str
    ) -> List[TiempoTrabajadorDTO]:
        """
        Obtiene tiempos promedio agrupados por trabajador.
        Útil para comparar rendimiento entre operarios.
        
        Args:
            producto_codigo: Código del producto a analizar
            
        Returns:
            Lista de TiempoTrabajadorDTO ordenados por promedio (mejor primero)
        """
        def _operation(session: Session, **kwargs) -> List[TiempoTrabajadorDTO]:
            datos = session.query(
                Trabajador.id,
                Trabajador.nombre_completo,
                func.avg(TrabajoLog.duracion_segundos).label('promedio'),
                func.min(TrabajoLog.duracion_segundos).label('minimo'),
                func.max(TrabajoLog.duracion_segundos).label('maximo'),
                func.count(TrabajoLog.id).label('total')
            ).join(
                TrabajoLog, TrabajoLog.trabajador_id == Trabajador.id
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo,
                TrabajoLog.duracion_segundos.isnot(None),
                TrabajoLog.duracion_segundos > 0
            ).group_by(
                Trabajador.id, Trabajador.nombre_completo
            ).order_by(
                'promedio'
            ).all()
            
            results = []
            for d in datos:
                results.append(TiempoTrabajadorDTO(
                    trabajador_id=d.id,
                    trabajador_nombre=d.nombre_completo or "Desconocido",
                    promedio_segundos=float(d.promedio or 0),
                    minimo_segundos=int(d.minimo or 0),
                    maximo_segundos=int(d.maximo or 0),
                    unidades_realizadas=d.total
                ))
            
            return results
        
        return self.safe_execute(_operation) or []
    
    # =========================================================================
    # INCIDENCIAS
    # =========================================================================
    
    def obtener_incidencias_por_producto(
        self, 
        producto_codigo: str
    ) -> List[IncidenciaResumenDTO]:
        """
        Obtiene resumen de incidencias agrupadas por tipo.
        Útil para gráficas de patrón de incidencias.
        
        Args:
            producto_codigo: Código del producto
            
        Returns:
            Lista de IncidenciaResumenDTO con cantidad y porcentaje por tipo
        """
        def _operation(session: Session, **kwargs) -> List[IncidenciaResumenDTO]:
            # Contar incidencias por tipo
            datos = session.query(
                IncidenciaLog.tipo_incidencia,
                func.count(IncidenciaLog.id).label('cantidad')
            ).join(
                TrabajoLog
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo
            ).group_by(
                IncidenciaLog.tipo_incidencia
            ).all()
            
            # Calcular total para porcentajes
            total = sum(d.cantidad for d in datos) if datos else 0
            
            results = []
            for d in datos:
                porcentaje = (d.cantidad / total * 100) if total > 0 else 0
                results.append(IncidenciaResumenDTO(
                    tipo_incidencia=d.tipo_incidencia or "Sin clasificar",
                    cantidad=d.cantidad,
                    porcentaje=round(porcentaje, 1)
                ))
            
            # Ordenar por cantidad descendente
            results.sort(key=lambda x: x.cantidad, reverse=True)
            
            return results
        
        return self.safe_execute(_operation) or []
    
    # =========================================================================
    # EVOLUCIÓN TEMPORAL
    # =========================================================================
    
    def obtener_evolucion_temporal(
        self, 
        producto_codigo: str,
        dias: int = 30
    ) -> List[PuntoEvolucionDTO]:
        """
        Obtiene la evolución del tiempo promedio en los últimos N días.
        Útil para gráficas de tendencia.
        
        Args:
            producto_codigo: Código del producto
            dias: Número de días hacia atrás a considerar
            
        Returns:
            Lista de PuntoEvolucionDTO ordenados cronológicamente
        """
        def _operation(session: Session, **kwargs) -> List[PuntoEvolucionDTO]:
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            # SQLite usa strftime para agrupar por día
            datos = session.query(
                func.date(TrabajoLog.tiempo_inicio).label('fecha'),
                func.avg(TrabajoLog.duracion_segundos).label('promedio'),
                func.count(TrabajoLog.id).label('cantidad')
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo,
                TrabajoLog.tiempo_inicio >= fecha_limite,
                TrabajoLog.duracion_segundos.isnot(None),
                TrabajoLog.duracion_segundos > 0
            ).group_by(
                func.date(TrabajoLog.tiempo_inicio)
            ).order_by(
                'fecha'
            ).all()
            
            results = []
            for d in datos:
                if d.fecha:
                    # Convertir string de fecha a datetime
                    if isinstance(d.fecha, str):
                        fecha_dt = datetime.strptime(d.fecha, "%Y-%m-%d")
                    else:
                        fecha_dt = datetime.combine(d.fecha, datetime.min.time())
                    
                    results.append(PuntoEvolucionDTO(
                        fecha=fecha_dt,
                        promedio_segundos=float(d.promedio or 0),
                        cantidad_unidades=d.cantidad
                    ))
            
            return results
        
        return self.safe_execute(_operation) or []
    
    # =========================================================================
    # RESUMEN DE PRODUCTO
    # =========================================================================
    
    def obtener_resumen_producto(
        self, 
        producto_codigo: str
    ) -> Optional[ResumenProductoDTO]:
        """
        Obtiene un resumen estadístico completo de un producto.
        
        Args:
            producto_codigo: Código del producto
            
        Returns:
            ResumenProductoDTO con estadísticas generales
        """
        def _operation(session: Session, **kwargs) -> Optional[ResumenProductoDTO]:
            # Obtener datos del producto
            producto = session.query(Producto).filter(
                Producto.codigo == producto_codigo
            ).first()
            
            if not producto:
                return None
            
            # Estadísticas de TrabajoLog
            stats = session.query(
                func.count(distinct(TrabajoLog.orden_fabricacion)).label('total_ordenes'),
                func.count(TrabajoLog.id).label('total_unidades'),
                func.avg(TrabajoLog.duracion_segundos).label('tiempo_promedio'),
                func.min(TrabajoLog.tiempo_inicio).label('primera'),
                func.max(TrabajoLog.tiempo_inicio).label('ultima')
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo
            ).first()
            
            # Contar incidencias
            total_incidencias = session.query(func.count(IncidenciaLog.id)).join(
                TrabajoLog
            ).filter(
                TrabajoLog.producto_codigo == producto_codigo
            ).scalar() or 0
            
            return ResumenProductoDTO(
                producto_codigo=producto_codigo,
                producto_descripcion=producto.descripcion or "",
                total_ordenes=stats.total_ordenes or 0,
                total_unidades=stats.total_unidades or 0,
                tiempo_promedio_segundos=float(stats.tiempo_promedio or 0),
                total_incidencias=total_incidencias,
                fecha_primera_produccion=stats.primera,
                fecha_ultima_produccion=stats.ultima
            )
        
        return self.safe_execute(_operation)
    
    # =========================================================================
    # UNIDADES DE UNA ORDEN
    # =========================================================================
    
    def obtener_unidades_de_orden(
        self, 
        orden_fabricacion: str
    ) -> List[UnidadTrabajoDTO]:
        """
        Obtiene las unidades individuales de una orden para vista de detalle.
        
        Args:
            orden_fabricacion: Identificador de la orden
            
        Returns:
            Lista de UnidadTrabajoDTO ordenadas por tiempo de inicio
        """
        def _operation(session: Session, **kwargs) -> List[UnidadTrabajoDTO]:
            trabajos = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.incidencias)
            ).filter(
                TrabajoLog.orden_fabricacion == orden_fabricacion
            ).order_by(
                TrabajoLog.tiempo_inicio
            ).all()
            
            results = []
            for t in trabajos:
                trabajador_nombre = ""
                if t.trabajador:
                    trabajador_nombre = t.trabajador.nombre_completo or ""
                
                results.append(UnidadTrabajoDTO(
                    qr_code=t.qr_code,
                    tiempo_inicio=t.tiempo_inicio,
                    tiempo_fin=t.tiempo_fin,
                    duracion_segundos=t.duracion_segundos or 0,
                    trabajador_nombre=trabajador_nombre,
                    tiene_incidencias=len(t.incidencias) > 0 if t.incidencias else False
                ))
            
            return results
        
        return self.safe_execute(_operation) or []
