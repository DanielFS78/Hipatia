# -*- coding: utf-8 -*-
# =================================================================================
# GESTOR DE LA BASE DE DATOS (database_manager.py)
# =================================================================================
# Este mÃ³dulo se encarga de toda la interacciÃ³n con la base de datos.
# Contiene la clase DatabaseManager con mÃ©todos para:
# 1. ConexiÃ³n directa a SQLite (legacy).
# 2. Sesiones de SQLAlchemy para nuevas implementaciones y migraciÃ³n gradual.
# =================================================================================

import sqlite3
import logging
import hashlib
from datetime import date, datetime
from typing import Dict, List, Optional

# --- NUEVOS IMPORTS PARA SQLALCHEMY ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import (Producto, Trabajador, Maquina, Pila, Subfabricacion,
                     ProcesoMecanico, Material, PasoPila, MachineMaintenanc,
                     TrabajadorPilaAnotacion, GrupoPreparacion, PreparacionPaso,
                     DiarioBitacora, EntradaDiario, Base, Fabricacion, Preproceso)
from .repositories import (ProductRepository, WorkerRepository, MachineRepository,
                             PilaRepository, LoteRepository, ConfigurationRepository,
                           MaterialRepository, PreprocesoRepository,
                           IterationRepository, TrackingRepository)


class DatabaseManager:
    """
    Gestiona todas las operaciones de la base de datos para la aplicaciÃ³n,
    soportando tanto conexiones directas a SQLite como sesiones de SQLAlchemy.
    """

    def __init__(self, db_path="montaje.db", existing_connection=None):
        """
        Inicializa el gestor, se conecta a la base de datos, configura SQLAlchemy,
        y crea las tablas.

        Args:
            db_path (str): Ruta al archivo de la base de datos.
            existing_connection: Una conexiÃ³n de base de datos existente (para tests).
        """
        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.engine = None
        self.SessionLocal = None

        try:
            # --- LÃ“GICA DE CONEXIÃ“N MODIFICADA ---
            if existing_connection:
                # Si se proporciona una conexiÃ³n (entorno de prueba), Ãºsala.
                self.conn = existing_connection
                self.logger.info("DatabaseManager inicializado con una conexiÃ³n existente.")
            else:
                # Comportamiento normal: crear una nueva conexiÃ³n.
                self.conn = sqlite3.connect(
                    db_path,
                    check_same_thread=False
                )
                self.logger.info(f"CoÓOnexiÃ³n legacy exitosa a la base de datos en: {db_path}")

            self.cursor = self.conn.cursor()

            # --- CONFIGURACIÓN DE SQLALCHEMY (CORREGIDA) ---
            def get_existing_connection():
                return self.conn

            db_url = "sqlite://"
            self.engine = create_engine(db_url, creator=get_existing_connection, echo=False)

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.logger.info("Motor y sesión de SQLAlchemy configurados para compartir conexiÃ³n.")

            # --- MIGRACIONES Y CREACIÃ“N DE TABLAS ---
            self._check_and_migrate()
            self.create_tables()
            self.ensure_preprocesos_tables()
            self.product_repo = ProductRepository(self.SessionLocal)
            self.worker_repo = WorkerRepository(self.SessionLocal)
            self.machine_repo = MachineRepository(self.SessionLocal)
            self.pila_repo = PilaRepository(self.SessionLocal)
            self.lote_repo = LoteRepository(self.SessionLocal)
            self.preproceso_repo = PreprocesoRepository(self.SessionLocal)
            self.config_repo = ConfigurationRepository(self.SessionLocal)
            # MaintenanceRepository eliminado - funcionalidad en MachineRepository
            self.material_repo = MaterialRepository(self.SessionLocal)
            self.iteration_repo = IterationRepository(self.SessionLocal)
            self.iteration_repo = IterationRepository(self.SessionLocal)
            self.tracking_repo = TrackingRepository(self.SessionLocal)

        except sqlite3.Error as e:
            self.logger.critical(f"CRITICAL: Error al conectar (sqlite3) a la base de datos: {e}")
            self.conn = None
            self.cursor = None
        except Exception as e:
            self.logger.critical(f"CRITICAL: Error general en la inicialización de DatabaseManager: {e}")
            self.conn = None
            self.cursor = None
            self.engine = None

    # =================================================================================
    # --- NUEVOS MÃ‰TODOS DE SQLALCHEMY ---
    # =================================================================================

    def close(self):
        """Cierra todas las conexiones a la base de datos."""
        if self.SessionLocal:
            self.SessionLocal.close_all()
        
        if self.engine:
            self.engine.dispose()
            self.engine = None
            
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.ProgrammingError:
                pass # Ya estaba cerrada
            self.conn = None
            self.cursor = None
            
        self.logger.info("Conexiones a base de datos cerradas.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =================================================================================
    # --- NUEVOS MÃ‰TODOS DE SQLALCHEMY ---
    # =================================================================================

    def get_session(self):
        """Devuelve una nueva sesión de SQLAlchemy."""
        if not self.SessionLocal:
            self.logger.error("SessionLocal no está inicializado. No se puede crear sesión.")
            return None
        return self.SessionLocal()

    def _get_schema_version(self) -> int:
        """Obtiene la versión del esquema. Si no existe, asume la versión 0."""
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS db_info (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.cursor.execute("SELECT value FROM db_info WHERE key = 'schema_version'")
            result = self.cursor.fetchone()
            if result:
                return int(result[0])
            else:
                # Si la tabla existe pero no la clave, es una BD pre-versionado.
                self.cursor.execute("INSERT INTO db_info (key, value) VALUES ('schema_version', '0')")
                self.conn.commit()
                return 0
        except sqlite3.Error:
            return 0





    def create_fabricacion_productos_table(self):
        """Crea la tabla de enlace fabricacion_productos si no existe."""
        # CORRECCIÃ“N: Se usa self.conn en lugar de self.connection
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fabricacion_productos (
                fabricacion_id INTEGER NOT NULL,
                producto_codigo TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (fabricacion_id, producto_codigo),
                FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()
        self.logger.info("Tabla fabricacion_productos verificada/creada.")



    # ==============================================================================
    # CREAR TABLA FABRICACION_PRODUCTOS (AÃ‘ADIR AL MÃ‰TODO ensure_preprocesos_tables)
    # ==============================================================================

    def ensure_preprocesos_tables(self):
        """
        Verifica y crea las tablas necesarias para preprocesos y fabricaciones.
        Este mÃ©todo debe ejecutarse en la inicializaciÃ³n para asegurar
        que las nuevas tablas estÃ©n disponibles.
        """
        try:
            # Tablas existentes...
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                descripcion TEXT
            )
            """)

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preprocesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                tiempo REAL NOT NULL DEFAULT 0.0
            )
            """)

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preproceso_material_link (
                preproceso_id INTEGER,
                material_id INTEGER,
                PRIMARY KEY (preproceso_id, material_id),
                FOREIGN KEY (preproceso_id) REFERENCES preprocesos (id) ON DELETE CASCADE,
                FOREIGN KEY (material_id) REFERENCES materiales (id) ON DELETE CASCADE
            )
            """)

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricacion_preproceso_link (
                fabricacion_id INTEGER,
                preproceso_id INTEGER,
                PRIMARY KEY (fabricacion_id, preproceso_id),
                FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (preproceso_id) REFERENCES preprocesos (id) ON DELETE CASCADE
            )
            """)


            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricacion_productos (
                fabricacion_id INTEGER NOT NULL,
                producto_codigo TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (fabricacion_id, producto_codigo),
                FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE
            )
            """)

            self.conn.commit()
            self.logger.info("Tablas de preprocesos y fabricaciones verificadas/creadas exitosamente.")

        except sqlite3.Error as e:
            self.logger.error(f"Error creando tablas de preprocesos: {e}")
            if self.conn:
                self.conn.rollback()

    def _set_schema_version(self, version: int):
        """Actualiza la versiÃ³n del esquema en la tabla 'db_info'."""
        try:
            self.cursor.execute("UPDATE db_info SET value = ? WHERE key = 'schema_version'", (str(version),))
            self.conn.commit()
            logging.info(f"Versión del esquema de la BD actualizada a {version}.")
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar la versión del esquema de la BD: {e}")

    def _migrate_to_v3(self):
        """
        Crea las tablas para el sistema de Preprocesos.
        - fabricaciones
        - preprocesos
        - preproceso_material_link (M-M)
        - fabricacion_preproceso_link (M-M)
        """
        self.logger.info("Aplicando migración a v3: Creando tablas de Preprocesos...")
        try:
            tables_to_create = [
                Fabricacion.__table__,
                Preproceso.__table__,
                # Las tablas de enlace se incluyen a travÃ©s de Base.metadata
            ]
            Base.metadata.create_all(self.engine, tables=[tbl for tbl in Base.metadata.sorted_tables if
                                                          tbl.name in ['fabricaciones', 'preprocesos',
                                                                       'preproceso_material_link',
                                                                       'fabricacion_preproceso_link']], checkfirst=True)
            self._set_schema_version(3)
            self.logger.info("Tablas de Preprocesos creadas con Éxito.")
            return True
        except Exception as e:
            self.logger.error(f"Error al migrar a v3: {e}")
            return False

    def _migrate_to_v4(self):
        """AÃ±ade la columna 'tiempo' a la tabla 'preprocesos'."""
        self.logger.info("Aplicando migraciÃ³n a v4: AÃ±adiendo 'tiempo' a preprocesos...")
        try:
            self.cursor.execute("ALTER TABLE preprocesos ADD COLUMN tiempo REAL NOT NULL DEFAULT 0.0")
            self.conn.commit()
            self._set_schema_version(4)
            self.logger.info("Columna 'tiempo' aÃ±adida a 'preprocesos' con Ã©xito.")
            return True
        except sqlite3.OperationalError:
            # La columna ya existe, lo consideramos un Ã©xito para la migraciÃ³n
            self._set_schema_version(4)
            self.logger.warning("La columna 'tiempo' ya existÃ­a en 'preprocesos'.")
            return True
        except Exception as e:
            self.logger.error(f"Error al migrar a v4: {e}")
            self.conn.rollback()
            return False

    def _migrate_to_v5(self):
        """AÃ±ade columnas para tipo_fallo y ruta_plano a la tabla de iteraciones."""
        self.logger.info("Aplicando migraciÃ³n a v5: AÃ±adiendo campos a iteraciones_producto...")
        try:
            self.cursor.execute("ALTER TABLE iteraciones_producto ADD COLUMN tipo_fallo TEXT")
            self.cursor.execute("ALTER TABLE iteraciones_producto ADD COLUMN ruta_plano TEXT")
            self.conn.commit()
            self._set_schema_version(5)
            self.logger.info("Columnas 'tipo_fallo' y 'ruta_plano' aÃ±adidas con Ã©xito.")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self._set_schema_version(5)
                self.logger.warning(f"Las columnas para la v5 ya existÃ­an: {e}")
                return True
            self.logger.error(f"Error operacional al migrar a v5: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            self.logger.error(f"Error general al migrar a v5: {e}")
            self.conn.rollback()
            return False

    def _migrate_to_v6(self):
        """
        Migra la tabla 'subfabricaciones' para usar una clave forÃ¡nea 'maquina_id'
        en lugar de un campo de texto 'requiere_maquina_tipo'.
        VERSIÃ“N CORREGIDA: Verifica si la migraciÃ³n ya se aplicÃ³.
        """
        self.logger.info("Aplicando migraciÃ³n a v6: Actualizando subfabricaciones para usar maquina_id...")
        try:
            # VERIFICAR SI LA MIGRACIÃ“N YA SE APLICÃ“
            self.cursor.execute("PRAGMA table_info(subfabricaciones)")
            columns = [column[1] for column in self.cursor.fetchall()]

            # Si ya tiene maquina_id y no tiene requiere_maquina_tipo, ya estÃ¡ migrada
            if 'maquina_id' in columns and 'requiere_maquina_tipo' not in columns:
                self.logger.info("La tabla subfabricaciones ya tiene el esquema v6. Saltando migraciÃ³n.")
                self._set_schema_version(6)
                return True

            # Si tiene ambas columnas o solo la antigua, hacer migraciÃ³n
            if 'requiere_maquina_tipo' in columns:
                self.cursor.execute("PRAGMA foreign_keys=off;")
                self.cursor.execute("BEGIN TRANSACTION;")

                # 1. Renombrar la tabla original
                self.cursor.execute("ALTER TABLE subfabricaciones RENAME TO subfabricaciones_old;")

                # 2. Crear la nueva tabla con la estructura correcta
                self.cursor.execute("""
                    CREATE TABLE subfabricaciones (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        producto_codigo TEXT NOT NULL,
                        descripcion TEXT NOT NULL,
                        tiempo REAL NOT NULL,
                        tipo_trabajador INTEGER NOT NULL,
                        maquina_id INTEGER,
                        FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE,
                        FOREIGN KEY (maquina_id) REFERENCES maquinas (id) ON DELETE SET NULL
                    );
                """)

                # 3. Migrar datos existentes
                self.logger.info("Migrando datos existentes...")
                self.cursor.execute("""
                    INSERT INTO subfabricaciones (id, producto_codigo, descripcion, tiempo, tipo_trabajador, maquina_id)
                    SELECT
                        o.id,
                        o.producto_codigo,
                        o.descripcion,
                        o.tiempo,
                        o.tipo_trabajador,
                        (SELECT id FROM maquinas WHERE tipo_proceso = o.requiere_maquina_tipo LIMIT 1)
                    FROM subfabricaciones_old AS o;
                """)

                # 4. Eliminar la tabla antigua
                self.cursor.execute("DROP TABLE subfabricaciones_old;")

                self.cursor.execute("COMMIT;")
                self.cursor.execute("PRAGMA foreign_keys=on;")

            self._set_schema_version(6)
            self.logger.info("MigraciÃ³n a v6 completada con Ã©xito.")
            return True

        except Exception as e:
            self.logger.error(f"Error al migrar a v6: {e}")
            self.conn.rollback()
            self.cursor.execute("PRAGMA foreign_keys=on;")
            return False

    def _migrate_to_v7(self):
        """AÃ±ade la columna para guardar la 'pila de cÃ¡lculo' en formato JSON."""
        self.logger.info("Aplicando migraciÃ³n a v7: AÃ±adiendo 'pila_de_calculo_json' a la tabla 'pilas'...")
        try:
            self.cursor.execute("ALTER TABLE pilas ADD COLUMN pila_de_calculo_json TEXT")
            self.conn.commit()
            self._set_schema_version(7)
            self.logger.info("Columna 'pila_de_calculo_json' aÃ±adida a 'pilas' con Ã©xito.")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # La columna ya existe, lo consideramos un Ã©xito para la migraciÃ³n.
                self._set_schema_version(7)
                self.logger.warning("La columna 'pila_de_calculo_json' ya existÃ­a. Marcando como migrado.")
                return True
            self.logger.error(f"Error operacional al migrar a v7: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            self.logger.error(f"Error general al migrar a v7: {e}")
            self.conn.rollback()
            return False

    def _migrate_to_v8(self):
        """AÃ±ade la columna 'tipo_trabajador' a la tabla 'trabajadores'."""
        self.logger.info("Aplicando migraciÃ³n a v8: AÃ±adiendo 'tipo_trabajador' a trabajadores...")
        try:
            self.cursor.execute("ALTER TABLE trabajadores ADD COLUMN tipo_trabajador INTEGER NOT NULL DEFAULT 1")
            self.conn.commit()
            self._set_schema_version(8)
            self.logger.info("Columna 'tipo_trabajador' aÃ±adida a 'trabajadores' con Ã©xito.")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self._set_schema_version(8)
                self.logger.warning("La columna 'tipo_trabajador' ya existÃ­a. Marcando como migrado.")
                return True
            self.logger.error(f"Error operacional al migrar a v8: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            self.logger.error(f"Error general al migrar a v8: {e}")
            self.conn.rollback()
            return False

    def _migrate_to_v9(self):
        """Reestructura las tablas de Lote sin perder datos."""
        self.logger.info("Aplicando migraciÃ³n a v9: Reestructurando tablas de Lotes...")
        try:
            from .models import Lote, lote_producto_link, lote_fabricacion_link

            # Iniciamos una transacciÃ³n para poder revertir si algo falla
            self.cursor.execute("BEGIN TRANSACTION;")

            # 1. Comprobar si la tabla antigua y errÃ³nea existe
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lote_contenido_link'")
            if self.cursor.fetchone():
                self.logger.info("Eliminando tabla 'lote_contenido_link' obsoleta.")
                # Como no tenÃ­a datos, es seguro eliminarla directamente
                self.cursor.execute("DROP TABLE lote_contenido_link;")

            # 2. Crear las nuevas tablas usando el motor de SQLAlchemy
            # Esto asegura que se creen exactamente como el modelo las define.
            Base.metadata.create_all(self.engine, tables=[
                Lote.__table__,
                lote_producto_link,
                lote_fabricacion_link
            ], checkfirst=True)
            self.logger.info("Nuevas tablas de Lotes y enlaces creadas con Ã©xito.")

            # 3. Finalizar la transacciÃ³n
            self.conn.commit()

            self._set_schema_version(9)
            self.logger.info("MigraciÃ³n a v9 completada. Tus datos estÃ¡n intactos.")
            return True
        except Exception as e:
            self.logger.error(f"Error al migrar a v9: {e}")
            self.conn.rollback()  # Revertir cambios si algo falla
            return False

    def _migrate_to_v10(self):
        """AÃ±ade tipo_trabajador a preprocesos"""
        self.logger.info("Migrando a v10: aÃ±adiendo tipo_trabajador a preprocesos...")
        try:
            self.cursor.execute("""
                ALTER TABLE preprocesos 
                ADD COLUMN tipo_trabajador INTEGER NOT NULL DEFAULT 1
            """)
            self.conn.commit()
            self._set_schema_version(10)
            self.logger.info("MigraciÃ³n a v10 completada.")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                self.logger.info("La columna tipo_trabajador ya existe.")
                self._set_schema_version(10)
                return True
            else:
                self.logger.error(f"Error en migraciÃ³n v10: {e}")
                return False

    def _migrate_to_v11(self):
        """Añade la columna 'orden_fabricacion' a la tabla 'trabajo_logs'."""
        self.logger.info("Aplicando migración a v11: Añadiendo 'orden_fabricacion' a trabajo_logs...")
        try:
            self.cursor.execute("ALTER TABLE trabajo_logs ADD COLUMN orden_fabricacion TEXT")
            self.conn.commit()
            self._set_schema_version(11)
            self.logger.info("Columna 'orden_fabricacion' añadida a 'trabajo_logs' con éxito.")
            return True
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                self._set_schema_version(11)
                self.logger.warning("La columna 'orden_fabricacion' ya existía. Marcando como migrado.")
                return True
            self.logger.error(f"Error operacional al migrar a v11: {e}")
            self.conn.rollback()
            return False
            self.conn.rollback()
            return False

    def _migrate_to_v12(self):
        """Añade la tabla 'iteration_images' para soportar múltiples imágenes por iteración."""
        self.logger.info("Aplicando migración a v12: Creando tabla 'iteration_images'...")
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS iteration_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    iteration_id INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    description TEXT,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (iteration_id) REFERENCES iteraciones_producto (id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            self._set_schema_version(12)
            self.logger.info("Tabla 'iteration_images' creada con éxito.")
            return True
        except Exception as e:
            self.logger.error(f"Error general al migrar a v12: {e}")
            self.conn.rollback()
            return False

    def _migrate_to_v13(self):
        """Añade la tabla 'fabricacion_contadores' para numeración de etiquetas."""
        self.logger.info("Aplicando migración a v13: Creando tabla 'fabricacion_contadores'...")
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS fabricacion_contadores (
                    fabricacion_id INTEGER PRIMARY KEY,
                    ultimo_numero_unidad INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            self._set_schema_version(13)
            self.logger.info("Tabla 'fabricacion_contadores' creada con éxito.")
            return True
        except Exception as e:
            self.logger.error(f"Error general al migrar a v13: {e}")
            self.conn.rollback()
            return False

    def _check_and_migrate(self):
        """
        Comprueba la versiÃ³n de la base de datos y aplica las migraciones necesarias.
        """
        current_version = self._get_schema_version()
        self.logger.info(f"VersiÃ³n actual de la DB: {current_version}")

        if current_version < 1:
            if not self._migrate_to_v1(): return
            current_version = 1

        if current_version < 2:
           if not self._migrate_to_v2(): return
           current_version = 2

        if current_version < 3:
            if not self._migrate_to_v3(): return
            current_version = 3

        if current_version < 4:
            if not self._migrate_to_v4(): return
            current_version = 4

        if current_version < 5:
            if not self._migrate_to_v5(): return
            current_version = 5

        if current_version < 6:
            if not self._migrate_to_v6(): return
            current_version = 6

        if current_version < 7:
            if not self._migrate_to_v7(): return
            current_version = 7

        if current_version < 8:
            if not self._migrate_to_v8(): return
            current_version = 8

        if current_version < 9:
            if not self._migrate_to_v9(): return
            current_version = 9

        if current_version < 10:
            if not self._migrate_to_v10():
                self.logger.error("FallÃ³ la migraciÃ³n a v10")

        if current_version < 11:
            if not self._migrate_to_v11():
                self.logger.error("Falló la migración a v11")

        if current_version < 12:
            if not self._migrate_to_v12():
                self.logger.error("Falló la migración a v12")

        if current_version < 13:
            if not self._migrate_to_v13():
                self.logger.error("Falló la migración a v13")
            current_version = 13

        if self._get_schema_version() == current_version:
            self.logger.info("La base de datos estÃ¡ actualizada.")
        else:
            self.logger.warning("No se pudo actualizar la base de datos a la Ãºltima versiÃ³n.")

    def _run_migrations(self, from_version: int, to_version: int):
        """Ejecuta las funciones de migraciÃ³n necesarias en secuencia."""
        logging.info(f"Ejecutando migraciones desde la v{from_version} a la v{to_version}.")

        # El diccionario de migraciones mapea la versiÃ³n de destino a la funciÃ³n que la alcanza.
        migrations = {
            1: self._migrate_to_v1,
            # Futuras migraciones irÃ­an aquÃ­:
            # 2: self._migrate_to_v2,
            2: self._migrate_to_v2,
        }

        for version in sorted(migrations.keys()):
            if from_version < version <= to_version:
                try:
                    logging.info(f"Aplicando migraciÃ³n para alcanzar la v{version}...")
                    migrations[version]()
                    self._set_schema_version(version)
                    logging.info(f"MigraciÃ³n a v{version} completada con Ã©xito.")
                except sqlite3.Error as e:
                    logging.critical(f"FALLO CRÃTICO al migrar a la v{version}: {e}", exc_info=True)
                    self.conn.rollback()
                    raise Exception(f"No se pudo migrar la base de datos a la v{version}.") from e

    def _migrate_to_v1(self):
        """
        MigraciÃ³n inicial. AÃ±ade las columnas necesarias a las tablas existentes
        para alcanzar el esquema de la versiÃ³n 1.
        """
        self.cursor.execute("BEGIN TRANSACTION")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS db_info (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

        # --- CORRECCIÃ“N PRINCIPAL: AÃ±adir la columna que falta ---
        try:
            self.cursor.execute("ALTER TABLE subfabricaciones ADD COLUMN requiere_maquina_tipo TEXT")
            self.logger.info("Columna 'requiere_maquina_tipo' aÃ±adida a 'subfabricaciones'.")
        except sqlite3.OperationalError:
            pass  # La columna ya existe, no hacer nada

        try:
            self.cursor.execute("ALTER TABLE fabricaciones ADD COLUMN estado TEXT NOT NULL DEFAULT 'Pendiente'")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE iteraciones_producto ADD COLUMN ruta_imagen TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute("ALTER TABLE trabajadores ADD COLUMN username TEXT UNIQUE")
            self.cursor.execute("ALTER TABLE trabajadores ADD COLUMN password_hash TEXT")
            self.cursor.execute("ALTER TABLE trabajadores ADD COLUMN role TEXT")
        except sqlite3.OperationalError:
            pass

        self.conn.commit()

    def _migrate_to_v2(self):
        """
        MigraciÃ³n para eliminar tablas de fabricaciones y actualizar referencias.
        """
        self.cursor.execute("BEGIN TRANSACTION")

        try:
            # Eliminar tablas de fabricaciones
            self.cursor.execute("DROP TABLE IF EXISTS fabricacion_contenido")
            self.cursor.execute("DROP TABLE IF EXISTS fabricaciones")

            # Actualizar referencias en pilas si existen
            self.cursor.execute("PRAGMA table_info(pilas)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if 'fabricacion_origen_codigo' in columns:
                # Renombrar columna en tabla pilas
                self.cursor.execute(
                    "ALTER TABLE pilas RENAME COLUMN fabricacion_origen_codigo TO producto_origen_codigo")

            self.conn.commit()
            self.logger.info("MigraciÃ³n v2 completada: eliminadas tablas de fabricaciones.")
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Error en migraciÃ³n v2: {e}")
            raise





    def create_tables(self):
        """Crea todas las tablas necesarias en la base de datos."""
        try:
            cursor = self.conn.cursor()

            # âœ… AÃ‘ADIR TABLA USUARIOS QUE FALTA
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'Trabajador',
                    worker_id INTEGER,
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (worker_id) REFERENCES trabajadores(id)
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    codigo TEXT PRIMARY KEY, descripcion TEXT NOT NULL, departamento TEXT NOT NULL,
                    tipo_trabajador INTEGER NOT NULL, donde TEXT, tiene_subfabricaciones INTEGER NOT NULL,
                    tiempo_optimo REAL
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS subfabricaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_codigo TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    tiempo REAL NOT NULL,
                    tipo_trabajador INTEGER NOT NULL,
                    maquina_id INTEGER,
                    FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE,
                    FOREIGN KEY (maquina_id) REFERENCES maquinas (id) ON DELETE SET NULL
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS procesos_mecanicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_codigo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    tiempo REAL NOT NULL,
                    tipo_trabajador INTEGER NOT NULL,
                    FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS trabajadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_completo TEXT NOT NULL UNIQUE,
                    activo INTEGER NOT NULL DEFAULT 1,
                    notas TEXT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS maquinas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
                    departamento TEXT NOT NULL, tipo_proceso TEXT, activa INTEGER NOT NULL DEFAULT 1
                )""")
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS machine_maintenance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id INTEGER NOT NULL,
                    maintenance_date DATE NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (machine_id) REFERENCES maquinas(id) ON DELETE CASCADE
                )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabajador_pila_anotaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER NOT NULL,
                pila_id INTEGER NOT NULL,
                fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                anotacion TEXT NOT NULL,
                FOREIGN KEY (worker_id) REFERENCES trabajadores(id) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS grupos_preparacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                maquina_id INTEGER NOT NULL,
                descripcion TEXT,
                producto_codigo TEXT REFERENCES productos(codigo) ON DELETE SET NULL,
                UNIQUE(nombre, maquina_id),
                FOREIGN KEY (maquina_id) REFERENCES maquinas (id) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preparacion_pasos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                descripcion TEXT, tiempo_fase REAL NOT NULL, grupo_id INTEGER,
                es_diario INTEGER DEFAULT 0, es_verificacion INTEGER DEFAULT 0,
                FOREIGN KEY (grupo_id) REFERENCES grupos_preparacion(id) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS iteraciones_producto (
                id INTEGER PRIMARY KEY AUTOINCREMENT, producto_codigo TEXT NOT NULL,
                fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                nombre_responsable TEXT NOT NULL, descripcion_cambio TEXT,
                ruta_imagen TEXT,
                tipo_fallo TEXT, 
                ruta_plano TEXT, 
                FOREIGN KEY (producto_codigo) REFERENCES productos (codigo) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_componente TEXT UNIQUE NOT NULL,
                descripcion_componente TEXT
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS iteracion_material_link (
                iteracion_id INTEGER,
                material_id INTEGER,
                PRIMARY KEY (iteracion_id, material_id),
                FOREIGN KEY (iteracion_id) REFERENCES iteraciones_producto (id) ON DELETE CASCADE,
                FOREIGN KEY (material_id) REFERENCES materiales (id) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS producto_material_link (
                producto_codigo TEXT,
                material_id INTEGER,
                PRIMARY KEY (producto_codigo, material_id),
                FOREIGN KEY (producto_codigo) REFERENCES productos(codigo) ON DELETE CASCADE,
                FOREIGN KEY (material_id) REFERENCES materiales(id) ON DELETE CASCADE
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pasos_trazabilidad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trabajo_log_id INTEGER NOT NULL,
                trabajador_id INTEGER NOT NULL,
                maquina_id INTEGER,
                paso_nombre TEXT NOT NULL,
                tipo_paso TEXT NOT NULL,
                tiempo_inicio_paso TIMESTAMP NOT NULL,
                tiempo_fin_paso TIMESTAMP,
                duracion_paso_segundos INTEGER,
                estado_paso TEXT NOT NULL,
                FOREIGN KEY (trabajo_log_id) REFERENCES trabajo_logs(id) ON DELETE CASCADE,
                FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id),
                FOREIGN KEY (maquina_id) REFERENCES maquinas(id)
            )""")
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricacion_contadores (
                fabricacion_id INTEGER PRIMARY KEY,
                ultimo_numero_unidad INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE
            )""")

            # --- CREACIÓN DEL USUARIO ADMINISTRADOR POR DEFECTO ---
            self.cursor.execute("SELECT COUNT(id) FROM trabajadores")
            if self.cursor.fetchone()[0] == 0:
                self.logger.info("La tabla 'trabajadores' estÃ¡ vacÃ­a. Creando usuario administrador por defecto...")
                admin_pass = 'admin'
                admin_hash = hashlib.sha256(admin_pass.encode('utf-8')).hexdigest()
                # Se aÃ±ade la columna 'tipo_trabajador' al INSERT
                admin_sql = "INSERT INTO trabajadores (nombre_completo, activo, username, password_hash, role, tipo_trabajador) VALUES (?, ?, ?, ?, ?, ?)"
                # Se aÃ±ade el valor por defecto (1) para tipo_trabajador
                self.cursor.execute(admin_sql, ("Administrador del Sistema", 1, "admin", admin_hash, "Responsable", 1))
                self.logger.info("Usuario 'admin' con rol 'Responsable' creado con Ã©xito.")

            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error al verificar/crear las tablas base: {e}", exc_info=True)
            self.conn.rollback()




    # MÃ‰TODOS CRUD PARA MÃQUINAS


    # En database_manager.py -> get_machine_usage_stats()


    # ==============================================================================
    # DELEGADOS DE PREPROCESO REPOSITORY (AÑADIDOS EN REFACTORIZACIÓN DTO)
    # ==============================================================================


    # --- MÃ‰TODOS NUEVOS PARA HISTORIALES ---
    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str):
        """AÃ±ade un nuevo registro de mantenimiento para una mÃ¡quina."""
        if not self.conn: return False
        try:
            sql = "INSERT INTO machine_maintenance (machine_id, maintenance_date, notes) VALUES (?, ?, ?)"
            self.cursor.execute(sql, (machine_id, maintenance_date, notes))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.error(f"Error al aÃ±adir registro de mantenimiento para la mÃ¡quina {machine_id}: {e}")
            return False


    # ========================================================================
    # MÉTODOS DE TRACKING Y TRAZABILIDAD
    # ========================================================================

    def iniciar_trabajo_qr(
            self,
            qr_code: str,
            trabajador_id: int,
            fabricacion_id: int,
            producto_codigo: str,
            notas: Optional[str] = None
    ):
        """
        [NUEVO] Inicia el registro de tiempo para una unidad con código QR.

        Args:
            qr_code: Código QR único de la unidad
            trabajador_id: ID del trabajador
            fabricacion_id: ID de la fabricación
            producto_codigo: Código del producto
            notas: Notas opcionales

        Returns:
            TrabajoLog creado o None si hay error
        """
        return self.tracking_repo.iniciar_trabajo(
            qr_code=qr_code,
            trabajador_id=trabajador_id,
            fabricacion_id=fabricacion_id,
            producto_codigo=producto_codigo,
            notas=notas
        )

    def finalizar_trabajo_qr(self, qr_code: str, notas: Optional[str] = None):
        """
        [NUEVO] Finaliza el registro de tiempo de una unidad.

        Args:
            qr_code: Código QR de la unidad
            notas: Notas de finalización (opcional)

        Returns:
            TrabajoLog actualizado o None si hay error
        """
        return self.tracking_repo.finalizar_trabajo(
            qr_code=qr_code,
            notas_finalizacion=notas
        )

    def registrar_incidencia(
            self,
            trabajo_log_id: int,
            trabajador_id: int,
            tipo_incidencia: str,
            descripcion: str,
            rutas_fotos: Optional[List[str]] = None
    ):
        """
        [NUEVO] Registra una incidencia durante la producción.

        Args:
            trabajo_log_id: ID del trabajo asociado
            trabajador_id: ID del trabajador que reporta
            tipo_incidencia: Tipo de incidencia
            descripcion: Descripción detallada
            rutas_fotos: Lista de rutas de fotos (opcional)

        Returns:
            IncidenciaLog creada o None si hay error
        """
        return self.tracking_repo.registrar_incidencia(
            trabajo_log_id=trabajo_log_id,
            trabajador_id=trabajador_id,
            tipo_incidencia=tipo_incidencia,
            descripcion=descripcion,
            rutas_fotos=rutas_fotos
        )

    def asignar_trabajador_fabricacion(
            self,
            trabajador_id: int,
            fabricacion_id: int
    ) -> bool:
        """
        [NUEVO] Asigna un trabajador a una fabricación.

        Args:
            trabajador_id: ID del trabajador
            fabricacion_id: ID de la fabricación

        Returns:
            True si se asignó correctamente, False si no
        """
        return self.tracking_repo.asignar_trabajador_a_fabricacion(
            trabajador_id=trabajador_id,
            fabricacion_id=fabricacion_id
        )

    def obtener_trabajos_activos(
            self,
            trabajador_id: Optional[int] = None,
            fabricacion_id: Optional[int] = None
    ):
        """
        [NUEVO] Obtiene todos los trabajos activos.

        Args:
            trabajador_id: Filtrar por trabajador (opcional)
            fabricacion_id: Filtrar por fabricación (opcional)

        Returns:
            Lista de TrabajoLog activos
        """
        return self.tracking_repo.obtener_trabajos_activos(
            trabajador_id=trabajador_id,
            fabricacion_id=fabricacion_id
        )

    def obtener_estadisticas_trabajador(
            self,
            trabajador_id: int,
            fecha_inicio: Optional[datetime] = None,
            fecha_fin: Optional[datetime] = None
    ):
        """
        [NUEVO] Obtiene estadísticas de productividad de un trabajador.

        Args:
            trabajador_id: ID del trabajador
            fecha_inicio: Fecha de inicio del periodo (opcional)
            fecha_fin: Fecha de fin del periodo (opcional)

        Returns:
            Diccionario con estadísticas
        """
        return self.tracking_repo.obtener_estadisticas_trabajador(
            trabajador_id=trabajador_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

    def obtener_estadisticas_fabricacion(self, fabricacion_id: int):
        """
        [NUEVO] Obtiene estadísticas de una fabricación.

        Args:
            fabricacion_id: ID de la fabricación

        Returns:
            Diccionario con estadísticas
        """
        return self.tracking_repo.obtener_estadisticas_fabricacion(
            fabricacion_id=fabricacion_id
        )

    # NOTA: El método close() principal está en línea 109 (más completo)
    # Se eliminó el duplicado que estaba aquí para evitar sombreado


    def _verify_database_integrity(self):
        """Verifica la integridad bÃ¡sica de la base de datos."""
        try:
            if not self.conn:
                return False

            # Verificar que las tablas principales existen
            essential_tables = ['productos', 'trabajadores', 'maquinas', 'configuracion']
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in self.cursor.fetchall()]

            missing_tables = [table for table in essential_tables if table not in existing_tables]
            if missing_tables:
                self.logger.warning(f"Tablas faltantes detectadas: {missing_tables}")
                return False

            self.logger.info("VerificaciÃ³n de integridad de BD completada correctamente.")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Error en verificaciÃ³n de integridad: {e}")
            return False

    def test_all_repositories(self):
        """MÃ©todo temporal para probar todos los repositorios"""
        from .repositories import ProductRepository, WorkerRepository, MachineRepository, PilaRepository

        results = {}

        # Test ProductRepository
        try:
            product_repo = ProductRepository(self.SessionLocal)
            products = product_repo.get_all_products()
            results['products'] = len(products)
            self.logger.info(f"ProductRepository: {len(products)} productos")
        except Exception as e:
            results['products'] = f"ERROR: {e}"
            self.logger.error(f"Error en ProductRepository: {e}")

        # Test WorkerRepository
        try:
            worker_repo = WorkerRepository(self.SessionLocal)
            workers = worker_repo.get_all_workers()
            results['workers'] = len(workers)
            self.logger.info(f"WorkerRepository: {len(workers)} trabajadores")
        except Exception as e:
            results['workers'] = f"ERROR: {e}"
            self.logger.error(f"Error en WorkerRepository: {e}")

        # Test MachineRepository
        try:
            machine_repo = MachineRepository(self.SessionLocal)
            machines = machine_repo.get_all_machines()
            results['machines'] = len(machines)
            self.logger.info(f"MachineRepository: {len(machines)} mÃ¡quinas")
        except Exception as e:
            results['machines'] = f"ERROR: {e}"
            self.logger.error(f"Error en MachineRepository: {e}")

        # Test PilaRepository (este puede fallar si no tienes pilas_db integrado aÃºn)
        try:
            pila_repo = PilaRepository(self.SessionLocal)
            pilas = pila_repo.get_all_pilas()
            results['pilas'] = len(pilas)
            self.logger.info(f"PilaRepository: {len(pilas)} pilas")
        except Exception as e:
            results['pilas'] = f"ERROR: {e}"
            self.logger.error(f"Error en PilaRepository: {e}")

        return results

    def create_preprocesos_tables_if_not_exist(self):
        """
        Crea las tablas de preprocesos y fabricaciones si no existen.
        Este mÃ©todo debe ejecutarse en la inicializaciÃ³n para asegurar
        que las nuevas tablas estÃ©n disponibles.
        """
        try:
            # Verificar y crear tabla fabricaciones
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                descripcion TEXT
            )
            """)

            # Verificar y crear tabla preprocesos
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preprocesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT
            )
            """)

            # Verificar y crear tabla de enlace preproceso-material
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preproceso_material_link (
                preproceso_id INTEGER,
                material_id INTEGER,
                PRIMARY KEY (preproceso_id, material_id),
                FOREIGN KEY (preproceso_id) REFERENCES preprocesos (id) ON DELETE CASCADE,
                FOREIGN KEY (material_id) REFERENCES materiales (id) ON DELETE CASCADE
            )
            """)

            # Verificar y crear tabla de enlace fabricacion-preproceso
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fabricacion_preproceso_link (
                fabricacion_id INTEGER,
                preproceso_id INTEGER,
                PRIMARY KEY (fabricacion_id, preproceso_id),
                FOREIGN KEY (fabricacion_id) REFERENCES fabricaciones (id) ON DELETE CASCADE,
                FOREIGN KEY (preproceso_id) REFERENCES preprocesos (id) ON DELETE CASCADE
            )
            """)

            self.conn.commit()
            self.logger.info("Tablas de preprocesos y fabricaciones verificadas/creadas exitosamente.")

            # Insertar datos de ejemplo si las tablas estÃ¡n vacÃ­as
            self._insert_sample_fabricaciones_if_empty()

        except sqlite3.Error as e:
            self.logger.error(f"Error creando tablas de preprocesos: {e}")
            if self.conn:
                self.conn.rollback()

    def _insert_sample_fabricaciones_if_empty(self):
        """Inserta fabricaciones de ejemplo si la tabla estÃ¡ vacÃ­a."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM fabricaciones")
            count = self.cursor.fetchone()[0]

            if count == 0:
                # Insertar fabricaciones de ejemplo
                sample_fabricaciones = [
                    ("FAB-001", "FabricaciÃ³n de Prueba 1"),
                    ("FAB-002", "FabricaciÃ³n de Prueba 2"),
                    ("FAB-DEMO", "FabricaciÃ³n DemostraciÃ³n"),
                ]

                for codigo, descripcion in sample_fabricaciones:
                    self.cursor.execute(
                        "INSERT INTO fabricaciones (codigo, descripcion) VALUES (?, ?)",
                        (codigo, descripcion)
                    )

                self.conn.commit()
                self.logger.info(f"Insertadas {len(sample_fabricaciones)} fabricaciones de ejemplo.")

        except sqlite3.Error as e:
            self.logger.error(f"Error insertando fabricaciones de ejemplo: {e}")

