"""Servicio de backup automatizado para protección de datos."""

import os
import logging
import tarfile
import shutil
import hashlib  # Compatibilidad para tests legacy que parchean este símbolo.
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from core.dtos import BackupInfoDTO


class BackupService:
    """Gestiona backups automatizados con rotación y verificación."""
    
    RETENTION_DAYS = 7
    
    def __init__(self, data_dir: str, backup_dir: Optional[str] = None):
        """
        Inicializa el servicio de backup.
        
        Args:
            data_dir: Directorio a respaldar (ej: 'data/')
            backup_dir: Directorio donde guardar backups (default: data/backups/)
        """
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.data_dir / 'backups'
        self.logger = logging.getLogger("BackupService")
        
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> Tuple[bool, str]:
        """
        Crea un backup comprimido del directorio de datos.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje/path)
        """
        try:
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_name
            
            # Verificar espacio en disco antes de crear backup
            if not self._check_disk_space():
                return False, "Espacio en disco insuficiente para crear backup"
            
            self.logger.info(f"Creando backup: {backup_name}")
            
            # Crear archivo tar.gz
            with tarfile.open(backup_path, "w:gz") as tar:
                # Recorrer archivos en data_dir excluyendo el directorio de backups
                for item in self.data_dir.iterdir():
                    if item.name == 'backups':
                        continue  # No respaldar los backups
                    
                    # Agregar al archivo con nombre relativo
                    arcname = item.name
                    tar.add(item, arcname=arcname)
            
            # Verificar integridad del backup
            if not self._verify_backup(backup_path):
                os.remove(backup_path)
                return False, "Backup creado pero falló verificación de integridad"
            
            # Crear archivo de checksum
            self._create_checksum(backup_path)
            
            file_size_mb = backup_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"Backup creado exitosamente: {backup_name} ({file_size_mb:.2f} MB)")
            
            return True, str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Error al crear backup: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self) -> int:
        """
        Elimina backups antiguos según política de retención.
        
        Returns:
            int: Número de backups eliminados
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)
            deleted_count = 0
            
            # Buscar todos los archivos de backup
            backup_files = list(self.backup_dir.glob("backup_*.tar.gz"))
            
            for backup_file in backup_files:
                # Extraer timestamp del nombre
                try:
                    # Formato: backup_YYYYMMDD_HHMMSS.tar.gz
                    # Usar name en lugar de stem para controlar mejor la extensión compuesta
                    filename = backup_file.name
                    if not filename.endswith(".tar.gz"):
                        continue
                        
                    timestamp_str = filename.replace("backup_", "").replace(".tar.gz", "")
                    
                    # Intentar parsear con segundos
                    try:
                        file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        # Intentar sin segundos por compatibilidad
                        file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M")
                    
                    if file_date < cutoff_date:
                        # Eliminar backup y su checksum
                        backup_file.unlink()
                        checksum_file = backup_file.with_suffix('.tar.gz.sha256')
                        if checksum_file.exists():
                            checksum_file.unlink()
                        
                        deleted_count += 1
                        self.logger.info(f"Backup antiguo eliminado: {backup_file.name}")
                        
                except ValueError as e:
                    # Nombre de archivo no coincide con el patrón esperado
                    self.logger.warning(f"Archivo de backup con formato inesperado: {backup_file.name} - {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Limpieza completada: {deleted_count} backups eliminados")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de backups: {e}")
            return 0
    
    def list_available_backups(self) -> List[BackupInfoDTO]:
        """
        Lista todos los backups disponibles ordenados por fecha (más reciente primero).
        
        Returns:
            List[BackupInfoDTO]: Lista de backups con metadata
        """
        backups: list[BackupInfoDTO] = []
        
        # Buscar todos los archivos de backup
        backup_files = list(self.backup_dir.glob("backup_*.tar.gz"))
        
        for backup_file in backup_files:
            try:
                # Formato: backup_YYYYMMDD_HHMMSS.tar.gz
                filename = backup_file.name
                if not filename.endswith(".tar.gz"):
                    continue
                    
                timestamp_str = filename.replace("backup_", "").replace(".tar.gz", "")
                
                # Intentar parsear con segundos
                try:
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    # Intentar sin segundos por compatibilidad
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M")
                
                file_size = backup_file.stat().st_size
                
                # Verificar si tiene checksum
                # Nota: with_suffix('.sha256') en un .tar.gz reemplazaría .gz por .sha256 -> .tar.sha256
                # Queremos .tar.gz.sha256, así que añadimos el sufijo manual
                checksum_file = backup_file.parent / (backup_file.name + ".sha256")
                if not checksum_file.exists():
                     # Intentar el patrón anterior por si acaso
                     checksum_file = backup_file.with_suffix('.tar.gz.sha256')
                
                has_checksum = checksum_file.exists()
                
                backups.append(
                    BackupInfoDTO(
                        name=backup_file.name,
                        path=str(backup_file),
                        date=file_date,
                        size_bytes=int(file_size),
                        size_mb=file_size / (1024 * 1024),
                        has_checksum=bool(has_checksum),
                    )
                )
                
            except (ValueError, OSError) as e:
                self.logger.warning(f"Error procesando backup {backup_file.name}: {e}")
                continue
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x.date, reverse=True)
        
        return backups
    
    def restore_backup(self, backup_name: str, target_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Restaura un backup a un directorio temporal para revisión.
        
        Args:
            backup_name: Nombre del archivo de backup
            target_dir: Directorio destino (default: data/restore_staging/)
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje/path)
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return False, f"Backup no encontrado: {backup_name}"
            
            # Verificar checksum antes de restaurar
            if not self._verify_checksum(backup_path):
                return False, "Checksum no coincide - backup posiblemente corrupto"
            
            # Directorio de staging para revisión antes de aplicar
            if target_dir is None:
                staging_dir = self.data_dir / 'restore_staging'
            else:
                staging_dir = Path(target_dir)
            
            # Limpiar staging si existe
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            staging_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Restaurando backup {backup_name} a {staging_dir}")
            
            # Extraer backup
            with tarfile.open(backup_path, "r:gz") as tar:
                import sys
                if sys.version_info >= (3, 12):
                    tar.extractall(staging_dir, filter='data')
                else:
                    tar.extractall(staging_dir)
            
            self.logger.info(f"Backup restaurado exitosamente en {staging_dir}")
            
            return True, str(staging_dir)
            
        except Exception as e:
            self.logger.error(f"Error al restaurar backup: {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Compatibilidad API legacy (tests y callers antiguos)
    # ------------------------------------------------------------------

    def _check_disk_space(self, min_free_gb: float = 0.5) -> bool:
        try:
            stat = shutil.disk_usage(self.backup_dir)
            free_gb = stat.free / (1024 ** 3)
            return free_gb >= min_free_gb
        except Exception as e:
            self.logger.warning(f"No se pudo verificar espacio en disco: {e}")
            return True

    def _verify_backup(self, backup_path: Path) -> bool:
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                members = tar.getmembers()
                return len(members) > 0
        except Exception as e:
            self.logger.error(f"Backup inválido: {e}")
            return False

    def _create_checksum(self, backup_path: Path) -> None:
        try:
            sha256_hash = hashlib.sha256()
            with open(backup_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum_file = backup_path.with_suffix('.tar.gz.sha256')
            checksum_file.write_text(sha256_hash.hexdigest())
        except Exception as e:
            self.logger.warning(f"No se pudo crear checksum: {e}")

    def _verify_checksum(self, backup_path: Path) -> bool:
        checksum_file = backup_path.with_suffix('.tar.gz.sha256')
        if not checksum_file.exists():
            self.logger.warning(f"No hay checksum para {backup_path.name}")
            return True
        try:
            stored_checksum = checksum_file.read_text().strip()
            sha256_hash = hashlib.sha256()
            with open(backup_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            calculated_checksum = sha256_hash.hexdigest()
            return stored_checksum == calculated_checksum
        except Exception as e:
            self.logger.error(f"Error verificando checksum: {e}")
            return False
    
