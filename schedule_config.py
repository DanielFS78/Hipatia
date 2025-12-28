from datetime import datetime, time
import json
import logging


class ScheduleConfig:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

        # Cargar configuración desde BD o usar valores por defecto
        self._load_from_database()

    def _load_from_database(self):
        """Carga la configuración desde la base de datos."""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT clave, valor FROM configuracion")
            config_data = dict(cursor.fetchall())

            # Usar valores correctos por defecto
            self.WORK_START_TIME = self._parse_time(
                config_data.get('work_start_time', '08:00')
            )
            self.WORK_END_TIME = self._parse_time(
                config_data.get('work_end_time', '17:00')
            )

            # Cargar configuración de descansos y festivos
            self.BREAKS = json.loads(
                config_data.get('breaks', '[{"start": "12:00", "end": "13:00"}]')
            )

            # Cargar festivos y convertir a objetos date para compatibilidad
            holidays_json = config_data.get('holidays', '[]')
            holidays_data = json.loads(holidays_json)
            self.HOLIDAYS = self._process_holidays(holidays_data)

        except Exception as e:
            # Valores por defecto si hay error
            self.WORK_START_TIME = time(8, 0)  # 8:00 AM
            self.WORK_END_TIME = time(17, 0)  # 5:00 PM
            self.BREAKS = [{"start": "12:00", "end": "13:00"}]
            self.HOLIDAYS = []
            self.logger.warning(f"Error cargando configuración, usando valores por defecto: {e}")

    def __getstate__(self):
        """
        Prepara el estado del objeto para ser 'pickled' (guardado).
        Excluimos los atributos que no se pueden guardar, como el logger y el gestor de BD.
        """
        state = self.__dict__.copy()
        # Eliminar los atributos no serializables
        if 'db_manager' in state:
            del state['db_manager']
        if 'logger' in state:
            del state['logger']
        return state

    def __setstate__(self, state):
        """
        Restaura el estado del objeto al ser 'unpickled' (cargado).
        """
        self.__dict__.update(state)
        # Los atributos no serializables se deben restaurar como None o reinicializarse
        # si fuera necesario, pero para el checkpoint no se usarán.
        self.db_manager = None
        self.logger = logging.getLogger(__name__)

    def reload_config(self, db_manager=None):
        """
        Recarga la configuración desde la base de datos.

        Args:
            db_manager: Gestor de base de datos (opcional, usa self.db_manager si no se proporciona)
        """
        if db_manager:
            self.db_manager = db_manager

        try:
            # Usar get_setting del db_manager via config_repo
            if hasattr(self.db_manager, 'config_repo'):
                self.WORK_START_TIME = datetime.strptime(
                    self.db_manager.config_repo.get_setting("work_start_time", "08:00"), "%H:%M"
                ).time()
                self.WORK_END_TIME = datetime.strptime(
                    self.db_manager.config_repo.get_setting("work_end_time", "17:00"), "%H:%M"
                ).time()
                self.BREAKS = json.loads(
                    self.db_manager.config_repo.get_setting("breaks", '[{"start": "12:00", "end": "13:00"}]')
                )

                # Procesar festivos correctamente
                holidays_json = self.db_manager.config_repo.get_setting("holidays", "[]")
                holidays_data = json.loads(holidays_json)
                self.HOLIDAYS = self._process_holidays(holidays_data)
            else:
                # Fallback al método original
                self._load_from_database()

        except Exception as e:
            self.logger.error(f"Error recargando configuración: {e}")
            # Mantener valores actuales en caso de error

    def _parse_time(self, time_str):
        """Convierte string de tiempo a objeto time."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return time(hours, minutes)
        except (ValueError, TypeError):  # <-- CORRECCIÓN: Captura excepciones específicas
            self.logger.warning(f"Formato de tiempo inválido: '{time_str}'. Usando valor por defecto.")
            return time(8, 0)  # Valor por defecto

    def _process_holidays(self, holidays_data):
        """
        Procesa los datos de festivos desde la base de datos y los convierte
        a objetos date para compatibilidad con el sistema de calendario.
        """
        processed_holidays = []

        for holiday in holidays_data:
            try:
                if isinstance(holiday, dict) and 'date' in holiday:
                    # Formato: {"date": "2025-12-25", "description": "..."}
                    date_str = holiday['date']
                elif isinstance(holiday, str):
                    # Formato: "2025-12-25"
                    date_str = holiday
                else:
                    continue  # Saltar formatos no válidos

                # Convertir string a objeto date
                from datetime import date
                year, month, day = map(int, date_str.split('-'))
                holiday_date = date(year, month, day)
                processed_holidays.append(holiday_date)

            except (ValueError, TypeError, KeyError) as e:
                self.logger.warning(f"Error procesando festivo {holiday}: {e}")
                continue

        return processed_holidays