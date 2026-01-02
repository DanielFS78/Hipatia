# Análisis de `tracking_repository.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/repositories/tracking_repository.py`


## Importaciones
- `base.BaseRepository`
- `core.tracking_dtos.FabricacionAsignadaDTO`
- `core.tracking_dtos.IncidenciaAdjuntoDTO`
- `core.tracking_dtos.IncidenciaLogDTO`
- `core.tracking_dtos.PasoTrazabilidadDTO`
- `core.tracking_dtos.TrabajoLogDTO`
- `database.models.Fabricacion`
- `database.models.IncidenciaAdjunto`
- `database.models.IncidenciaLog`
- `database.models.Maquina`
- `database.models.PasoTrazabilidad`
- `database.models.Producto`
- `database.models.Trabajador`
- `database.models.TrabajoLog`
- `datetime.datetime`
- `datetime.timedelta`
- `datetime.timezone`
- `logging`
- `models.Fabricacion`
- `models.fabricacion_productos`
- `models.trabajador_fabricacion_link`
- `sqlalchemy.and_`
- `sqlalchemy.desc`
- `sqlalchemy.exc.IntegrityError`
- `sqlalchemy.exc.SQLAlchemyError`
- `sqlalchemy.func`
- `sqlalchemy.or_`
- `sqlalchemy.orm.Session`
- `sqlalchemy.orm.aliased`
- `sqlalchemy.orm.joinedload`
- `typing.Any`
- `typing.Dict`
- `typing.List`
- `typing.Optional`
- `typing.Tuple`

## Clases

### Clase `TrackingRepository`
- **Línea:** 38
- **Hereda de:** `BaseRepository`
- **Docstring:** Repositorio para operaciones de tracking y trazabilidad.

Este repositorio maneja toda la lÃ³gica de negocio relacionada con:
- Inicio y finalizaciÃ³n de trabajos
- Registro de incidencias con fotos
-...

#### Métodos
- `__init__`(self, session_factory)
  - _Inicializa el repositorio._
- `get_fabricaciones_por_trabajador`(self, trabajador_id: int)
  - _Obtiene todas las fabricaciones asignadas a un trabajador específicamente,_
- `actualizar_estado_asignacion`(self, trabajador_id: int, fabricacion_id: int, nuevo_estado: str)
  - _Actualiza el estado de una asignaciÃ³n de fabricaciÃ³n a un trabajador._
- `obtener_o_crear_trabajo_log_por_qr`(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str, orden_fabricacion: Optional[str], notas: Optional[str])
  - _Obtiene un TrabajoLog por QR si existe. Si no, lo crea._
- `iniciar_trabajo`(self, qr_code: str, trabajador_id: int, fabricacion_id: int, producto_codigo: str)
  - _Inicia un nuevo trabajo (Wrapper para obtener_o_crear_trabajo_log_por_qr)._
- `finalizar_trabajo_log`(self, trabajo_log_id: int, notas_finalizacion: Optional[str])
  - _Finaliza el TrabajoLog principal (el "pasaporte")._
- `pausar_trabajo`(self, qr_code: str, motivo: str)
  - _Pausa un trabajo en proceso._
- `reanudar_trabajo`(self, qr_code: str)
  - _Reanuda un trabajo pausado._
- `obtener_trabajo_por_qr`(self, qr_code: str)
  - _Obtiene un trabajo por su código QR._
- `obtener_trabajo_por_id`(self, trabajo_log_id: int)
  - _Obtiene un trabajo por su ID._
- `get_paso_activo_por_trabajador`(self, trabajador_id: int)
  - _Busca si un trabajador tiene un paso de trazabilidad en estado 'en_proceso'._
- `get_ultimo_paso_para_qr`(self, trabajo_log_id: int)
  - _Obtiene el último paso (más reciente) registrado para un TrabajoLog (QR)._
- `iniciar_nuevo_paso`(self, trabajo_log_id: int, trabajador_id: int, paso_nombre: str, tipo_paso: str, maquina_id: Optional[int])
  - _Crea un nuevo registro de PasoTrazabilidad (un "sello")._
- `finalizar_paso`(self, paso_id: int)
  - _Finaliza un PasoTrazabilidad, calculando su duración._
- `obtener_trabajos_activos`(self, trabajador_id: Optional[int], fabricacion_id: Optional[int])
  - _Obtiene todos los trabajos activos (en_proceso o pausados)._
- `registrar_incidencia`(self, trabajo_log_id: int, trabajador_id: int, tipo_incidencia: str, descripcion: str, rutas_fotos: Optional[List[str]])
  - _Registra una nueva incidencia._
- `_crear_adjunto`(self, session: Session, incidencia_id: int, ruta_archivo: str)
  - _Crea un adjunto fotogrÃ¡fico (uso interno)._
- `añadir_foto_a_incidencia`(self, incidencia_id: int, ruta_foto: str, descripcion: Optional[str])
  - _Añade una foto a una incidencia existente._
- `resolver_incidencia`(self, incidencia_id: int, resolucion: str)
  - _Marca una incidencia como resuelta._
- `obtener_incidencias_abiertas`(self, fabricacion_id: Optional[int])
  - _Obtiene todas las incidencias abiertas._
- `asignar_trabajador_a_fabricacion`(self, trabajador_id: int, fabricacion_id: int)
  - _Asigna un trabajador a una fabricaciÃ³n._
- `desasignar_trabajador_de_fabricacion`(self, trabajador_id: int, fabricacion_id: int)
  - _Desasigna un trabajador de una fabricaciÃ³n._
- `obtener_trabajadores_de_fabricacion`(self, fabricacion_id: int)
  - _Obtiene todos los trabajadores asignados a una fabricaciÃ³n._
- `obtener_estadisticas_trabajador`(self, trabajador_id: int, fecha_inicio: Optional[datetime], fecha_fin: Optional[datetime])
  - _Obtiene estadÃ­sticas de un trabajador._
- `obtener_estadisticas_fabricacion`(self, fabricacion_id: int)
  - _Obtiene estadÃ­sticas de una fabricaciÃ³n._
- `get_trabajo_logs_por_trabajador`(self, trabajador_id: int)
  - _Obtiene todos los registros de trabajo (fichajes) de un trabajador,_
- `upsert_trabajo_log_from_dict`(self, data: Dict[str, Any])
  - _Inserta o actualiza un TrabajoLog desde un diccionario (JSON)._
- `get_data_for_export`(self, trabajador_id: int, since_date: datetime)
  - _Recopila todos los datos de un trabajador creados desde una fecha específica._
- `get_all_ordenes_fabricacion`(self)
  - _Obtiene todas las Órdenes de Fabricación únicas registradas en el sistema._
- `_map_to_trabajo_log_dto`(self, trabajo: TrabajoLog)
  - _Map a TrabajoLog ORM object to TrabajoLogDTO._
- `_map_to_incidencia_log_dto`(self, incidencia: IncidenciaLog)
  - _Map an IncidenciaLog ORM object to IncidenciaLogDTO._
- `_map_to_incidencia_adjunto_dto`(self, adjunto: IncidenciaAdjunto)
  - _Map IncidenciaAdjunto ORM to DTO._
- `_map_to_paso_trazabilidad_dto`(self, paso: PasoTrazabilidad)
  - _Map a PasoTrazabilidad ORM object to PasoTrazabilidadDTO._