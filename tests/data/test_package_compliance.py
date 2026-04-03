"""
Tests de cumplimiento para el paquete tests.data.
Asegura que los patrones estructurales de calidad se ejecuten y verifiquen.
"""
import pytest
from tests.data import _compliance_check_structural_patterns

@pytest.mark.setup
class TestDataPackageCompliance:
    """Verifica el cumplimiento del paquete de datos."""
    
    def test_structural_compliance(self):
        """Ejecuta la verificación de patrones estructurales del paquete."""
        assert _compliance_check_structural_patterns() is True
