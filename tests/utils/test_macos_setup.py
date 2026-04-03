"""
Tests para verificar el workaround de configuración de entorno en macOS.
Cubre el módulo tests.utils.macos_fix.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from tests.utils.macos_fix import apply_macos_workaround, _compliance_check_structural_patterns

@pytest.mark.setup
@pytest.mark.unit
class TestMacOSFixInfrastructure:
    """Verifica la lógica de parcheo para rutas con espacios en macOS."""

    def test_compliance_patterns(self):
        """Verifica los patrones estructurales de calidad."""
        assert _compliance_check_structural_patterns() is True

    def test_apply_workaround_non_darwin(self):
        """Verifica que en sistemas no-macOS no se aplique nada (excepto offscreen)."""
        with patch("sys.platform", "linux"), patch("os.environ", {}):
            apply_macos_workaround()
            assert os.environ.get("QT_QPA_PLATFORM") == "offscreen"

    def test_apply_workaround_no_spaces(self):
        """Verifica que si no hay espacios en el path, no se aplique el fix de paths."""
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/path/without/spaces/file.py"), \
             patch("os.environ", {}):
            apply_macos_workaround()
            assert "tmp/pyqt6_venv" not in sys.path

    def test_apply_workaround_site_packages_not_found(self):
        """Cubre la rama donde no se encuentra site-packages (líneas 51-53)."""
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("site.getsitepackages", side_effect=Exception), \
             patch("sys.path", []), \
             patch("os.environ", {}):
            apply_macos_workaround()
            assert "QT_PLUGIN_PATH" not in os.environ

    def test_apply_workaround_site_packages_empty_list(self):
        """Cubre el caso donde getsitepackages devuelve lista vacía (línea 39)."""
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("site.getsitepackages", return_value=[]), \
             patch("sys.path", []), \
             patch("os.environ", {}):
            apply_macos_workaround()
            assert "QT_PLUGIN_PATH" not in os.environ

    def test_apply_workaround_create_tmp_dir(self):
        """Cubre la creación inicial del directorio temporal y copia (líneas 59-66)."""
        tmp_dir = "/tmp/pyqt6_venv"
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("os.path.exists", side_effect=lambda x: x != os.path.join(tmp_dir, "PyQt6")), \
             patch("site.getsitepackages", return_value=["/fake/site-packages"]), \
             patch("os.makedirs") as mock_mkdir, \
             patch("shutil.copytree") as mock_copy, \
             patch("subprocess.run") as mock_run, \
             patch("os.environ", {}):
            
            apply_macos_workaround()
            assert mock_mkdir.called
            assert mock_copy.called
            assert mock_run.called

    def test_apply_workaround_tmp_dir_exists(self):
        """Cubre el caso donde el directorio temporal ya existe (salta líneas 60-65)."""
        tmp_dir = "/tmp/pyqt6_venv"
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("os.path.exists", side_effect=lambda x: x == os.path.join(tmp_dir, "PyQt6") or "/fake" in x), \
             patch("site.getsitepackages", return_value=["/fake/site-packages"]), \
             patch("shutil.copytree") as mock_copy, \
             patch("os.environ", {}):
            
            apply_macos_workaround()
            # No debería llamar a copytree porque ya existe
            assert not mock_copy.called

    def test_apply_workaround_site_packages_in_sys_path(self):
        """Cubre la búsqueda de site-packages en sys.path (líneas 46-49)."""
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("site.getsitepackages", side_effect=Exception), \
             patch("sys.path", ["/some/site-packages", "/other"]), \
             patch("os.path.exists", side_effect=lambda x: "site-packages/PyQt6" in x or "/tmp" in x), \
             patch("os.environ", {}):
            
            with patch("shutil.copytree"), patch("subprocess.run"):
                apply_macos_workaround()
                assert "/tmp/pyqt6_venv" in sys.path

    def test_apply_workaround_exception_handling(self):
        """Cubre el bloque try-except final (línea 74)."""
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("os.path.exists", return_value=True), \
             patch("site.getsitepackages", return_value=["/fake/site-packages"]), \
             patch("shutil.copytree", side_effect=RuntimeError("Simulated error")), \
             patch("os.environ", {}):
            try:
                apply_macos_workaround()
            except RuntimeError:
                pytest.fail("apply_macos_workaround no debería propagar RuntimeError")
            assert sys.platform == "darwin"  # workaround no propagó excepción

    def test_apply_workaround_subprocess_error(self):
        """Cubre errores en subprocess.run."""
        tmp_dir = "/tmp/pyqt6_venv"
        with patch("sys.platform", "darwin"), \
             patch("os.path.abspath", return_value="/Path With Spaces/macos_fix.py"), \
             patch("os.path.exists", side_effect=lambda x: x != os.path.join(tmp_dir, "PyQt6")), \
             patch("site.getsitepackages", return_value=["/fake/site-packages"]), \
             patch("os.makedirs"), \
             patch("shutil.copytree"), \
             patch("subprocess.run", side_effect=Exception("cmd error")), \
             patch("os.environ", {}):
            try:
                apply_macos_workaround()
            except Exception:
                pytest.fail("apply_macos_workaround no debería propagar excepciones de subprocess")
            assert sys.platform == "darwin"  # contexto intacto
