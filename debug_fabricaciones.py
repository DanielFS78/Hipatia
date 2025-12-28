import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.getcwd())

from database.models import Fabricacion, Base

def inspect_fabricaciones():
    db_path = "montaje.db"
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- INSPECTING FABRICACION TABLE ---")
    stmt = select(Fabricacion).order_by(Fabricacion.id.desc()).limit(20)
    results = session.execute(stmt).scalars().all()

    for fab in results:
        print(f"ID: {fab.id}, Code: {fab.codigo}, Desc: {fab.descripcion}")

    print(f"Total count: {session.query(Fabricacion).count()}")

if __name__ == "__main__":
    inspect_fabricaciones()
