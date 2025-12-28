# -*- coding: utf-8 -*-
"""
========================================================================
TRACKING REPOSITORY - GESTIÃ“N DE TRAZABILIDAD Y SEGUIMIENTO
========================================================================
Repositorio para todas las operaciones relacionadas con:
- Registro de tiempos de trabajo (TrabajoLog)
- GestiÃ³n de incidencias (IncidenciaLog)
- Adjuntos fotogrÃ¡ficos (IncidenciaAdjunto)
- AsignaciÃ³n de trabajadores a fabricaciones

Autor: Sistema de Trazabilidad
Fecha: 2025
========================================================================
"""

import logging
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..models import Fabricacion, trabajador_fabricacion_link, fabricacion_productos
from sqlalchemy.orm import aliased

from database.models import (
    TrabajoLog, IncidenciaLog, IncidenciaAdjunto,
    Trabajador, Fabricacion, Producto,
    PasoTrazabilidad, Maquina
)
from .base import BaseRepository
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, 
    IncidenciaAdjuntoDTO, FabricacionAsignadaDTO
)
from core.tracking_dtos import (
    TrabajoLogDTO, PasoTrazabilidadDTO, IncidenciaLogDTO, 
    IncidenciaAdjuntoDTO, FabricacionAsignadaDTO
)

class TrackingRepository(BaseRepository):
    """
    Repositorio para operaciones de tracking y trazabilidad.

    Este repositorio maneja toda la lÃ³gica de negocio relacionada con:
    - Inicio y finalizaciÃ³n de trabajos
    - Registro de incidencias con fotos
    - Consultas de productividad y tiempos
    - AsignaciÃ³n de trabajadores a fabricaciones
    """

    def __init__(self, session_factory):
        """
        Inicializa el repositorio.

        Args:
            session_factory: Factory para crear sesiones de SQLAlchemy
        """
        super().__init__(session_factory)
        self.logger = logging.getLogger("EvolucionTiemposApp.TrackingRepository")

    # ========================================================================
    # TRABAJO LOGS - GESTIÃ“N DE TIEMPOS
    # ========================================================================

    def get_fabricaciones_por_trabajador(self, trabajador_id: int) -> List[FabricacionAsignadaDTO]:
        """
        Obtiene todas las fabricaciones asignadas a un trabajador específicamente,
        ordenadas por la más reciente primero, incluyendo los productos y cantidades.
        
        Returns:
            Lista de FabricacionAsignadaDTO
        """

        def _operation(session, **kwargs):
            # Realizamos la consulta uniendo Fabricacion con las tablas de enlace
            # y con la tabla de productos
            query_results = session.query(
                Fabricacion.id,
                Fabricacion.codigo,
                Fabricacion.descripcion,
                trabajador_fabricacion_link.c.fecha_asignacion,
                trabajador_fabricacion_link.c.estado,
                fabricacion_productos.c.producto_codigo,
                fabricacion_productos.c.cantidad,
                Producto.descripcion.label('producto_descripcion')
            ).join(
                trabajador_fabricacion_link,
                Fabricacion.id == trabajador_fabricacion_link.c.fabricacion_id
            ).outerjoin(
                fabricacion_productos,
                Fabricacion.id == fabricacion_productos.c.fabricacion_id
            ).outerjoin(
                Producto,
                fabricacion_productos.c.producto_codigo == Producto.codigo
            ).filter(
                # Filtramos por el ID del trabajador
                trabajador_fabricacion_link.c.trabajador_id == trabajador_id
            ).order_by(
                trabajador_fabricacion_link.c.fecha_asignacion.desc()
            ).all()

            # Convertimos los resultados a un diccionario intermedio
            fabricaciones_dict = {}

            for row in query_results:
                fab_id = row.id

                # Si es la primera vez que vemos esta fabricación, crear entrada
                if fab_id not in fabricaciones_dict:
                    fabricaciones_dict[fab_id] = FabricacionAsignadaDTO(
                        id=row.id,
                        codigo=row.codigo,
                        descripcion=row.descripcion,
                        fecha_asignacion=row.fecha_asignacion,
                        estado=row.estado,
                        productos=[]
                    )

                # Añadir producto si existe
                if row.producto_codigo:
                    fabricaciones_dict[fab_id].productos.append({
                        "codigo": row.producto_codigo,
                        "descripcion": row.producto_descripcion,
                        "cantidad": row.cantidad
                    })

            # Convertir el diccionario a lista
            results = list(fabricaciones_dict.values())

            return results

        # Usamos safe_execute para manejar la sesión y los errores
        return self.safe_execute(_operation, default_value=[])

    def actualizar_estado_asignacion(
            self,
            trabajador_id: int,
            fabricacion_id: int,
            nuevo_estado: str
    ) -> bool:
        """
        Actualiza el estado de una asignaciÃ³n de fabricaciÃ³n a un trabajador.

        Args:
            trabajador_id: ID del trabajador
            fabricacion_id: ID de la fabricaciÃ³n
            nuevo_estado: Nuevo estado ('activo', 'completado', 'cancelado')

        Returns:
            True si se actualizÃ³ correctamente, False en caso contrario
        """

        def _operation(session, **kwargs):
            # Buscar el registro en la tabla de enlace
            update_stmt = trabajador_fabricacion_link.update().where(
                and_(
                    trabajador_fabricacion_link.c.trabajador_id == trabajador_id,
                    trabajador_fabricacion_link.c.fabricacion_id == fabricacion_id
                )
            ).values(estado=nuevo_estado)

            result = session.execute(update_stmt)

            if result.rowcount > 0:
                self.logger.info(
                    f"Estado de asignaciÃ³n actualizado: Trabajador {trabajador_id}, "
                    f"FabricaciÃ³n {fabricacion_id}, Nuevo estado: {nuevo_estado}"
                )
                return True
            else:
                self.logger.warning(
                    f"No se encontrÃ³ asignaciÃ³n para actualizar: Trabajador {trabajador_id}, "
                    f"FabricaciÃ³n {fabricacion_id}"
                )
                return False

        return self.safe_execute(_operation, default_value=False)

    def obtener_o_crear_trabajo_log_por_qr(
            self,
            qr_code: str,
            trabajador_id: int,
            fabricacion_id: int,
            producto_codigo: str,
            orden_fabricacion: Optional[str] = None,
            notas: Optional[str] = None
    ) -> Optional[TrabajoLogDTO]:
        """
        Obtiene un TrabajoLog por QR si existe. Si no, lo crea.
        Este es el "pasaporte" de la unidad.

        Args:
            qr_code: Código QR único de la unidad
            trabajador_id: ID del trabajador que crea el registro
            fabricacion_id: ID de la fabricación
            producto_codigo: Código del producto
            orden_fabricacion: Número de orden (opcional)
            notas: Notas opcionales

        Returns:
            TrabajoLogDTO (existente o nuevo) o None si hay error
        """
        session = self.session_factory()
        try:
            # 1. Buscar si ya existe
            trabajo_existente = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter(
                TrabajoLog.qr_code == qr_code
            ).first()

            if trabajo_existente:
                self.logger.debug(f"TrabajoLog existente encontrado para QR: {qr_code} (ID: {trabajo_existente.id})")
                return self._map_to_trabajo_log_dto(trabajo_existente)

            # 2. Si no existe, crearlo
            self.logger.info(f"QR {qr_code} no existe. Creando nuevo TrabajoLog (Pasaporte)...")
            nuevo_trabajo = TrabajoLog(
                qr_code=qr_code,
                trabajador_id=trabajador_id,
                fabricacion_id=fabricacion_id,
                producto_codigo=producto_codigo,
                orden_fabricacion=orden_fabricacion,
                tiempo_inicio=datetime.now(timezone.utc),
                estado='en_proceso',
                notas=notas
            )

            session.add(nuevo_trabajo)
            session.commit()

            # Recargar con relaciones para el DTO
            trabajo_recargado = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter(TrabajoLog.id == nuevo_trabajo.id).first()

            self.logger.info(f"Nuevo TrabajoLog creado: QR={qr_code}, ID={trabajo_recargado.id}")
            return self._map_to_trabajo_log_dto(trabajo_recargado)

        except IntegrityError as e:
            session.rollback()
            self.logger.error(f"Error de integridad al obtener/crear trabajo: {e}")
            return None
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al obtener/crear trabajo: {e}")
            return None
        finally:
            session.close()

    def iniciar_trabajo(
        self,
        qr_code: str,
        trabajador_id: int,
        fabricacion_id: int,
        producto_codigo: str
    ) -> Optional[TrabajoLogDTO]:
        """
        Inicia un nuevo trabajo (Wrapper para obtener_o_crear_trabajo_log_por_qr).
        Mantiene compatibilidad con cÃ³digo existente.
        """
        return self.obtener_o_crear_trabajo_log_por_qr(
            qr_code=qr_code,
            trabajador_id=trabajador_id,
            fabricacion_id=fabricacion_id,
            producto_codigo=producto_codigo
        )

    def finalizar_trabajo_log(
            self,
            trabajo_log_id: int,
            notas_finalizacion: Optional[str] = None
    ) -> Optional[TrabajoLogDTO]:
        """
        Finaliza el TrabajoLog principal (el "pasaporte").
        Esto solo debe llamarse cuando se completa el ÚLTIMO paso.
        
        Args:
            trabajo_log_id: ID del TrabajoLog a finalizar
            notas_finalizacion: Notas al finalizar (opcional)

        Returns:
            TrabajoLogDTO actualizado o None si hay error
        """
        session = self.session_factory()
        try:
            # --- PASO 1: Consulta simple ---
            trabajo = session.query(TrabajoLog).filter(
                TrabajoLog.id == trabajo_log_id,
                TrabajoLog.estado == 'en_proceso'
            ).first()

            if not trabajo:
                self.logger.warning(f"No se encontró TrabajoLog 'en_proceso' con ID: {trabajo_log_id}")
                return None

            # --- PASO 2: Calcular y modificar ---
            tiempo_fin_aware = datetime.now(timezone.utc)
            # Asegurar que el tiempo de inicio tiene timezone
            tiempo_inicio_aware = trabajo.tiempo_inicio
            if tiempo_inicio_aware.tzinfo is None:
                tiempo_inicio_aware = tiempo_inicio_aware.replace(tzinfo=timezone.utc)

            duracion_total = (tiempo_fin_aware - tiempo_inicio_aware).total_seconds()

            trabajo.tiempo_fin = tiempo_fin_aware
            trabajo.duracion_segundos = int(duracion_total)
            trabajo.estado = 'completado'

            if notas_finalizacion:
                trabajo.notas = (trabajo.notas or "") + f"\n[Finalización] {notas_finalizacion}"

            trabajo.updated_at = datetime.now(timezone.utc)

            # --- PASO 3: Hacer commit ---
            session.commit()

            self.logger.info(
                f"TrabajoLog (Pasaporte) finalizado: ID={trabajo_log_id}, Duración Total={int(duracion_total)}s"
            )

            # --- PASO 4: Recargar el objeto con joinedload para DTO ---
            trabajo_cargado = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter(
                TrabajoLog.id == trabajo_log_id
            ).first()

            return self._map_to_trabajo_log_dto(trabajo_cargado)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al finalizar TrabajoLog: {e}", exc_info=True)
            return None
        finally:
            session.close()



    def pausar_trabajo(self, qr_code: str, motivo: str) -> bool:
        """
        Pausa un trabajo en proceso.

        Args:
            qr_code: CÃ³digo QR de la unidad
            motivo: Motivo de la pausa

        Returns:
            True si se pausÃ³ correctamente, False si no
        """
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).filter(
                TrabajoLog.qr_code == qr_code,
                TrabajoLog.estado == 'en_proceso'
            ).first()

            if not trabajo:
                return False

            trabajo.estado = 'pausado'
            trabajo.notas = (trabajo.notas or "") + f"\n[Pausa] {motivo}"
            trabajo.updated_at = datetime.now(timezone.utc)

            session.commit()
            self.logger.info(f"Trabajo pausado: QR={qr_code}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al pausar trabajo: {e}")
            return False
        finally:
            session.close()

    def reanudar_trabajo(self, qr_code: str) -> bool:
        """
        Reanuda un trabajo pausado.

        Args:
            qr_code: CÃ³digo QR de la unidad

        Returns:
            True si se reanudÃ³ correctamente, False si no
        """
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).filter(
                TrabajoLog.qr_code == qr_code,
                TrabajoLog.estado == 'pausado'
            ).first()

            if not trabajo:
                return False

            trabajo.estado = 'en_proceso'
            trabajo.notas = (trabajo.notas or "") + f"\n[ReanudaciÃ³n] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
            trabajo.updated_at = datetime.now(timezone.utc)

            session.commit()
            self.logger.info(f"Trabajo reanudado: QR={qr_code}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al reanudar trabajo: {e}")
            return False
        finally:
            session.close()

    def obtener_trabajo_por_qr(self, qr_code: str) -> Optional[TrabajoLogDTO]:
        """
        Obtiene un trabajo por su código QR.

        Args:
            qr_code: Código QR de la unidad

        Returns:
            TrabajoLogDTO o None si no existe
        """
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter(TrabajoLog.qr_code == qr_code).first()

            return self._map_to_trabajo_log_dto(trabajo)

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener trabajo por QR: {e}")
            return None
        finally:
            session.close()

    def obtener_trabajo_por_id(self, trabajo_log_id: int) -> Optional[TrabajoLogDTO]:
        """
        Obtiene un trabajo por su ID.

        Args:
            trabajo_log_id: ID del TrabajoLog

        Returns:
            TrabajoLogDTO o None si no existe
        """
        session = self.session_factory()
        try:
            trabajo = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias).joinedload(IncidenciaLog.adjuntos)
            ).filter(TrabajoLog.id == trabajo_log_id).first()

            return self._map_to_trabajo_log_dto(trabajo)

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener trabajo por ID: {e}")
            return None
        finally:
            session.close()

    # ========================================================================
    # PASOS DE TRAZABILIDAD (NUEVOS MÃ‰TODOS)
    # ========================================================================

    def get_paso_activo_por_trabajador(self, trabajador_id: int) -> Optional[PasoTrazabilidadDTO]:
        """
        Busca si un trabajador tiene un paso de trazabilidad en estado 'en_proceso'.
        Esto previene que un trabajador inicie dos tareas a la vez.

        Args:
            trabajador_id: ID del trabajador

        Returns:
            El objeto PasoTrazabilidadDTO activo, o None si no tiene ninguno.
        """
        from sqlalchemy.orm import defer, joinedload

        session = self.session_factory()
        try:
            paso_activo = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.trabajador),
                joinedload(PasoTrazabilidad.trabajador),
                joinedload(PasoTrazabilidad.maquina)
            ).filter(
                PasoTrazabilidad.trabajador_id == trabajador_id,
                PasoTrazabilidad.estado_paso == 'en_proceso'
            ).order_by(
                PasoTrazabilidad.tiempo_inicio_paso.desc()
            ).first()

            return self._map_to_paso_trazabilidad_dto(paso_activo)

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener paso activo para trabajador {trabajador_id}: {e}")
            return None
        finally:
            session.close()

    def get_ultimo_paso_para_qr(self, trabajo_log_id: int) -> Optional[PasoTrazabilidadDTO]:
        """
        Obtiene el último paso (más reciente) registrado para un TrabajoLog (QR).

        Args:
            trabajo_log_id: ID del TrabajoLog (el "pasaporte")

        Returns:
            El último objeto PasoTrazabilidadDTO, o None si no tiene ninguno.
        """
        from sqlalchemy.orm import defer

        session = self.session_factory()
        try:
            ultimo_paso = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log),
                joinedload(PasoTrazabilidad.maquina),
                joinedload(PasoTrazabilidad.trabajador)
            ).filter(
                PasoTrazabilidad.trabajo_log_id == trabajo_log_id
            ).order_by(
                PasoTrazabilidad.tiempo_inicio_paso.desc()
            ).first()

            return self._map_to_paso_trazabilidad_dto(ultimo_paso)

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener último paso para trabajo_log {trabajo_log_id}: {e}")
            return None
        finally:
            session.close()

    def iniciar_nuevo_paso(
            self,
            trabajo_log_id: int,
            trabajador_id: int,
            paso_nombre: str,
            tipo_paso: str,
            maquina_id: Optional[int] = None
    ) -> Optional[PasoTrazabilidadDTO]:
        """
        Crea un nuevo registro de PasoTrazabilidad (un "sello").
        """
        from sqlalchemy.orm import joinedload

        session = self.session_factory()
        try:
            nuevo_paso = PasoTrazabilidad(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                maquina_id=maquina_id,
                paso_nombre=paso_nombre,
                tipo_paso=tipo_paso,
                tiempo_inicio_paso=datetime.now(timezone.utc),
                tiempo_fin_paso=None,
                estado_paso='en_proceso'
            )

            session.add(nuevo_paso)
            session.flush()

            nuevo_paso_id = nuevo_paso.id
            session.commit()

            # Recargar para DTO
            paso_cargado = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajador),
                joinedload(PasoTrazabilidad.maquina)
            ).filter(
                PasoTrazabilidad.id == nuevo_paso_id
            ).first()

            return self._map_to_paso_trazabilidad_dto(paso_cargado)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al iniciar nuevo paso: {e}")
            return None
        finally:
            session.close()

    def finalizar_paso(
            self,
            paso_id: int
    ) -> Optional[PasoTrazabilidadDTO]:
        """
        Finaliza un PasoTrazabilidad, calculando su duración.

        Args:
            paso_id: ID del PasoTrazabilidad a finalizar.

        Returns:
            El objeto PasoTrazabilidadDTO actualizado.
        """
        from sqlalchemy.orm import joinedload

        session = self.session_factory()
        try:
            # --- PASO 1: Consulta simple ---
            paso = session.query(PasoTrazabilidad).filter(
                PasoTrazabilidad.id == paso_id,
                PasoTrazabilidad.estado_paso == 'en_proceso'
            ).first()

            if not paso:
                self.logger.warning(f"No se encontró paso 'en_proceso' con ID: {paso_id}")
                return None

            # --- PASO 2: Calcular y modificar ---
            tiempo_fin_aware = datetime.now(timezone.utc)
            # Asegurarse que el tiempo de inicio tiene timezone
            tiempo_inicio_aware = paso.tiempo_inicio_paso
            if tiempo_inicio_aware.tzinfo is None:
                tiempo_inicio_aware = tiempo_inicio_aware.replace(tzinfo=timezone.utc)

            duracion_total = (tiempo_fin_aware - tiempo_inicio_aware).total_seconds()

            paso.tiempo_fin_paso = tiempo_fin_aware
            paso.duracion_paso_segundos = int(duracion_total)
            paso.estado_paso = 'completado'

            # --- PASO 3: Hacer commit ---
            session.commit()

            self.logger.info(f"Paso finalizado (ID: {paso.id}), Duración: {paso.duracion_paso_segundos}s")

            # --- PASO 4: Recargar el objeto con joinedload para DTO ---
            paso_cargado = session.query(PasoTrazabilidad).options(
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.fabricacion),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.producto),
                joinedload(PasoTrazabilidad.trabajo_log).joinedload(TrabajoLog.trabajador),
                joinedload(PasoTrazabilidad.trabajador),
                joinedload(PasoTrazabilidad.maquina)
            ).filter(
                PasoTrazabilidad.id == paso_id
            ).first()

            return self._map_to_paso_trazabilidad_dto(paso_cargado)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al finalizar paso: {e}")
            return None
        finally:
            session.close()

    def obtener_trabajos_activos(
        self,
        trabajador_id: Optional[int] = None,
        fabricacion_id: Optional[int] = None
    ) -> List[TrabajoLogDTO]:
        """
        Obtiene todos los trabajos activos (en_proceso o pausados).

        Args:
            trabajador_id: Filtrar por trabajador (opcional)
            fabricacion_id: Filtrar por fabricaciÃ³n (opcional)

        Returns:
            Lista de TrabajoLogDTO activos
        """
        session = self.session_factory()
        try:
            query = session.query(TrabajoLog).filter(
                TrabajoLog.estado.in_(['en_proceso', 'pausado'])
            )

            if trabajador_id:
                query = query.filter(TrabajoLog.trabajador_id == trabajador_id)

            if fabricacion_id:
                query = query.filter(TrabajoLog.fabricacion_id == fabricacion_id)

            # Load relationships eagerly for DTO mapping
            trabajos = query.options(
                joinedload(TrabajoLog.trabajador),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.incidencias)
            ).all()

            return [self._map_to_trabajo_log_dto(t) for t in trabajos]

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener trabajos activos: {e}")
            return []
        finally:
            session.close()

    # ========================================================================
    # INCIDENCIAS - GESTIÃ“N DE PROBLEMAS
    # ========================================================================

    def registrar_incidencia(
            self,
            trabajo_log_id: int,
            trabajador_id: int,
            tipo_incidencia: str,
            descripcion: str,
            rutas_fotos: Optional[List[str]] = None
    ) -> Optional[IncidenciaLogDTO]:
        """
        Registra una nueva incidencia.
        """
        session = self.session_factory()
        try:
            # Crear incidencia
            incidencia = IncidenciaLog(
                trabajo_log_id=trabajo_log_id,
                trabajador_id=trabajador_id,
                tipo_incidencia=tipo_incidencia,
                descripcion=descripcion,
                fecha_reporte=datetime.now(timezone.utc),
                estado='abierta'
            )

            session.add(incidencia)
            session.flush()  # Para obtener el ID

            # Guardamos el ID para la recarga
            nueva_incidencia_id = incidencia.id

            # Añadir fotos si las hay
            if rutas_fotos:
                for ruta in rutas_fotos:
                    self._crear_adjunto(session, nueva_incidencia_id, ruta)

            session.commit()  # Guardamos todo en la BD

            # Recargar con DTO
            incidencia_cargada = session.query(IncidenciaLog).options(
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.adjuntos)
            ).filter(
                IncidenciaLog.id == nueva_incidencia_id
            ).first()

            return self._map_to_incidencia_log_dto(incidencia_cargada)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al registrar incidencia: {e}")
            return None
        finally:
            session.close()

    def _crear_adjunto(
        self,
        session: Session,
        incidencia_id: int,
        ruta_archivo: str
    ) -> Optional[IncidenciaAdjunto]:
        """
        Crea un adjunto fotogrÃ¡fico (uso interno).

        Args:
            session: SesiÃ³n activa de SQLAlchemy
            incidencia_id: ID de la incidencia
            ruta_archivo: Ruta completa del archivo

        Returns:
            IncidenciaAdjunto creado
        """
        import os

        nombre_archivo = os.path.basename(ruta_archivo)

        # Detectar tipo MIME bÃ¡sico
        extension = os.path.splitext(nombre_archivo)[1].lower()
        tipo_mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        tipo_mime = tipo_mime_map.get(extension, 'application/octet-stream')

        # Obtener tamaÃ±o del archivo
        tamano = os.path.getsize(ruta_archivo) if os.path.exists(ruta_archivo) else 0

        adjunto = IncidenciaAdjunto(
            incidencia_id=incidencia_id,
            ruta_archivo=ruta_archivo,
            nombre_archivo=nombre_archivo,
            tipo_mime=tipo_mime,
            tamano_bytes=tamano,
            fecha_subida=datetime.now(timezone.utc)
        )

        session.add(adjunto)
        return adjunto

    def añadir_foto_a_incidencia(
        self,
        incidencia_id: int,
        ruta_foto: str,
        descripcion: Optional[str] = None
    ) -> Optional[IncidenciaAdjuntoDTO]:
        """
        Añade una foto a una incidencia existente.

        Args:
            incidencia_id: ID de la incidencia
            ruta_foto: Ruta de la foto
            descripcion: Descripción de la foto (opcional)

        Returns:
            IncidenciaAdjuntoDTO creado o None si hay error
        """
        session = self.session_factory()
        try:
            adjunto = self._crear_adjunto(session, incidencia_id, ruta_foto)
            if descripcion:
                adjunto.descripcion = descripcion

            session.commit()
            
            # Recargar para asegurar IDs y consistencia (aunque adjunto ya tiene ID post-flush/commit)
            session.refresh(adjunto)
            
            self.logger.info(f"Foto añadida a incidencia {incidencia_id}")
            return self._map_to_incidencia_adjunto_dto(adjunto)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al añadir foto: {e}")
            return None
        finally:
            session.close()

    def resolver_incidencia(
        self,
        incidencia_id: int,
        resolucion: str
    ) -> Optional[IncidenciaLogDTO]:
        """
        Marca una incidencia como resuelta.

        Args:
            incidencia_id: ID de la incidencia
            resolucion: Descripción de la resolución

        Returns:
            IncidenciaLogDTO actualizado o None si hay error
        """
        session = self.session_factory()
        try:
            incidencia = session.query(IncidenciaLog).options(
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.adjuntos)
            ).filter(
                IncidenciaLog.id == incidencia_id
            ).first()

            if not incidencia:
                return None

            incidencia.estado = 'resuelta'
            incidencia.resolucion = resolucion
            incidencia.fecha_resolucion = datetime.now(timezone.utc)

            session.commit()
            self.logger.info(f"Incidencia {incidencia_id} resuelta")
            
            return self._map_to_incidencia_log_dto(incidencia)

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al resolver incidencia: {e}")
            return None
        finally:
            session.close()

    def obtener_incidencias_abiertas(
        self,
        fabricacion_id: Optional[int] = None
    ) -> List[IncidenciaLogDTO]:
        """
        Obtiene todas las incidencias abiertas.

        Args:
            fabricacion_id: Filtrar por fabricación (opcional)

        Returns:
            Lista de IncidenciaLogDTO abiertas
        """
        session = self.session_factory()
        try:
            query = session.query(IncidenciaLog).filter(
                IncidenciaLog.estado == 'abierta'
            )

            if fabricacion_id:
                query = query.join(TrabajoLog).filter(
                    TrabajoLog.fabricacion_id == fabricacion_id
                )

            incidencias = query.options(
                joinedload(IncidenciaLog.trabajo_log),
                joinedload(IncidenciaLog.trabajador),
                joinedload(IncidenciaLog.adjuntos)
            ).all()

            return [self._map_to_incidencia_log_dto(i) for i in incidencias]

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener incidencias abiertas: {e}")
            return []
        finally:
            session.close()

    # ========================================================================
    # ASIGNACIÃ“N DE TRABAJADORES A FABRICACIONES
    # ========================================================================

    def asignar_trabajador_a_fabricacion(
        self,
        trabajador_id: int,
        fabricacion_id: int
    ) -> bool:
        """
        Asigna un trabajador a una fabricaciÃ³n.

        Args:
            trabajador_id: ID del trabajador
            fabricacion_id: ID de la fabricaciÃ³n

        Returns:
            True si se asignÃ³ correctamente, False si no
        """
        session = self.session_factory()
        try:
            trabajador = session.query(Trabajador).filter(
                Trabajador.id == trabajador_id
            ).first()

            fabricacion = session.query(Fabricacion).filter(
                Fabricacion.id == fabricacion_id
            ).first()

            if not trabajador or not fabricacion:
                self.logger.warning(
                    f"Trabajador {trabajador_id} o FabricaciÃ³n {fabricacion_id} no encontrados"
                )
                return False

            # Verificar si ya estÃ¡ asignado
            if fabricacion in trabajador.fabricaciones_asignadas:
                self.logger.info(f"Trabajador ya asignado a la fabricaciÃ³n")
                return True

            # Asignar
            trabajador.fabricaciones_asignadas.append(fabricacion)
            session.commit()

            self.logger.info(
                f"Trabajador {trabajador_id} asignado a FabricaciÃ³n {fabricacion_id}"
            )
            return True

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al asignar trabajador: {e}")
            return False
        finally:
            session.close()

    def desasignar_trabajador_de_fabricacion(
        self,
        trabajador_id: int,
        fabricacion_id: int
    ) -> bool:
        """
        Desasigna un trabajador de una fabricaciÃ³n.

        Args:
            trabajador_id: ID del trabajador
            fabricacion_id: ID de la fabricaciÃ³n

        Returns:
            True si se desasignÃ³ correctamente, False si no
        """
        session = self.session_factory()
        try:
            trabajador = session.query(Trabajador).filter(
                Trabajador.id == trabajador_id
            ).first()

            fabricacion = session.query(Fabricacion).filter(
                Fabricacion.id == fabricacion_id
            ).first()

            if not trabajador or not fabricacion:
                return False

            if fabricacion in trabajador.fabricaciones_asignadas:
                trabajador.fabricaciones_asignadas.remove(fabricacion)
                session.commit()
                self.logger.info(
                    f"Trabajador {trabajador_id} desasignado de FabricaciÃ³n {fabricacion_id}"
                )
                return True

            return False

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al desasignar trabajador: {e}")
            return False
        finally:
            session.close()

    def obtener_trabajadores_de_fabricacion(
        self,
        fabricacion_id: int
    ) -> List[Trabajador]:
        """
        Obtiene todos los trabajadores asignados a una fabricaciÃ³n.

        Args:
            fabricacion_id: ID de la fabricaciÃ³n

        Returns:
            Lista de Trabajador asignados
        """
        session = self.session_factory()
        try:
            fabricacion = session.query(Fabricacion).options(
                joinedload(Fabricacion.trabajadores_asignados)
            ).filter(Fabricacion.id == fabricacion_id).first()

            if not fabricacion:
                return []

            return fabricacion.trabajadores_asignados

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener trabajadores de fabricaciÃ³n: {e}")
            return []
        finally:
            session.close()

    # ========================================================================
    # ESTADÃSTICAS Y REPORTES
    # ========================================================================

    def obtener_estadisticas_trabajador(
        self,
        trabajador_id: int,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None
    ) -> Dict:
        """
        Obtiene estadÃ­sticas de un trabajador.

        Args:
            trabajador_id: ID del trabajador
            fecha_inicio: Fecha de inicio del periodo (opcional)
            fecha_fin: Fecha de fin del periodo (opcional)

        Returns:
            Diccionario con estadÃ­sticas
        """
        session = self.session_factory()
        try:
            query = session.query(TrabajoLog).filter(
                TrabajoLog.trabajador_id == trabajador_id,
                TrabajoLog.estado == 'completado'
            )

            if fecha_inicio:
                query = query.filter(TrabajoLog.tiempo_inicio >= fecha_inicio)
            if fecha_fin:
                query = query.filter(TrabajoLog.tiempo_fin <= fecha_fin)

            trabajos = query.all()

            if not trabajos:
                return {
                    'unidades_completadas': 0,
                    'tiempo_total_segundos': 0,
                    'tiempo_promedio_segundos': 0,
                    'tiempo_minimo_segundos': 0,
                    'tiempo_maximo_segundos': 0
                }

            duraciones = [t.duracion_segundos for t in trabajos if t.duracion_segundos]

            return {
                'unidades_completadas': len(trabajos),
                'tiempo_total_segundos': sum(duraciones),
                'tiempo_promedio_segundos': sum(duraciones) // len(duraciones) if duraciones else 0,
                'tiempo_minimo_segundos': min(duraciones) if duraciones else 0,
                'tiempo_maximo_segundos': max(duraciones) if duraciones else 0
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener estadÃ­sticas: {e}")
            return {}
        finally:
            session.close()

    def obtener_estadisticas_fabricacion(
        self,
        fabricacion_id: int
    ) -> Dict:
        """
        Obtiene estadÃ­sticas de una fabricaciÃ³n.

        Args:
            fabricacion_id: ID de la fabricaciÃ³n

        Returns:
            Diccionario con estadÃ­sticas
        """
        session = self.session_factory()
        try:
            # Trabajos completados
            completados = session.query(func.count(TrabajoLog.id)).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                TrabajoLog.estado == 'completado'
            ).scalar()

            # Trabajos en proceso
            en_proceso = session.query(func.count(TrabajoLog.id)).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                TrabajoLog.estado == 'en_proceso'
            ).scalar()

            # Incidencias abiertas
            incidencias_abiertas = session.query(func.count(IncidenciaLog.id)).join(
                TrabajoLog
            ).filter(
                TrabajoLog.fabricacion_id == fabricacion_id,
                IncidenciaLog.estado == 'abierta'
            ).scalar()

            return {
                'unidades_completadas': completados or 0,
                'unidades_en_proceso': en_proceso or 0,
                'incidencias_abiertas': incidencias_abiertas or 0,
                'trabajadores_asignados': len(self.obtener_trabajadores_de_fabricacion(fabricacion_id))
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener estadÃ­sticas de fabricaciÃ³n: {e}")
            return {}
        finally:
            session.close()

    def get_trabajo_logs_por_trabajador(self, trabajador_id: int) -> List[TrabajoLogDTO]:
        """
        Obtiene todos los registros de trabajo (fichajes) de un trabajador,
        ordenados por el mÃ¡s reciente.

        Args:
            trabajador_id: ID del trabajador

        Returns:
            Lista de TrabajoLogDTO.
        """
        session = self.session_factory()
        try:
            # Consultamos la entidad ORM directamente con sus relaciones cargadas
            query = session.query(TrabajoLog).options(
                joinedload(TrabajoLog.incidencias),
                joinedload(TrabajoLog.fabricacion),
                joinedload(TrabajoLog.producto),
                joinedload(TrabajoLog.trabajador)
            ).filter(
                TrabajoLog.trabajador_id == trabajador_id
            ).order_by(
                TrabajoLog.tiempo_inicio.desc()
            )

            results = query.all()
            return [self._map_to_trabajo_log_dto(log) for log in results]

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener logs de trabajador: {e}")
            return []
        finally:
            session.close()

    def upsert_trabajo_log_from_dict(self, data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        """
        Inserta o actualiza un TrabajoLog desde un diccionario (JSON).
        Maneja anidamiento de incidencias y adjuntos.

        Args:
            data: Diccionario con los datos del TrabajoLog

        Returns:
            Tuple (str: 'created'/'updated'/'skipped'/'error', int: id_trabajo)
        """
        session = self.session_factory()
        try:
            qr_code = data.get('qr_code')
            if not qr_code:
                return 'error', None

            # Convertir fechas ISO de vuelta a datetime
            for key in ['tiempo_inicio', 'tiempo_fin', 'created_at', 'updated_at']:
                if data.get(key) and isinstance(data[key], str):
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))

            # 1. Buscar si el trabajo ya existe
            trabajo = session.query(TrabajoLog).filter_by(qr_code=qr_code).first()

            # Extraer incidencias y adjuntos
            incidencias_data = data.pop('incidencias', [])

            # Limpiar claves que no estÃ¡n en el modelo TrabajoLog (si las hubiera)
            trabajo_log_keys = TrabajoLog.__table__.columns.keys()
            trabajo_data_clean = {k: v for k, v in data.items() if k in trabajo_log_keys}

            if trabajo:
                # --- ACTUALIZAR ---
                # No actualizamos si el trabajo local es mÃ¡s nuevo
                local_updated = trabajo.updated_at or trabajo.created_at
                remote_updated = trabajo_data_clean.get('updated_at') or trabajo_data_clean.get('created_at')

                if local_updated and remote_updated and local_updated >= remote_updated:
                    return 'skipped', trabajo.id

                for key, value in trabajo_data_clean.items():
                    setattr(trabajo, key, value)

                session.commit()
                status = 'updated'
                trabajo_id = trabajo.id
            else:
                # --- CREAR ---
                trabajo = TrabajoLog(**trabajo_data_clean)
                session.add(trabajo)
                session.flush()  # Para obtener el ID
                status = 'created'
                trabajo_id = trabajo.id

            # 2. Sincronizar Incidencias
            for inc_data in incidencias_data:
                # Convertir fechas
                for key in ['fecha_reporte', 'fecha_resolucion']:
                    if inc_data.get(key) and isinstance(inc_data[key], str):
                        inc_data[key] = datetime.fromisoformat(inc_data[key].replace('Z', '+00:00'))

                adjuntos_data = inc_data.pop('adjuntos', [])
                inc_data['trabajo_log_id'] = trabajo_id

                # Elimina el ID antiguo para forzar la creación de uno nuevo
                inc_data.pop('id', None)

                incidencia_log_keys = IncidenciaLog.__table__.columns.keys()
                incidencia_data_clean = {k: v for k, v in inc_data.items() if k in incidencia_log_keys}

                # Asumimos que no hay incidencias duplicadas (basado en ID es difÃ­cil)
                # Sencillamente las creamos si no existen
                # (Una lÃ³gica mÃ¡s robusta buscarÃ­a por trabajo_id y timestamp)
                incidencia = IncidenciaLog(**incidencia_data_clean)
                session.add(incidencia)
                session.flush()  # Obtener ID de incidencia

                # 3. Sincronizar Adjuntos
                for adj_data in adjuntos_data:
                    adj_data['incidencia_id'] = incidencia.id

                    # Elimina también el ID antiguo del adjunto
                    adj_data.pop('id', None)

                    adj_log_keys = IncidenciaAdjunto.__table__.columns.keys()
                    adj_data_clean = {k: v for k, v in adj_data.items() if k in adj_log_keys}

                    adjunto = IncidenciaAdjunto(**adj_data_clean)
                    session.add(adjunto)

            session.commit()
            return status, trabajo_id

        except Exception as e:
            session.rollback()
            self.logger.error(f"Error en upsert_trabajo_log_from_dict: {e}", exc_info=True)
            return 'error', None
        finally:
            session.close()

        # ========================================================================
        # EXPORTACIÃ“N DE DATOS
        # ========================================================================

    def get_data_for_export(
            self,
            trabajador_id: int,
            since_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Recopila todos los datos de un trabajador creados desde una fecha específica.
        Incluye TrabajoLogs, PasosTrazabilidad, IncidenciaLogs y IncidenciaAdjuntos.

        Args:
            trabajador_id: ID del trabajador
            since_date: Fecha (en UTC) desde la cual exportar

        Returns:
            Lista de diccionarios (serializables a JSON) con todos los datos.
        """
        from sqlalchemy.orm import load_only

        def _to_dict(obj):
            """Convierte un objeto SQLAlchemy a un diccionario."""
            data = {}

            # Obtener solo atributos que no sean internos de SQLAlchemy
            for key in dir(obj):
                if not key.startswith('_') and key not in ['metadata', 'registry']:
                    try:
                        value = getattr(obj, key)
                        # Evitar métodos y relaciones
                        if not callable(value) and not hasattr(value, '_sa_instance_state'):
                            if isinstance(value, datetime):
                                data[key] = value.isoformat()
                            elif isinstance(value, (str, int, float, bool)) or value is None:
                                data[key] = value
                    except Exception:
                        pass

            return data

        session = self.session_factory()
        try:
            # Asegurar que since_date tenga timezone
            if since_date.tzinfo is None:
                since_date = since_date.replace(tzinfo=timezone.utc)

            # 1. Obtener todos los TrabajoLog relevantes
            trabajos_query = session.query(TrabajoLog).filter(
                TrabajoLog.trabajador_id == trabajador_id,
                TrabajoLog.created_at >= since_date
            ).order_by(TrabajoLog.created_at)

            trabajos = trabajos_query.all()

            export_data = []

            # 2. Convertir todo a diccionarios
            for trabajo in trabajos:
                # Expulsar para evitar problemas al cerrar sesión
                session.expunge(trabajo)

                trabajo_dict = _to_dict(trabajo)
                trabajo_id = trabajo.id

                # 3. Obtener Pasos de Trazabilidad para este trabajo
                # Usar una consulta separada con load_only
                pasos_query = session.query(PasoTrazabilidad).options(
                    load_only(
                        PasoTrazabilidad.id,
                        PasoTrazabilidad.trabajo_log_id,
                        PasoTrazabilidad.trabajador_id,
                        PasoTrazabilidad.maquina_id,
                        PasoTrazabilidad.paso_nombre,
                        PasoTrazabilidad.tipo_paso,
                        PasoTrazabilidad.tiempo_inicio_paso,
                        PasoTrazabilidad.estado_paso,
                        PasoTrazabilidad.duracion_paso_segundos
                    )
                ).filter(
                    PasoTrazabilidad.trabajo_log_id == trabajo_id
                ).order_by(PasoTrazabilidad.tiempo_inicio_paso)

                pasos = pasos_query.all()
                pasos_list = []

                for paso in pasos:
                    session.expunge(paso)
                    paso_dict = _to_dict(paso)

                    # Si el paso está completado, obtener tiempo_fin_paso por separado
                    if paso.estado_paso == 'completado':
                        # Hacer una consulta específica para obtener tiempo_fin_paso
                        paso_completo = session.query(PasoTrazabilidad).filter(
                            PasoTrazabilidad.id == paso.id
                        ).first()
                        if paso_completo and paso_completo.tiempo_fin_paso:
                            paso_dict['tiempo_fin_paso'] = paso_completo.tiempo_fin_paso.isoformat()
                        session.expunge(paso_completo)
                    else:
                        paso_dict['tiempo_fin_paso'] = None

                    pasos_list.append(paso_dict)

                trabajo_dict['pasos_trazabilidad'] = pasos_list

                # 4. Obtener incidencias para este trabajo
                incidencias_query = session.query(IncidenciaLog).filter(
                    IncidenciaLog.trabajo_log_id == trabajo_id
                ).order_by(IncidenciaLog.fecha_reporte)

                incidencias = incidencias_query.all()
                incidencias_list = []

                for incidencia in incidencias:
                    session.expunge(incidencia)
                    incidencia_dict = _to_dict(incidencia)
                    incidencia_id = incidencia.id

                    # 5. Obtener adjuntos para esta incidencia
                    adjuntos_query = session.query(IncidenciaAdjunto).filter(
                        IncidenciaAdjunto.incidencia_id == incidencia_id
                    )

                    adjuntos = adjuntos_query.all()
                    adjuntos_list = []

                    for adj in adjuntos:
                        session.expunge(adj)
                        adjuntos_list.append(_to_dict(adj))

                    incidencia_dict['adjuntos'] = adjuntos_list
                    incidencias_list.append(incidencia_dict)

                trabajo_dict['incidencias'] = incidencias_list
                export_data.append(trabajo_dict)

            self.logger.info(f"Preparados {len(export_data)} registros de trabajo para exportar.")
            return export_data

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener datos para exportación: {e}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Error inesperado al obtener datos para exportación: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def get_all_ordenes_fabricacion(self) -> list[str]:
        """
        Obtiene todas las Órdenes de Fabricación únicas registradas en el sistema.

        Returns:
            Lista de códigos de Órdenes de Fabricación (sin duplicados, ordenados)
        """
        session = self.session_factory()
        try:
            # Consultar todas las órdenes de fabricación únicas, excluyendo valores NULL
            ordenes = session.query(TrabajoLog.orden_fabricacion).distinct().filter(
                TrabajoLog.orden_fabricacion.isnot(None),
                TrabajoLog.orden_fabricacion != ""
            ).order_by(TrabajoLog.orden_fabricacion).all()

            # Extraer los códigos de las tuplas y devolverlos como lista
            of_list = [of[0] for of in ordenes if of[0]]

            self.logger.debug(f"Encontradas {len(of_list)} Órdenes de Fabricación únicas.")
            return of_list

        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener órdenes de fabricación: {e}", exc_info=True)
            return []
        finally:
            session.close()

    # ========================================================================
    # HELPER METHODS FOR DTO MAPPING
    # ========================================================================

    def _map_to_trabajo_log_dto(self, trabajo: TrabajoLog) -> TrabajoLogDTO:
        """Map a TrabajoLog ORM object to TrabajoLogDTO."""
        if not trabajo:
            return None
            
        dto = TrabajoLogDTO(
            id=trabajo.id,
            qr_code=trabajo.qr_code,
            estado=trabajo.estado,
            tiempo_inicio=trabajo.tiempo_inicio,
            tiempo_fin=trabajo.tiempo_fin,
            duracion_segundos=trabajo.duracion_segundos,
            notas=trabajo.notas,
            trabajador_id=trabajo.trabajador_id,
            trabajador_nombre=trabajo.trabajador.nombre_completo if trabajo.trabajador else None,
            fabricacion_id=trabajo.fabricacion_id,
            fabricacion_codigo=trabajo.fabricacion.codigo if trabajo.fabricacion else None,
            fabricacion_descripcion=trabajo.fabricacion.descripcion if trabajo.fabricacion else None,
            producto_codigo=trabajo.producto_codigo,
            producto_descripcion=trabajo.producto.descripcion if trabajo.producto else None,
            orden_fabricacion=trabajo.orden_fabricacion
        )
        
        try:
            # Intento de acceso que podría fallar si la sesión está cerrada
            # o el objeto desprendido y la relación no se cargó con joinedload
            incidencias = getattr(trabajo, 'incidencias', [])
            dto.incidencias = [self._map_to_incidencia_log_dto(i) for i in incidencias]
        except Exception:
            dto.incidencias = []
            
        return dto

    def _map_to_incidencia_log_dto(self, incidencia: IncidenciaLog) -> IncidenciaLogDTO:
        """Map an IncidenciaLog ORM object to IncidenciaLogDTO."""
        if not incidencia:
            return None
            
        dto = IncidenciaLogDTO(
            id=incidencia.id,
            tipo_incidencia=incidencia.tipo_incidencia,
            descripcion=incidencia.descripcion,
            fecha_reporte=incidencia.fecha_reporte,
            estado=incidencia.estado,
            resolucion=incidencia.resolucion,
            fecha_resolucion=incidencia.fecha_resolucion,
            trabajador_nombre=incidencia.trabajador.nombre_completo if incidencia.trabajador else None
        )
        
        try:
            adjuntos = getattr(incidencia, 'adjuntos', [])
            dto.adjuntos = [self._map_to_incidencia_adjunto_dto(a) for a in adjuntos]
        except Exception:
            dto.adjuntos = []
            
        return dto

    def _map_to_incidencia_adjunto_dto(self, adjunto: IncidenciaAdjunto) -> IncidenciaAdjuntoDTO:
        """Map IncidenciaAdjunto ORM to DTO."""
        if not adjunto:
            return None
        return IncidenciaAdjuntoDTO(
            id=adjunto.id,
            ruta_archivo=adjunto.ruta_archivo,
            tipo_archivo=adjunto.tipo_mime # Mapping tipo_mime to tipo_archivo as expected by DTO
        )

    def _map_to_paso_trazabilidad_dto(self, paso: PasoTrazabilidad) -> PasoTrazabilidadDTO:
        """Map a PasoTrazabilidad ORM object to PasoTrazabilidadDTO."""
        if not paso:
            return None
            
        return PasoTrazabilidadDTO(
            id=paso.id,
            trabajo_log_id=paso.trabajo_log_id,
            paso_nombre=paso.paso_nombre,
            tipo_paso=paso.tipo_paso,
            estado_paso=paso.estado_paso,
            tiempo_inicio_paso=paso.tiempo_inicio_paso,
            tiempo_fin_paso=paso.tiempo_fin_paso,
            duracion_paso_segundos=paso.duracion_paso_segundos,
            maquina_id=paso.maquina_id,
            maquina_nombre=paso.maquina.nombre if paso.maquina else None,
            trabajador_nombre=paso.trabajador.nombre_completo if paso.trabajador else None
        )
