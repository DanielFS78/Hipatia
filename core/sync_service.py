# -*- coding: utf-8 -*-
"""
SyncService: Database Comparison and Merge for USB Sync
========================================================
Enables "sneakernet" synchronization by comparing local database with
an imported SQLite file and allowing selective merge of differences.
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
    Service for comparing and synchronizing two SQLAlchemy databases.
    Designed for USB-based sync workflow between disconnected machines.
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
        Initialize SyncService with the local database session factory.
        
        Args:
            local_session_factory: SQLAlchemy sessionmaker for local DB
        """
        self.logger = logging.getLogger("SyncService")
        self.local_session_factory = local_session_factory

    def compare_databases(self, foreign_db_path: str) -> DatabaseComparisonDTO:
        """
        Compare local database with a foreign SQLite database file.
        
        Args:
            foreign_db_path: Path to the foreign .db file (from USB)
            
        Returns:
            DatabaseComparisonDTO containing differences per table.
        """
        self.logger.info(f"Comparing with foreign DB: {foreign_db_path}")
        tables_diffs = []
        
        # Connect to foreign SQLite database
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
        Compare a single table between local and foreign databases.
        
        Args:
            local_session: Local database session
            foreign_session: Foreign database session
            model_class: SQLAlchemy model class
            primary_key: Name of the primary key column
            
        Returns:
            List of SyncRecordDTOs that differ (new or updated in foreign DB).
            Each DTO contains a SyncRecordPayloadDTO with the fields.
        """
        differences = []
        
        # Get all records from both databases
        local_records = {
            getattr(r, primary_key): r 
            for r in local_session.query(model_class).all()
        }
        foreign_records = foreign_session.query(model_class).all()
        
        # Get column names for comparison (exclude relationships)
        mapper = inspect(model_class)
        columns = [c.key for c in mapper.columns]
        
        for foreign_record in foreign_records:
            pk_value = getattr(foreign_record, primary_key)
            local_record = local_records.get(pk_value)
            
            # Convert to dict for comparison and display
            record_dict = {col: getattr(foreign_record, col) for col in columns}
            
            if local_record is None:
                # New record in foreign DB
                differences.append(SyncRecordDTO(action='new', data=SyncRecordPayloadDTO(fields=record_dict)))
            else:
                # Check if modified
                is_modified = False
                for col in columns:
                    local_val = getattr(local_record, col)
                    foreign_val = getattr(foreign_record, col)
                    
                    # Handle datetime comparison
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
        """Filas del enlace presentes en extranjero y ausentes en local (p. ej. BOM producto–material)."""
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
        """Orden según FKs (p. ej. materiales antes que producto_material_link) aunque el diálogo devuelva otro orden."""
        order: dict[str, int] = {}
        for idx, spec in enumerate(self.SYNCABLE_TABLES):
            order[spec[0]] = idx
        offset = len(order)
        for j, spec in enumerate(self.ASSOCIATION_TABLES):
            order[spec[0]] = offset + j
        return sorted(tables, key=lambda t: order.get(t.table_name, 9999))

    def apply_changes(self, comparison: DatabaseComparisonDTO) -> int:
        """
        Apply selected changes to the local database.
        
        Args:
            comparison: DatabaseComparisonDTO containing changes to apply
            
        Returns:
            Number of records successfully applied
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
        Apply a single record to the local database.
        
        Args:
            session: Local database session
            model_class: SQLAlchemy model class
            primary_key: Name of primary key column
            record_dto: SyncRecordDTO
            
        Returns:
            True if successfully applied.
        """
        sync_action = record_dto.action
        record_data = record_dto.data.fields
        
        # Remove internal keys if any (prefixed with _)
        clean_dict = {k: v for k, v in record_data.items() if not k.startswith('_')}
        
        pk_value = clean_dict.get(primary_key)
        
        if sync_action == 'new':
            # Insert new record
            new_record = model_class(**clean_dict)
            session.add(new_record)
            self.logger.debug(f"Inserted new {model_class.__name__}: {pk_value}")
        else:
            # Update existing record
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
        """Inserta una fila de tabla de enlace (solo acción 'new')."""
        if record_dto.action != 'new':
            return False
        clean_dict = {k: v for k, v in record_dto.data.fields.items() if not k.startswith('_')}
        session.execute(insert(table).values(**clean_dict))
        self.logger.debug("Inserted association row in %s: %s", table.name, clean_dict)
        return True
