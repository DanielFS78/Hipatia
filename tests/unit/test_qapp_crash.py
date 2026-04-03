"""
Nombre del Módulo: tests.test_qapp_crash
Descripción: Prueba de humo para verificar la creación de QApplication.
Asegura que el entorno de GUI (offscreen o real) esté correctamente configurado.

Este test implementa el estándar de Strict Testing de Hipatia.
"""
import sys
import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

pytestmark = pytest.mark.unit


def test_create_app(qapp):
    """ Verifica la inicialización de QApplication sin crashes usando el fixture. """
    print("\n--- TEST: Creating QApplication ---")
    
    try:
        assert qapp is not None
        assert QApplication.instance() is not None
        print("QApplication exists and is healthy:", QApplication.instance())
    except Exception as e:
        print("Exception during creation:", e)
        raise
    print("--- TEST COMPLETE ---")
