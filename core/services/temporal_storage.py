# temporal_storage.py
"""
Lógica o utilidades del núcleo (`temporal_storage`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import json
import logging
import os
from typing import Any, List, Dict, Tuple, Optional, cast
from datetime import datetime
from enum import Enum
from core.simulation.simulation_events import EventoDeSimulacion
import sqlite3
import threading


class RegistroTemporal:
    """
    [cite_start]Gestiona el almacenamiento incremental de eventos procesados en disco.
    CORREGIDO: Ahora es seguro para usar en múltiples hilos (thread-safe).
    """

    def __init__(self, db_path: str = ':memory:', buffer_size: int = 1000) -> None:
        """
        Prepara el almacenamiento de eventos. La conexión a la BD se creará
        en el hilo que la necesite.
        """
        self.db_path = db_path
        self.buffer_size = buffer_size
        self.buffer: list[dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        # Usamos un lock para proteger el acceso a la conexión entre hilos si fuera necesario
        self._lock = threading.Lock()
        # self.conn ya no se inicializa aquí, sino de forma "perezosa"
        self._local = threading.local()

    def _get_conn(self) -> sqlite3.Connection | None:
        """
        Crea y devuelve una conexión a la base de datos específica para el hilo actual.
        Si ya existe una para este hilo, la reutiliza.
        Tras close(), conn queda en None y se vuelve a crear al consultar.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            try:
                self.logger.info(
                    f"Creando nueva conexión a SQLite para el hilo {threading.get_ident()} en '{self.db_path}'...")
                self._local.conn = sqlite3.connect(self.db_path)
                cursor = self._local.conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS eventos_simulacion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        tipo_evento TEXT NOT NULL,
                        tarea_id TEXT,
                        datos_json TEXT NOT NULL
                    )
                ''')
                # Limpiamos la tabla solo si es la primera conexión que se establece
                if not hasattr(self, '_table_cleaned'):
                    cursor.execute('DELETE FROM eventos_simulacion')
                    self._table_cleaned = True

                self._local.conn.commit()
                if self.db_path != ':memory:':
                    self._local.conn.execute('PRAGMA journal_mode=WAL;')
                self.logger.info(
                    f"Conexión y tabla 'eventos_simulacion' preparadas para el hilo {threading.get_ident()}.")

            except sqlite3.Error as e:
                self.logger.critical(
                    f"No se pudo inicializar la base de datos de eventos para el hilo {threading.get_ident()}: {e}")
                self._local.conn = None

        return cast(sqlite3.Connection | None, self._local.conn)

    def _default_serializer(self, obj: Any) -> str:
        """Serializador JSON para objetos datetime y Enum."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return cast(str, obj.value)
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    def guardar_evento(self, evento: EventoDeSimulacion) -> None:
        """Añade un evento al buffer y lo vuelca a disco si está lleno."""
        with self._lock:
            self.buffer.append(vars(evento))
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer_to_disk()

    def _flush_buffer_to_disk(self) -> None:
        """Escribe el contenido del buffer en la base de datos SQLite y lo limpia."""
        conn = self._get_conn()
        if not self.buffer or not conn:
            return

        data_to_insert = []
        for evento_dict in self.buffer:
            datos_especificos = evento_dict.get('datos', {})
            datos_json = json.dumps(datos_especificos, default=self._default_serializer)
            timestamp_iso = self._default_serializer(evento_dict.get('timestamp'))
            tipo_evento = evento_dict.get('tipo_evento')
            tarea_id = datos_especificos.get('tarea_id')

            data_to_insert.append((timestamp_iso, tipo_evento, tarea_id, datos_json))

        try:
            with conn:  # Usar 'with' gestiona automáticamente el cursor, commit y rollback
                conn.executemany('''
                    INSERT INTO eventos_simulacion (timestamp, tipo_evento, tarea_id, datos_json)
                    VALUES (?, ?, ?, ?)
                ''', data_to_insert)

            self.logger.info(
                f"Vaciados {len(self.buffer)} eventos a la base de datos SQLite desde el hilo {threading.get_ident()}.")
            self.buffer.clear()
        except sqlite3.Error as e:
            self.logger.error(f"Error al vaciar el buffer de eventos a SQLite en el hilo {threading.get_ident()}: {e}")

    def close(self) -> None:
        """Asegura que el buffer se guarde y cierra la conexión del hilo actual."""
        with self._lock:
            self._flush_buffer_to_disk()

        conn = getattr(self._local, 'conn', None)
        if conn:
            try:
                conn.close()
                self._local.conn = None
                self.logger.info(
                    f"Conexión a la base de datos de eventos SQLite cerrada para el hilo {threading.get_ident()}.")
            except sqlite3.Error as e:
                self.logger.error(f"Error al cerrar la conexión SQLite en el hilo {threading.get_ident()}: {e}")

    def cleanup(self) -> None:
        """Cierra la conexión y elimina el archivo de BD del disco (solo si no es :memory:)."""
        self.close()
        if self.db_path and self.db_path != ':memory:':
            for path in (self.db_path, f"{self.db_path}-wal", f"{self.db_path}-shm"):
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                        self.logger.info(f"Archivo temporal de simulación eliminado: '{path}'")
                except OSError as e:
                    self.logger.warning(f"No se pudo eliminar el archivo temporal '{path}': {e}")

    def consultar_eventos(self, rango_temporal: tuple[datetime, datetime] | None = None, tipo_evento: str | None = None, tarea_id: str | None = None) -> list[dict[str, Any]]:
        """Lee eventos de la base de datos SQLite."""
        conn = self._get_conn()
        if not conn:
            self.logger.error("No hay conexión a la base de datos para consultar eventos.")
            return []

        # ✅ NUEVO: Asegurar que todos los eventos en buffer estén en disco
        with self._lock:
            if self.buffer:
                self.logger.info(f"💾 Vaciando {len(self.buffer)} eventos del buffer antes de consultar...")
                self._flush_buffer_to_disk()

        query = "SELECT timestamp, tipo_evento, datos_json FROM eventos_simulacion"
        conditions = []
        params = []

        if rango_temporal:
            start_time, end_time = rango_temporal
            conditions.append("timestamp >= ? AND timestamp <= ?")
            params.extend([start_time.isoformat(), end_time.isoformat()])
        if tipo_evento:
            conditions.append("tipo_evento = ?")
            params.append(tipo_evento)
        if tarea_id:
            conditions.append("tarea_id = ?")
            params.append(tarea_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp ASC"

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            eventos_reconstruidos = []
            for row in cursor.fetchall():
                timestamp_str, tipo, datos_str = row
                datos = json.loads(datos_str)
                evento = {
                    "timestamp": datetime.fromisoformat(timestamp_str),
                    "tipo_evento": tipo,
                    "datos": datos
                }
                eventos_reconstruidos.append(evento)
            return eventos_reconstruidos
        except sqlite3.Error as e:
            self.logger.error(f"Error al consultar eventos desde SQLite: {e}")
            return []