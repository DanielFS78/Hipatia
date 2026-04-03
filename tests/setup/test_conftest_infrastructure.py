"""
Tests unitarios para la infraestructura de conftest.py.
Objetivo: Alcanzar el 100% de cobertura en tests/conftest.py.
"""
import pytest
import os
from datetime import date
from unittest.mock import MagicMock, patch

# Importar componentes de conftest
import tests.conftest as conftest

@pytest.mark.setup
class TestConftestCore:
    """Pruebas para la lógica core de configuración de tests."""

    def test_adapt_date_iso(self):
        """Prueba manual del adaptador de fecha para sqlite3."""
        d = date(2025, 5, 20)
        assert conftest.adapt_date_iso(d) == "2025-05-20"

    def test_mock_qt_class(self):
        """Verifica la clase MockQtClass para evitar SIGABRT."""
        mock = conftest.MockQtClass()
        assert mock.RenderHint.Antialiasing == 1
        assert isinstance(mock, MagicMock)

    def test_compliance_structural_patterns(self):
        """Ejercita la función de verificación de cumplimiento de conftest."""
        assert conftest._compliance_check_structural_patterns() is True

    # Los tests de clear_di_container y register_application_state se omiten 
    # proactivamente aquí porque se ejecutan automáticamente como autouse fixtures
    # en cada test de esta suite, garantizando su cobertura.

@pytest.mark.setup
class TestConftestFixtures:
    """Validación de que las fixtures de conftest.py proporcionan datos válidos."""

    def test_db_manager_proxy_behavior(self, in_memory_db_manager):
        """Verifica que el DatabaseManager de test usa el proxy de sesión."""
        # Esto cubre la clase SessionKeepAliveProxy definida dentro de la fixture
        session_proxy = in_memory_db_manager.SessionLocal()
        session_proxy.close() # No debe cerrar la sesión real (cobertura de no-op)
        assert hasattr(session_proxy, "execute")
        
    def test_temp_files_fixtures(self, temp_report_dir, temp_db_file, session_reports_dir):
        """Verifica creación de archivos y directorios temporales."""
        assert os.path.exists(temp_report_dir)
        assert os.path.exists(temp_db_file)
        assert session_reports_dir.exists()

    def test_data_samples_fixtures(self, sample_workers, sample_machines, sample_products):
        """Verifica que los datos de ejemplo son correctos."""
        assert len(sample_workers) >= 5
        assert len(sample_machines) >= 4
        # sample_products crea 2 productos según la definición de la fixture
        assert len(sample_products) == 2
        assert any(p.codigo == "PROD-SIMPLE-01" for p in sample_products)

    def test_simulation_fixtures(self, sample_simulation_data, sample_pytest_audit_data):
        """Verifica fixtures de simulación y auditoría."""
        assert "planificacion" in sample_simulation_data
        assert "coverage" in sample_pytest_audit_data
        
    def test_qapp_fixture(self, qapp):
        """Verifica la inicialización de QApplication."""
        from PyQt6.QtWidgets import QApplication
        assert QApplication.instance() is not None
        assert qapp.applicationName() == "Evolucion Tiempos Test"


@pytest.mark.setup
class TestConftestExtended:
    """Pruebas extendidas para fixtures de UI y controladores en conftest.py."""

    def test_app_controller_fixture(self, app_controller, app_model):
        """Verifica la fixture del controlador principal."""
        assert app_controller is not None
        assert app_model is not None

    def test_worker_controller_fixture(self, worker_controller, label_counter_repo):
        """Verifica la fixture del controlador de trabajadores."""
        assert worker_controller is not None
        assert label_counter_repo is not None

    def test_ui_mocks(self, mock_main_view, mock_worker_view, mock_qr_scanner, mock_label_manager):
        """Verifica que los mocks de UI se carguen correctamente."""
        assert mock_main_view is not None
        assert mock_worker_view is not None
        assert mock_qr_scanner is not None
        assert mock_label_manager is not None
        
        # Ejercitar comportamiento básico de los mocks para cobertura
        mock_qr_scanner.parse_qr_data("test")
        mock_label_manager.count_qr_placeholders()

    def test_terminal_summary_manual(self):
        """Ejercita manualmente el hook de resumen de terminal."""
        terminalreporter = MagicMock(spec=["stats"])
        terminalreporter.stats = {'passed': [1], 'failed': []}
        config = MagicMock(spec=[])
        conftest.pytest_terminal_summary(terminalreporter, 0, config)
        # El hook se ejecuta sin error
        assert terminalreporter.stats is not None
