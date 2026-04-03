"""Funciones utilitarias para operación de backups."""

from __future__ import annotations

import hashlib
import shutil
import tarfile
from pathlib import Path
from typing import Any


def check_disk_space(path: Path, min_free_gb: float = 0.5) -> bool:
    """Verifica que exista espacio libre suficiente en el disco."""
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)
        return free_gb >= min_free_gb
    except Exception:
        return True


def verify_tar_backup(backup_path: Path, logger: Any) -> bool:
    """Verifica que el archivo de backup se pueda abrir y tenga contenido."""
    try:
        with tarfile.open(backup_path, "r:gz") as tar:
            return len(tar.getmembers()) > 0
    except Exception as exc:
        logger.error(f"Backup inválido: {exc}")
        return False


def create_checksum(backup_path: Path, logger: Any) -> None:
    """Crea archivo SHA256 para el backup."""
    try:
        sha256_hash = hashlib.sha256()
        with open(backup_path, "rb") as fh:
            for byte_block in iter(lambda: fh.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum_file = backup_path.with_suffix(".tar.gz.sha256")
        checksum_file.write_text(sha256_hash.hexdigest())
    except Exception as exc:
        logger.warning(f"No se pudo crear checksum: {exc}")


def verify_checksum(backup_path: Path, logger: Any) -> bool:
    """Valida checksum de backup si existe; si no existe, lo considera válido."""
    checksum_file = backup_path.with_suffix(".tar.gz.sha256")
    if not checksum_file.exists():
        logger.warning(f"No hay checksum para {backup_path.name}")
        return True

    try:
        stored_checksum = checksum_file.read_text().strip()
        sha256_hash = hashlib.sha256()
        with open(backup_path, "rb") as fh:
            for byte_block in iter(lambda: fh.read(4096), b""):
                sha256_hash.update(byte_block)
        return stored_checksum == sha256_hash.hexdigest()
    except Exception as exc:
        logger.error(f"Error verificando checksum: {exc}")
        return False
