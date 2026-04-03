"""
Nombre del Módulo: tests.db
Descripción: Paquete de utilidades de base de datos para pruebas.
Contiene configuraciones y fixtures específicas para el testing del motor de persistencia
en el proyecto Hipatia.
"""
import pytest

# Marcador global para configuración de entorno de pruebas de base de datos
pytestmark = pytest.mark.setup
