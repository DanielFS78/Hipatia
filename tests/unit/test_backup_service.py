"""
Tests unitarios para BackupService.
Sigue los estándares de calidad del proyecto Hipatia (100/100).
"""

import pytest
import tarfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, ANY, create_autospec
from typing import Any, cast
from core.services.backup_service import BackupService


@pytest.fixture
def mock_service(monkeypatch):
    """
    Fixture que proporciona BackupService con dependencias de sistema de archivos mockeadas.
    """
    # Mock de rutas
    mock_path_class = MagicMock(spec=["__call__", "side_effect"])
    
    mock_data_dir = MagicMock(spec=["__str__", "exists", "__truediv__", "iterdir"])
    cast(Any, mock_data_dir.__str__).return_value = "/mock/data"
    mock_data_dir.exists.return_value = True
    
    mock_backup_dir = MagicMock(spec=["__str__", "exists", "mkdir", "__truediv__", "glob"])
    cast(Any, mock_backup_dir.__str__).return_value = "/mock/data/backups"
    mock_backup_dir.exists.return_value = True
    
    # Configurar el comportamiento de la clase Path decorada
    def path_side_effect(arg):
        if arg == "/mock/data": return mock_data_dir
        if arg == "/mock/data/backups": return mock_backup_dir
        # Para cualquier otra ruta, devolver un mock genérico
        m = MagicMock(spec=["__str__"])
        cast(Any, m.__str__).return_value = str(arg)
        return m
        
    mock_path_class.side_effect = path_side_effect
    
    # Simular la unión de rutas: data_dir / "backups" -> backup_dir
    mock_data_dir.__truediv__.return_value = mock_backup_dir
    
    # Mock de dependencias externas en el módulo
    mock_tar = MagicMock(spec=tarfile)
    
    import hashlib
    mock_sha = MagicMock(spec=hashlib)
    
    with patch("core.services.backup_service.Path", new=mock_path_class), \
         patch("core.services.backup_service.tarfile", new=mock_tar), \
         patch("core.services.backup_service.hashlib", new=mock_sha):
        
        # Instanciar servicio
        class BackupServiceWithMocks(BackupService):
            mock_tar: Any
            mock_data_dir: Any
            mock_backup_dir: Any
            mock_sha: Any
            mock_path_class: Any

        service = cast(BackupServiceWithMocks, BackupService("/mock/data"))
        
        # Guardar mocks en el servicio para fácil acceso en tests
        service.mock_tar = mock_tar
        service.mock_data_dir = mock_data_dir
        service.mock_backup_dir = mock_backup_dir
        service.mock_sha = mock_sha
        service.mock_path_class = mock_path_class
        
        yield service


@pytest.mark.unit
class TestBackupServiceCreation:
    """Escenarios de prueba para la creación e inicialización de backups."""
    
    def test_init_creates_backup_directory(self, monkeypatch):
        """Verifica que el constructor crea el directorio de backups si no existe."""
        mock_path = MagicMock(spec=Path)
        cast(Any, mock_path.__str__).return_value = "/path/data"
        mock_bak_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = mock_bak_path
        
        # Simular que el directorio de backups no existe inicialmente
        mock_bak_path.exists.return_value = False
        
        with patch("core.services.backup_service.Path", return_value=mock_path):
            service = BackupService("/path/data")
            
            # Verificaciones
            mock_bak_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            assert service.backup_dir == mock_bak_path

    def test_create_backup_success(self, mock_service, monkeypatch):
        """Verifica el flujo de creación exitosa de un backup."""
        # Mock de archivos a incluir
        mock_db = MagicMock(spec=Path)
        mock_db.name = "test.db"
        mock_db.is_file.return_value = True
        
        mock_service.mock_data_dir.iterdir.return_value = [mock_db]
        
        # Mock de espacio en disco
        monkeypatch.setattr(mock_service, "_check_disk_space", lambda: True)
        # Mock de verificación interna para que no borre el archivo
        monkeypatch.setattr(mock_service, "_verify_backup", lambda x: True)
        
        # Mock de tarfile.open
        mock_tar_ctx = mock_service.mock_tar.open.return_value.__enter__.return_value
        
        # Mock de checksum
        mock_hash_inst = mock_service.mock_sha.sha256.return_value
        mock_hash_inst.hexdigest.return_value = "f" * 64
        
        # Mock de stat() y ruta final
        mock_stat = MagicMock(spec=["st_size"])
        mock_stat.st_size = 1024 * 1024 * 2 # 2 MB
        mock_bak_file = MagicMock(spec=Path)
        cast(Any, mock_bak_file.__str__).return_value = "/mock/data/backups/backup_test.tar.gz"
        mock_bak_file.stat.return_value = mock_stat
        mock_service.mock_backup_dir.__truediv__.return_value = mock_bak_file
        
        with patch("core.services.backup_service.open", create=True) as mock_open:
            # Configurar el mock del archivo para que la lectura termine (evitar bucle infinito)
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.side_effect = [b"mock data block", b""]
            
            success, result = mock_service.create_backup()
            
            assert success is True
            assert "tar.gz" in result
            mock_tar_ctx.add.assert_called()

    def test_create_backup_no_space(self, mock_service, monkeypatch):
        """Verifica que falla si no hay espacio suficiente en disco."""
        monkeypatch.setattr(mock_service, "_check_disk_space", lambda: False)
        
        success, message = mock_service.create_backup()
        
        assert success is False
        assert "espacio" in message.lower()


@pytest.mark.unit
class TestBackupServiceRotation:
    """Escenarios de prueba para la rotación y limpieza de backups antiguos."""
    
    def test_cleanup_old_backups(self, mock_service):
        """Verifica que se eliminan archivos que superan la política de retención."""
        # Mock de archivos de backup
        old_file = MagicMock(spec=Path)
        old_file.name = "backup_20200101_000000.tar.gz"
        
        recent_file = MagicMock(spec=Path)
        recent_file.name = f"backup_{datetime.now().strftime('%Y%m%d')}_000000.tar.gz"
        
        mock_service.mock_backup_dir.glob.return_value = [old_file, recent_file]
        
        # Nota: cleanup_old_backups no recibe argumentos en la implementación real
        deleted_count = mock_service.cleanup_old_backups()
        
        assert deleted_count == 1
        assert old_file.unlink.call_count == 1
        old_file.unlink.assert_called_once_with()
        recent_file.unlink.assert_not_called()

    def test_cleanup_removes_checksum_files(self, mock_service):
        """Verifica que al eliminar un backup también se borre su checksum."""
        old_file = MagicMock(spec=Path)
        old_file.name = "backup_20200101_000000.tar.gz"
        
        mock_checksum = MagicMock(spec=Path)
        mock_checksum.exists.return_value = True
        old_file.with_suffix.return_value = mock_checksum
        
        mock_service.mock_backup_dir.glob.return_value = [old_file]
        
        mock_service.cleanup_old_backups()
        
        # Verifica que se intentó borrar el .sha256
        old_file.with_suffix.assert_called_with(".tar.gz.sha256")
        assert mock_checksum.unlink.call_count == 1
        mock_checksum.unlink.assert_called_once_with()


@pytest.mark.unit
class TestBackupServiceRestore:
    """Escenarios de prueba para la restauración de backups."""
    
    def test_restore_backup_success(self, mock_service, monkeypatch):
        """Verifica el flujo completo de restauración exitosa."""
        backup_name = "backup_test.tar.gz"
        mock_backup_file = MagicMock(spec=Path)
        mock_backup_file.exists.return_value = True
        mock_service.mock_backup_dir.__truediv__.return_value = mock_backup_file
        
        # Mock de verificación de integridad
        monkeypatch.setattr(mock_service, "_verify_checksum", lambda x: True)
        monkeypatch.setattr(mock_service, "_verify_backup", lambda x: True)
        
        # Mock de extracción
        mock_tar_ctx = mock_service.mock_tar.open.return_value.__enter__.return_value
        
        # Mock de shutil.rmtree para evitar errores si staging ya existe
        import shutil
        mock_shutil = MagicMock(spec=shutil)
        monkeypatch.setattr("core.services.backup_service.shutil", mock_shutil)
        
        success, result = mock_service.restore_backup(backup_name)
        
        assert success is True
        # En la implementación real usa self.data_dir / 'restore_staging'
        staging_expected = mock_service.mock_data_dir / 'restore_staging'
        staging_expected.mkdir.assert_called()
        mock_tar_ctx.extractall.assert_called()

    def test_restore_backup_corrupted(self, mock_service, monkeypatch):
        """Verifica que falla si el checksum no coincide."""
        monkeypatch.setattr(mock_service, "_verify_checksum", lambda x: False)
        
        # Asegurar que el archivo existe para que no falle por "no encontrado"
        mock_service.mock_backup_dir.__truediv__.return_value.exists.return_value = True
        
        success, message = mock_service.restore_backup("corrupt.tar.gz")
        
        assert success is False
        assert "checksum" in message.lower()


@pytest.mark.unit
class TestBackupServiceVerification:
    """Escenarios de prueba para integridad y validación."""
    
    def test_verify_backup_valid(self, mock_service):
        """Verifica que un archivo tar válido es aceptado."""
        mock_path = MagicMock(spec=Path)
        mock_service.mock_tar.open.return_value.__enter__.return_value.getmembers.return_value = [
            MagicMock(spec=[])
        ]
        
        assert mock_service._verify_backup(mock_path) is True

    def test_verify_backup_invalid(self, mock_service):
        """Verifica que un archivo no tar es rechazado."""
        mock_path = MagicMock(spec=Path)
        # Forzar excepción en tarfile.open
        mock_service.mock_tar.open.side_effect = Exception("Not a tar")
        
        assert mock_service._verify_backup(mock_path) is False
