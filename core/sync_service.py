# -*- coding: utf-8 -*-
"""
SyncService: Database Comparison and Merge for USB Sync
========================================================
Enables "sneakernet" synchronization by comparing local database with
an imported SQLite file and allowing selective merge of differences.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session

from database.models import (
    Producto, Trabajador, Maquina, Fabricacion, Pila
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

    # Tables to sync, in order of dependencies
    SYNCABLE_TABLES = [
        ('productos', Producto, 'codigo'),
        ('trabajadores', Trabajador, 'id'),
        ('maquinas', Maquina, 'id'),
        ('fabricaciones', Fabricacion, 'id'),
        ('pilas', Pila, 'id'),
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

    def apply_changes(self, comparison: DatabaseComparisonDTO) -> int:
        """
        Apply selected changes to the local database.
        
        Args:
            comparison: DatabaseComparisonDTO containing changes to apply
            
        Returns:
            Number of records successfully applied
        """
        self.logger.info(f"Applying sync changes for tables: {[t.table_name for t in comparison.tables]}")
        total_applied = 0
        local_session = self.local_session_factory()
        
        try:
            for table_diff in comparison.tables:
                table_name = table_diff.table_name
                records = table_diff.differences
                
                # Find the model class and primary key
                model_info = next(
                    (t for t in self.SYNCABLE_TABLES if t[0] == table_name), 
                    None
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
