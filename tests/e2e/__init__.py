"""
Nombre del Módulo: tests.e2e
Descripción: Paquete de pruebas de extremo a extremo (E2E) para el proyecto Hipatia.
Este paquete contiene flujos de prueba complejos que simulan la interacción
del usuario con la aplicación completa en un entorno controlado.
"""
import pytest

# Marcador global para pruebas E2E e infraestructura
pytestmark = pytest.mark.e2e
# pytestmark = pytest.mark.setup
