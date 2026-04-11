# -*- coding: utf-8 -*-
"""
Nombre del Módulo: sync_service
Descripción: Comparación y fusión selectiva entre la base SQLite local y un fichero SQLite
             externo (``sneakernet`` / USB / copia exportada). Construye ``DatabaseComparisonDTO``
             para la UI y aplica cambios elegidos respetando orden de claves foráneas e incluyendo
             tablas de asociación (BOM producto–material).
"""

import logging
from typing import Any, Callable, List, Tuple

from datetime import datetime

from sqlalchemy import create_engine, inspect, insert, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.schema import Table

from database.models import (
    Fabricacion,
    Maquina,
    Material,
    Pila,
    ProcesoMecanico,
    Producto,
    Subfabricacion,
    Trabajador,
    producto_material_link,
)
from core.dtos import (
    SyncRecordDTO,
    SyncRecordPayloadDTO,
    SyncTableDifferencesDTO,
    DatabaseComparisonDTO
)


class SyncService:
    """
    Servicio que compara y fusiona registros entre la sesión local y una segunda base SQLite.

    La lista ``SYNCABLE_TABLES`` define el orden de comparación y de aplicación (productos y máquinas
    antes que subfabricaciones y procesos mecánicos; materiales antes que ``producto_material_link``).
    Las tablas en ``ASSOCIATION_TABLES`` solo generan filas ``new`` cuando el vínculo existe en
    extranjero y no en local.
    """

    # Tablas ORM a sincronizar (orden respetando FKs: producto/maquina antes de subfabricación, etc.).
    SYNCABLE_TABLES: List[Tuple[str, Any, str]] = [
        ('productos', Producto, 'codigo'),
        ('trabajadores', Trabajador, 'id'),
        ('maquinas', Maquina, 'id'),
        ('materiales', Material, 'id'),
        ('subfabricaciones', Subfabricacion, 'id'),
        ('procesos_mecanicos', ProcesoMecanico, 'id'),
        ('fabricaciones', Fabricacion, 'id'),
        ('pilas', Pila, 'id'),
    ]

    # Tablas de asociación sin modelo ORM propio: solo filas nuevas en extranjero (presencia del vínculo).
    ASSOCIATION_TABLES: List[Tuple[str, Table, Tuple[str, ...]]] = [
        ('producto_material_link', producto_material_link, ('producto_codigo', 'material_id')),
    ]

    def __init__(self, local_session_factory: Callable[[], Session]) -> None:
        """
        Args:
            local_session_factory: Fábrica que devuelve sesiones SQLAlchemy sobre la BD local
                (típicamente ``sessionmaker`` ligado al motor de la app).
        """
        self.logger = logging.getLogger("SyncService")
        self.local_session_factory = local_session_factory

    def compare_databases(self, foreign_db_path: str) -> DatabaseComparisonDTO:
        """
        Compara todas las tablas configuradas entre local y el fichero SQLite externo.

        Args:
            foreign_db_path: Ruta absoluta al ``.db`` ya resuelto (no comprimido).

        Returns:
            DTO con una entrada por tabla que tenga diferencias (``new`` o ``updated`` en extranjero).
        """
        self.logger.info(f"Comparing with foreign DB: {foreign_db_path}")
        tables_diffs = []
        
        foreign_engine = create_engine(f"sqlite:///{foreign_db_path}")
        ForeignSession = sessionmaker(bind=foreign_engine)
        foreign_session = ForeignSession()
        local_session = self.local_session_factory()
        
        try:
            for table_name, model_class, primary_key in self.SYNCABLE_TABLES:
                diffs = self._compare_table(
                    local_session, foreign_session, model_class, primary_key
                )
                if diffs:
                    tables_diffs.append(SyncTableDifferencesDTO(
                        table_name=table_name,
                        differences=diffs
                    ))
                    self.logger.info(f"Found {len(diffs)} differences in {table_name}")

            for table_name, assoc_table, key_columns in self.ASSOCIATION_TABLES:
                diffs = self._compare_association_table(
                    local_session, foreign_session, assoc_table, key_columns
                )
                if diffs:
                    tables_diffs.append(SyncTableDifferencesDTO(
                        table_name=table_name,
                        differences=diffs
                    ))
                    self.logger.info(f"Found {len(diffs)} differences in {table_name}")

        except Exception as e:
            self.logger.error(f"Error comparing databases: {e}", exc_info=True)
            raise
        finally:
            foreign_session.close()
            local_session.close()
            foreign_engine.dispose()
            
        return DatabaseComparisonDTO(tables=tables_diffs)

    def _compare_table(
        self, 
        local_session: Session, 
        foreign_session: Session,
        model_class: Any,
        primary_key: str
    ) -> List[SyncRecordDTO]:
        """
        Compara una tabla ORM columna a columna (sin relaciones cargadas).

        Args:
            local_session: Sesión sobre la BD local.
            foreign_session: Sesión sobre la BD extranjera.
            model_class: Modelo declarativo SQLAlchemy.
            primary_key: Nombre del atributo que actúa como clave primaria.

        Returns:
            Lista de ``SyncRecordDTO`` con ``action`` ``new`` o ``updated`` respecto a local.
            Los ``datetime`` se consideran distintos si difieren en más de un segundo.
        """
        differences = []
        
        local_records = {
            getattr(r, primary_key): r 
            for r in local_session.query(model_class).all()
        }
        foreign_records = foreign_session.query(model_class).all()
        
        mapper = inspect(model_class)
        columns = [c.key for c in mapper.columns]
        
        for foreign_record in foreign_records:
            pk_value = getattr(foreign_record, primary_key)
            local_record = local_records.get(pk_value)
            
            record_dict = {col: getattr(foreign_record, col) for col in columns}
            
            if local_record is None:
                differences.append(SyncRecordDTO(action='new', data=SyncRecordPayloadDTO(fields=record_dict)))
            else:
                is_modified = False
                for col in columns:
                    local_val = getattr(local_record, col)
                    foreign_val = getattr(foreign_record, col)
                    
                    if isinstance(local_val, datetime) and isinstance(foreign_val, datetime):
                        if abs((local_val - foreign_val).total_seconds()) > 1:
                            is_modified = True
                            break
                    elif local_val != foreign_val:
                        is_modified = True
                        break
                        
                if is_modified:
                    differences.append(SyncRecordDTO(action='updated', data=SyncRecordPayloadDTO(fields=record_dict)))
                    
        return differences

    def _association_row_set(
        self, session: Session, table: Table, key_columns: Tuple[str, ...]
    ) -> set[tuple[Any, ...]]:
        """
        Lee todas las filas de una tabla de enlace como conjunto de tuplas de claves.

        Args:
            session: Sesión activa.
            table: Objeto ``Table`` SQLAlchemy (p. ej. ``producto_material_link``).
            key_columns: Columnas que forman la identidad de la fila.

        Returns:
            Conjunto de tuplas hashables para comparación de presencia.
        """
        stmt = select(*(table.c[col] for col in key_columns))
        rows = session.execute(stmt).all()
        return {tuple(row) for row in rows}

    def _compare_association_table(
        self,
        local_session: Session,
        foreign_session: Session,
        table: Table,
        key_columns: Tuple[str, ...],
    ) -> List[SyncRecordDTO]:
        """
        Detecta vínculos que existen en extranjero y faltan en local (solo inserciones).

        Args:
            local_session: Sesión local.
            foreign_session: Sesión extranjera.
            table: Tabla de asociación.
            key_columns: Columnas de la clave compuesta.

        Returns:
            Lista de ``SyncRecordDTO`` con ``action='new'`` por cada fila a insertar.
        """
        local_set = self._association_row_set(local_session, table, key_columns)
        foreign_set = self._association_row_set(foreign_session, table, key_columns)
        differences: List[SyncRecordDTO] = []
        for row in foreign_set:
            if row not in local_set:
                fields = {k: v for k, v in zip(key_columns, row)}
                differences.append(
                    SyncRecordDTO(action='new', data=SyncRecordPayloadDTO(fields=fields))
                )
        return differences

    def _sort_table_diffs_for_apply(
        self, tables: List[SyncTableDifferencesDTO]
    ) -> List[SyncTableDifferencesDTO]:
        """
        Reordena los bloques seleccionados por el usuario según ``SYNCABLE_TABLES`` + ``ASSOCIATION_TABLES``.

        Args:
            tables: Fragmentos del DTO tal como devuelve el diálogo (orden de pestañas).

        Returns:
            Misma información ordenada para minimizar errores de FK al aplicar.
        """
        order: dict[str, int] = {}
        for idx, spec in enumerate(self.SYNCABLE_TABLES):
            order[spec[0]] = idx
        offset = len(order)
        for j, assoc_spec in enumerate(self.ASSOCIATION_TABLES):
            order[assoc_spec[0]] = offset + j
        return sorted(tables, key=lambda t: order.get(t.table_name, 9999))

    def apply_changes(self, comparison: DatabaseComparisonDTO) -> int:
        """
        Aplica en la BD local los registros incluidos en ``comparison`` (una transacción con commit).

        Args:
            comparison: Subconjunto devuelto por ``SyncDialog.get_selected_changes``.

        Returns:
            Número de filas aplicadas con éxito (ORM + asociaciones).
        """
        sorted_tables = self._sort_table_diffs_for_apply(list(comparison.tables))
        self.logger.info(f"Applying sync changes for tables: {[t.table_name for t in sorted_tables]}")
        total_applied = 0
        local_session = self.local_session_factory()
        
        try:
            for table_diff in sorted_tables:
                table_name = table_diff.table_name
                records = table_diff.differences

                assoc_info = next(
                    (t for t in self.ASSOCIATION_TABLES if t[0] == table_name),
                    None,
                )
                if assoc_info:
                    _, assoc_table, _key_cols = assoc_info
                    for record_dto in records:
                        try:
                            if self._apply_association_row(local_session, assoc_table, record_dto):
                                total_applied += 1
                        except Exception as e:
                            self.logger.error(f"Error applying association row: {e}")
                    continue

                model_info = next(
                    (t for t in self.SYNCABLE_TABLES if t[0] == table_name),
                    None,
                )
                if not model_info:
                    self.logger.warning(f"Unknown table: {table_name}, skipping")
                    continue

                _, model_class, primary_key = model_info

                for record_dto in records:
                    try:
                        applied = self._apply_single_record(
                            local_session, model_class, primary_key, record_dto
                        )
                        if applied:
                            total_applied += 1
                    except Exception as e:
                        self.logger.error(f"Error applying record: {e}")
                        
            local_session.commit()
            self.logger.info(f"Successfully applied {total_applied} changes")
            
        except Exception as e:
            local_session.rollback()
            self.logger.error(f"Error during sync apply: {e}", exc_info=True)
            raise
        finally:
            local_session.close()
            
        return total_applied

    def _apply_single_record(
        self,
        session: Session,
        model_class: Any,
        primary_key: str,
        record_dto: SyncRecordDTO
    ) -> bool:
        """
        Inserta o actualiza una fila ORM según ``record_dto.action``.

        Args:
            session: Sesión local (sin commit aún).
            model_class: Modelo destino.
            primary_key: Nombre del campo PK en el modelo.
            record_dto: Carga útil con campos serializables.

        Returns:
            False si ``updated`` y no existe la fila local; True en caso contrario.
        """
        sync_action = record_dto.action
        record_data = record_dto.data.fields
        
        clean_dict = {k: v for k, v in record_data.items() if not k.startswith('_')}
        
        pk_value = clean_dict.get(primary_key)
        
        if sync_action == 'new':
            new_record = model_class(**clean_dict)
            session.add(new_record)
            self.logger.debug(f"Inserted new {model_class.__name__}: {pk_value}")
        else:
            existing = session.query(model_class).filter(
                getattr(model_class, primary_key) == pk_value
            ).first()
            
            if existing:
                for key, value in clean_dict.items():
                    setattr(existing, key, value)
                self.logger.debug(f"Updated {model_class.__name__}: {pk_value}")
            else:
                self.logger.warning(f"Record not found for update: {pk_value}")
                return False
                
        return True

    def _apply_association_row(
        self,
        session: Session,
        table: Table,
        record_dto: SyncRecordDTO,
    ) -> bool:
        """
        Ejecuta ``INSERT`` en una tabla ``Table`` de metadatos compartidos.

        Args:
            session: Sesión local.
            table: Tabla de enlace.
            record_dto: Debe traer ``action=='new'`` y campos alineados con las columnas.

        Returns:
            True si se insertó; False si la acción no es de alta.
        """
        if record_dto.action != 'new':
            return False
        clean_dict = {k: v for k, v in record_dto.data.fields.items() if not k.startswith('_')}
        session.execute(insert(table).values(**clean_dict))
        self.logger.debug("Inserted association row in %s: %s", table.name, clean_dict)
        return True
