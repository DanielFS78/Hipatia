"""
Tests para verificar la infraestructura de generación de informes de auditoría.
Cubre el módulo tests.reporting.audit_report_generator.
"""
import pytest
import os
from pathlib import Path
from tests.reporting.audit_report_generator import ISO9001AuditReporter

@pytest.mark.setup
@pytest.mark.unit
class TestAuditInfrastructure:
    """Verifica que el generador de informes PDF funcione correctamente."""


    def test_pdf_generation_flow(self, tmp_path):
        """Prueba el flujo completo de generación de un PDF de auditoría."""
        reporter = ISO9001AuditReporter(output_dir=str(tmp_path))
        
        test_data = {
            'validation_results': [
                {'test_name': 'test_dummy_pass', 'status': 'PASS'},
                {'test_name': 'test_dummy_fail', 'status': 'FAIL'}
            ],
            'coverage': {'percent_covered': 85.5},
            'raw_coverage_files': {
                'core/app.py': {'summary': {'num_statements': 100, 'covered_lines': 80}}
            }
        }
        
        pdf_path = reporter.generate_business_pdf_report(test_data)
        
        assert pdf_path != ""
        assert Path(pdf_path).exists()
        assert Path(pdf_path).suffix == ".pdf"

    def test_pdf_generation_error_handling(self):
        """Verifica el manejo de errores al pasar una ruta de salida inválida."""
        # Usamos un nombre de archivo que sea un directorio existente para forzar error de escritura
        invalid_path = Path("/tmp/invalid_audit_dir/file_that_is_dir")
        invalid_path.mkdir(parents=True, exist_ok=True)
        
        reporter = ISO9001AuditReporter(output_dir=str(invalid_path))
        # Intentar generar el reporte donde el output_dir es un archivo (o algo que cause error)
        # O simplemente pasar None como test_data
        path = reporter.generate_business_pdf_report(None)
        assert path == ""
