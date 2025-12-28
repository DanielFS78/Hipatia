# repositories/base.py
"""
Repositorio base que proporciona funcionalidades comunes para todos los repositorios.
"""

import logging
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class BaseRepository:
    """
    Clase base para todos los repositorios.
    Proporciona funcionalidades comunes como manejo de sesiones, logging y operaciones CRUD básicas.
    """

    def __init__(self, session_factory):
        """
        Inicializa el repositorio base.

        Args:
            session_factory: Factory de sesiones de SQLAlchemy (SessionLocal)
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(f"EvolucionTiemposApp.{self.__class__.__name__}")

    def get_session(self) -> Optional[Session]:
        """
        Obtiene una nueva sesión de SQLAlchemy.

        Returns:
            Session de SQLAlchemy o None si hay error
        """
        try:
            return self.session_factory()
        except Exception as e:
            self.logger.error(f"Error al crear sesión: {e}")
            return None

    def safe_execute(self, operation, *args, **kwargs):
        """
        Ejecuta una operación de base de datos de forma segura con manejo de errores.
        VERSIÓN MEJORADA con mejor logging para debugging.
        """
        session = self.get_session()
        if not session:
            self.logger.error("No se pudo obtener sesión de SQLAlchemy")
            return self._get_default_error_value()

        try:
            self.logger.debug(f"Ejecutando operación: {operation.__name__}")

            # Ejecutar la operación
            result = operation(session, *args, **kwargs)

            # Commit inmediato para asegurar persistencia
            session.commit()
            self.logger.debug(f"Operación {operation.__name__} - COMMIT exitoso")

            # Expulsar objetos de la sesión para evitar problemas de referencia
            if result:
                if isinstance(result, list):
                    for item in result:
                        if hasattr(item, '_sa_instance_state'):
                            session.expunge(item)
                elif hasattr(result, '_sa_instance_state'):
                    session.expunge(result)

            self.logger.debug(f"Operación {operation.__name__} completada exitosamente")
            return result

        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error de SQLAlchemy en {operation.__name__}: {e}")
            return self._get_default_error_value()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error inesperado en {operation.__name__}: {e}")
            return self._get_default_error_value()
        finally:
            session.close()

    def _get_default_error_value(self):
        """
        Valor por defecto a devolver en caso de error.
        Cada repositorio puede sobrescribir este método.
        """
        return None