"""
Script de mantenimiento: restablece o crea el usuario admin local en SQLite
con contraseña conocida; uso manual en entornos de desarrollo.
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Raíz del proyecto: scripts/maintenance -> scripts -> repo
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from database.config import DatabaseConfig
from database.models import Trabajador
from core.security.password_service import PasswordService


def _resolve_sqlite_db_path() -> str | None:
    """Devuelve la ruta del fichero SQLite según ``DatabaseConfig``, o None si no aplica."""
    db_url = DatabaseConfig.get_db_url()
    if not db_url.startswith("sqlite:///"):
        print(f"Este script solo admite SQLite; URL actual: {db_url}")
        return None
    return db_url.replace("sqlite:///", "")


def reset_admin_password() -> None:
    """Pone la contraseña del usuario ``admin`` a ``admin`` (solo SQLite configurado)."""
    db_path = _resolve_sqlite_db_path()
    if db_path is None:
        return
    if not Path(db_path).is_file():
        print(f"Base de datos no encontrada: {db_path}")
        return

    engine: Engine = create_engine(f"sqlite:///{db_path}")
    SessionFactory = sessionmaker(bind=engine)
    session: Session = SessionFactory()

    admin = session.query(Trabajador).filter_by(username="admin").first()
    if not admin:
        print("Usuario admin no encontrado. Creando...")
        admin = Trabajador(
            nombre_completo="Admin Local",
            username="admin",
            role="Responsable",
            activo=True,
            tipo_trabajador=1,
        )
        session.add(admin)

    print("Estableciendo contraseña de 'admin' a 'admin'...")
    admin.password_hash = PasswordService.hash_password("admin")
    session.commit()
    print("Listo. Puedes entrar con admin/admin en modo local.")

    session.close()


if __name__ == "__main__":
    reset_admin_password()
