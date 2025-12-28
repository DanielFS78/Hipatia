# repositories/worker_repository.py
"""
Repositorio para la gestión de trabajadores.
Migrado a DTOs para eliminar el uso de tuplas crudas.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from .base import BaseRepository
from ..models import Trabajador
from core.dtos import WorkerDTO, WorkerAnnotationDTO


class WorkerRepository(BaseRepository):
    """
    Repositorio para la gestión de trabajadores.
    Replica exactamente la interfaz de los métodos de trabajadores en database_manager.py
    """

    def get_all_workers(self, include_inactive: bool = False) -> List[WorkerDTO]:
        """
        Obtiene una lista de todos los trabajadores.

        Args:
            include_inactive: Si incluir trabajadores inactivos

        Returns:
            Lista de WorkerDTO con los datos de cada trabajador
        """

        def _operation(session):
            query = session.query(Trabajador)
            if not include_inactive:
                query = query.filter(Trabajador.activo == True)

            trabajadores = query.order_by(Trabajador.nombre_completo).all()
            return [
                WorkerDTO(
                    id=t.id,
                    nombre_completo=t.nombre_completo,
                    activo=bool(t.activo),
                    notas=t.notas or "",
                    tipo_trabajador=t.tipo_trabajador
                ) for t in trabajadores
            ]

        return self.safe_execute(_operation) or []

    def get_worker_annotations(self, worker_id: int) -> List[WorkerAnnotationDTO]:
        """
        Obtiene todas las anotaciones para un trabajador específico, ordenadas por fecha descendente.

        Args:
            worker_id: ID del trabajador.

        Returns:
            Lista de WorkerAnnotationDTO con las anotaciones.
        """

        def _operation(session):
            from ..models import TrabajadorPilaAnotacion

            anotaciones = session.query(TrabajadorPilaAnotacion).filter_by(
                worker_id=worker_id
            ).order_by(
                TrabajadorPilaAnotacion.fecha.desc()
            ).all()

            return [
                WorkerAnnotationDTO(
                    pila_id=a.pila_id,
                    fecha=a.fecha,
                    anotacion=a.anotacion
                ) for a in anotaciones
            ]

        return self.safe_execute(_operation) or []

    def get_latest_workers(self, limit: int = 10) -> List[WorkerDTO]:
        """
        Obtiene los últimos trabajadores añadidos.

        Args:
            limit: Número máximo de trabajadores a devolver

        Returns:
            Lista de WorkerDTO con los trabajadores más recientes
        """

        def _operation(session):
            trabajadores = session.query(Trabajador) \
                .order_by(Trabajador.id.desc()) \
                .limit(limit).all()
            return [
                WorkerDTO(
                    id=t.id,
                    nombre_completo=t.nombre_completo,
                    activo=bool(t.activo),
                    notas=t.notas or "",
                    tipo_trabajador=t.tipo_trabajador
                ) for t in trabajadores
            ]

        return self.safe_execute(_operation) or []

    def get_worker_details(self, worker_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de un trabajador específico por su ID.
        Mantiene compatibilidad con: database_manager.get_worker_details()

        CORREGIDO: Devuelve un diccionario en lugar de una tupla e incluye
                   los campos de usuario.

        Args:
            worker_id: ID del trabajador

        Returns:
            Diccionario con los datos del trabajador o None si no existe
        """

        def _operation(session):
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return None

            # Convertir a diccionario
            return {
                "id": trabajador.id,
                "nombre_completo": trabajador.nombre_completo,
                "activo": trabajador.activo,
                "notas": trabajador.notas,
                "tipo_trabajador": trabajador.tipo_trabajador,
                "username": trabajador.username,
                "role": trabajador.role
                # No incluimos el password_hash por seguridad
            }

        return self.safe_execute(_operation)

    def add_worker(self, nombre_completo: str, notas: str = "", tipo_trabajador: int = 1, activo: bool = True,
                    worker_id: Optional[int] = None, username: Optional[str] = None,
                    password_hash: Optional[str] = None, role: Optional[str] = None) -> Union[bool, str]:
        """
        Añade un nuevo trabajador o actualiza uno existente si se proporciona un ID
        o si ya existe un trabajador con el mismo nombre_completo.
        Prioriza la actualización por ID si se proporciona.

        Args:
            nombre_completo: Nombre completo.
            notas: Notas.
            tipo_trabajador: Nivel de habilidad.
            activo: Estado.
            worker_id: ID opcional para buscar y actualizar.
            username: Nombre de usuario opcional.
            password_hash: Hash de contraseña opcional.
            role: Rol opcional.

        Returns:
            True si se añadió/actualizó, "UNIQUE_CONSTRAINT" si hay conflicto de nombre al añadir, False si error.
        """

        def _operation(session):
            target_worker = None
            # Prioridad 1: Buscar por ID si se proporciona
            if worker_id is not None:
                target_worker = session.query(Trabajador).filter_by(id=worker_id).first()
                if not target_worker:
                    self.logger.warning(f"Se intentó actualizar trabajador ID {worker_id} pero no se encontró.")
                    # Decidimos no crearlo si el ID no existe para evitar IDs inesperados
                    # return False

            # Prioridad 2: Si no hay ID o no se encontró, buscar por nombre_completo
            if target_worker is None:
                target_worker = session.query(Trabajador).filter_by(nombre_completo=nombre_completo).first()

            if target_worker:
                # Actualizar trabajador existente
                # Solo si el ID coincide o si no se pasó ID explícito
                if worker_id is None or target_worker.id == worker_id:
                    target_worker.nombre_completo = nombre_completo  # Redundante si se busca por nombre
                    target_worker.notas = notas
                    target_worker.tipo_trabajador = tipo_trabajador
                    target_worker.activo = activo
                    # Actualizar credenciales solo si se proporcionan
                    if username is not None: target_worker.username = username
                    if password_hash is not None: target_worker.password_hash = password_hash
                    if role is not None: target_worker.role = role
                    self.logger.info(f"Trabajador '{nombre_completo}' (ID: {target_worker.id}) actualizado.")
                    return True
                else:
                    # Conflicto: ID proporcionado no coincide con el encontrado por nombre
                    self.logger.error(
                        f"Conflicto al actualizar trabajador: ID {worker_id} no coincide con el trabajador '{nombre_completo}' encontrado (ID: {target_worker.id}).")
                    return False  # Error por conflicto
            else:
                # Añadir nuevo trabajador
                try:
                    nuevo_trabajador = Trabajador(
                        nombre_completo=nombre_completo,
                        notas=notas,
                        tipo_trabajador=tipo_trabajador,
                        activo=activo,
                        username=username,
                        password_hash=password_hash,
                        role=role
                    )
                    session.add(nuevo_trabajador)
                    session.flush()  # Forzar verificación UNIQUE
                    self.logger.info(f"Trabajador '{nombre_completo}' añadido con ID {nuevo_trabajador.id}.")
                    return True
                except IntegrityError:
                    session.rollback()  # Necesario tras IntegrityError
                    self.logger.warning(
                        f"Error de integridad al añadir trabajador '{nombre_completo}', posible duplicado (nombre o username).")
                    # Podríamos intentar buscarlo de nuevo aquí si fuera necesario
                    return "UNIQUE_CONSTRAINT"

        # safe_execute maneja commit/rollback general
        result = self.safe_execute(_operation)
        return result if isinstance(result, str) else (result or False)

    def add_worker_annotation(self, worker_id: int, pila_id: int, annotation: str) -> bool:
        """
        Añade una nueva anotación para un trabajador asociada a una pila específica.
        Mantiene compatibilidad con database_manager.add_worker_annotation().

        Args:
            worker_id: ID del trabajador.
            pila_id: ID de la pila relacionada con la anotación.
            annotation: El texto de la anotación.

        Returns:
            True si la anotación se añadió correctamente, False en caso contrario.
        """

        def _operation(session):
            from ..models import TrabajadorPilaAnotacion  # Importar el modelo aquí
            from datetime import datetime  # Asegurarse de importar datetime

            # Verificar si el trabajador y la pila existen (opcional pero recomendado)
            # worker = session.query(Trabajador).filter_by(id=worker_id).first()
            # pila = session.query(Pila).filter_by(id=pila_id).first()
            # if not worker or not pila:
            #     self.logger.warning(f"No se encontró trabajador ID {worker_id} o pila ID {pila_id} al añadir anotación.")
            #     return False

            nueva_anotacion = TrabajadorPilaAnotacion(
                worker_id=worker_id,
                pila_id=pila_id,
                anotacion=annotation
                # La fecha se establece por defecto en el modelo (default=lambda: datetime.now(datetime.UTC))
            )
            session.add(nueva_anotacion)
            self.logger.info(f"Anotación añadida para trabajador ID {worker_id} en pila ID {pila_id}.")
            return True

        # safe_execute devuelve True o None (o el default), usamos 'or False'
        return self.safe_execute(_operation) or False

    def update_worker(self, worker_id: int, nombre_completo: str, activo: bool, notas: str,
                      tipo_trabajador: int) -> bool:
        """
        Actualiza los datos de un trabajador existente.
        Mantiene compatibilidad con: database_manager.update_worker()

        Args:
            worker_id: ID del trabajador
            nombre_completo: Nuevo nombre completo
            activo: Estado activo/inactivo
            notas: Nuevas notas
            tipo_trabajador: Nuevo nivel de habilidad

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """

        def _operation(session):
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            trabajador.nombre_completo = nombre_completo
            trabajador.activo = activo
            trabajador.notas = notas
            trabajador.tipo_trabajador = tipo_trabajador

            self.logger.info(f"Trabajador ID {worker_id} actualizado a '{nombre_completo}'.")
            return True

        return self.safe_execute(_operation) or False

    def delete_worker(self, worker_id: int) -> bool:
        """
        Elimina un trabajador de la base de datos.
        Mantiene compatibilidad con: database_manager.delete_worker()

        Args:
            worker_id: ID del trabajador a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """

        def _operation(session):
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            session.delete(trabajador)
            self.logger.info(f"Trabajador ID {worker_id} eliminado con éxito.")
            return True

        return self.safe_execute(_operation) or False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verifica las credenciales de un usuario y devuelve sus datos si son correctas.
        Mantiene compatibilidad con: database_manager.authenticate_user()

        Args:
            username: Nombre de usuario
            password: Contraseña (será hasheada)

        Returns:
            Diccionario con datos del usuario o None si las credenciales son incorrectas
        """

        def _operation(session):
            import hashlib
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

            trabajador = session.query(Trabajador).filter(
                Trabajador.username == username,
                Trabajador.password_hash == password_hash
            ).first()

            if trabajador:
                return {
                    "id": trabajador.id,
                    "nombre": trabajador.nombre_completo,
                    "role": trabajador.role,
                    "activo": trabajador.activo
                }
            return None

        return self.safe_execute(_operation)

    def update_user_credentials(self, worker_id: int, username: str, password: str, role: str) -> bool:
        """
        Actualiza los datos de login de un trabajador.
        Mantiene compatibilidad con: database_manager.update_user_credentials()

        Args:
            worker_id: ID del trabajador
            username: Nuevo nombre de usuario
            password: Nueva contraseña (vacía para no cambiar)
            role: Nuevo rol

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """

        def _operation(session):
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            trabajador.username = username
            trabajador.role = role

            if password:  # Solo hashear y actualizar si no está vacía
                import hashlib
                password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                trabajador.password_hash = password_hash

            return True

        return self.safe_execute(_operation) or False

    def update_user_password(self, worker_id: int, password: str) -> bool:
        """
        Actualiza únicamente la contraseña de un trabajador.
        Mantiene compatibilidad con: database_manager.update_user_password()

        Args:
            worker_id: ID del trabajador
            password: Nueva contraseña

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """

        def _operation(session):
            trabajador = session.query(Trabajador).filter_by(id=worker_id).first()
            if not trabajador:
                return False

            import hashlib
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            trabajador.password_hash = password_hash

            self.logger.info(f"Contraseña actualizada para el trabajador ID {worker_id}.")
            return True

        return self.safe_execute(_operation) or False