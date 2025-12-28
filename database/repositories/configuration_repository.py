# database/repositories/configuration_repository.py
"""
Repositorio para la gestión de configuración de la aplicación.
"""
from typing import Optional, Any, List
from datetime import date
import json

from .base import BaseRepository
from ..models import Configuration


class ConfigurationRepository(BaseRepository):
    """
    Repositorio para gestión de configuración de la aplicación.
    Almacena pares clave-valor de configuración.
    """

    def _get_default_error_value(self):
        """Valor por defecto en caso de error."""
        return None

    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Obtiene un valor de configuración por su clave.

        Args:
            key: Clave de configuración
            default_value: Valor por defecto si no existe

        Returns:
            Valor de configuración o default_value
        """

        def _operation(session):
            config = session.query(Configuration).filter_by(clave=key).first()
            return config.valor if config else default_value

        return self.safe_execute(_operation) or default_value

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Guarda o actualiza un valor de configuración.

        Args:
            key: Clave de configuración
            value: Valor a guardar (se convertirá a string)

        Returns:
            True si se guardó correctamente, False en caso contrario
        """

        def _operation(session):
            # Buscar si existe
            config = session.query(Configuration).filter_by(clave=key).first()

            if config:
                # Actualizar
                config.valor = str(value)
            else:
                # Crear nuevo
                config = Configuration(clave=key, valor=str(value))
                session.add(config)

            self.logger.info(f"Configuración '{key}' actualizada.")
            return True

        return self.safe_execute(_operation) or False

    def get_holidays(self) -> List[date]:
        """
        Obtiene la lista de días festivos.

        Returns:
            Lista de objetos date con los festivos
        """
        holidays_json = self.get_setting('holidays', '[]')

        try:
            holidays_data = json.loads(holidays_json)
        except json.JSONDecodeError:
            self.logger.error(f"Error decodificando JSON de festivos: {holidays_json}")
            return []

        result = []
        for h in holidays_data:
            try:
                if isinstance(h, dict):
                    date_str = h.get('date')
                else:
                    date_str = h

                if date_str:
                    year, month, day = map(int, date_str.split('-'))
                    result.append(date(year, month, day))
            except (ValueError, AttributeError) as e:
                self.logger.warning(f"Error procesando festivo {h}: {e}")
                continue

        return result

    def add_holiday(self, holiday_date: date, description: str = "") -> bool:
        """
        Añade un día festivo.

        Args:
            holiday_date: Fecha del festivo
            description: Descripción opcional del festivo

        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        # Obtener lista actual
        holidays_json = self.get_setting('holidays', '[]')

        try:
            holidays_list = json.loads(holidays_json)
        except json.JSONDecodeError:
            holidays_list = []

        # Verificar si ya existe
        date_str = holiday_date.strftime('%Y-%m-%d')
        for h in holidays_list:
            existing_date = h.get('date') if isinstance(h, dict) else h
            if existing_date == date_str:
                self.logger.info(f"Festivo {date_str} ya existe.")
                return True  # Ya existe, no es error

        # Añadir nuevo festivo
        new_holiday = {
            'date': date_str,
            'description': description
        }
        holidays_list.append(new_holiday)

        # Guardar
        return self.set_setting('holidays', json.dumps(holidays_list))

    def remove_holiday(self, holiday_date: date) -> bool:
        """
        Elimina un día festivo.

        Args:
            holiday_date: Fecha del festivo a eliminar

        Returns:
            True si se eliminó correctamente
        """
        # Obtener lista actual
        holidays_json = self.get_setting('holidays', '[]')

        try:
            holidays_list = json.loads(holidays_json)
        except json.JSONDecodeError:
            return False

        # Filtrar el festivo a eliminar
        date_str = holiday_date.strftime('%Y-%m-%d')
        updated_holidays = []
        removed = False

        for h in holidays_list:
            existing_date = h.get('date') if isinstance(h, dict) else h
            if existing_date != date_str:
                updated_holidays.append(h)
            else:
                removed = True

        if removed:
            self.logger.info(f"Festivo {date_str} eliminado.")
            return self.set_setting('holidays', json.dumps(updated_holidays))

        # No se encontró, pero no es error
        return True