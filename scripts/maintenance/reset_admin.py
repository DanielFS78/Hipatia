"""
Script de mantenimiento: restablece o crea el usuario admin local en SQLite
(montaje.db) con contraseña conocida; uso manual en entornos de desarrollo.
"""
# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from database.models import Trabajador
from core.security.password_service import PasswordService

def reset_admin_password():
    db_path = os.path.abspath("montaje.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    admin = session.query(Trabajador).filter_by(username="admin").first()
    if not admin:
        print("Admin user not found. Creating it...")
        admin = Trabajador(
            nombre_completo="Admin Local",
            username="admin",
            role="Responsable",
            activo=True,
            tipo_trabajador=1
        )
        session.add(admin)
    
    print("Setting password for 'admin' to 'admin'...")
    admin.password_hash = PasswordService.hash_password("admin")
    session.commit()
    print("Success! You can now login with admin/admin in Local mode.")
    
    session.close()

if __name__ == "__main__":
    reset_admin_password()
