# repositories/machine_repository.py
"""
Repositorio para la gestión de máquinas.
Mantiene compatibilidad exacta con los métodos existentes en database_manager.py
"""

from typing import List, Tuple, Optional, Dict, Any, Union
from datetime import date
from sqlalchemy.exc import IntegrityError

from .base import BaseRepository
from ..models import Maquina, MachineMaintenanc, GrupoPreparacion, PreparacionPaso
from core.dtos import MachineDTO, MachineMaintenanceDTO, PreparationGroupDTO, PreparationStepDTO


class MachineRepository(BaseRepository):
    """
    Repositorio para la gestión de máquinas.
    Replica exactamente la interfaz de los métodos de máquinas en database_manager.py
    """

    def get_all_machines(self, include_inactive: bool = False) -> List[MachineDTO]:
        """
        Obtiene una lista de todas las máquinas.
        Ahora devuelve objetos MachineDTO en lugar de tuplas.

        Args:
            include_inactive: Si incluir máquinas inactivas

        Returns:
            Lista de objetos MachineDTO
        """

        def _operation(session):
            query = session.query(Maquina)
            if not include_inactive:
                query = query.filter(Maquina.activa == True)

            maquinas = query.order_by(Maquina.nombre).all()
            # Mapeo a DTOs
            return [
                MachineDTO(
                    id=m.id,
                    nombre=m.nombre,
                    departamento=m.departamento,
                    tipo_proceso=m.tipo_proceso,
                    activa=bool(m.activa)
                ) for m in maquinas
            ]

        return self.safe_execute(_operation) or []

    def get_latest_machines(self, limit: int = 10) -> List[MachineDTO]:
        """
        Obtiene las últimas máquinas añadidas.
        Devuelve objetos MachineDTO.

        Args:
            limit: Número máximo de máquinas a devolver

        Returns:
            Lista de objetos MachineDTO
        """

        def _operation(session):
            maquinas = session.query(Maquina) \
                .order_by(Maquina.id.desc()) \
                .limit(limit).all()
            return [
                MachineDTO(
                    id=m.id,
                    nombre=m.nombre,
                    departamento=m.departamento,
                    tipo_proceso=m.tipo_proceso,
                    activa=bool(m.activa)
                ) for m in maquinas
            ]

        return self.safe_execute(_operation) or []

    def get_machines_by_process_type(self, tipo_proceso: str) -> List[MachineDTO]:
        """
        Obtiene máquinas activas para un tipo de proceso específico.
        Devuelve objetos MachineDTO.

        Args:
            tipo_proceso: Tipo de proceso a buscar

        Returns:
            Lista de objetos MachineDTO
        """

        def _operation(session):
            maquinas = session.query(Maquina).filter(
                Maquina.tipo_proceso == tipo_proceso,
                Maquina.activa == True
            ).order_by(Maquina.nombre).all()

            return [
                MachineDTO(
                    id=m.id,
                    nombre=m.nombre,
                    departamento=m.departamento,
                    tipo_proceso=m.tipo_proceso,
                    activa=bool(m.activa)
                ) for m in maquinas
            ]

        return self.safe_execute(_operation) or []

    def get_distinct_machine_processes(self) -> List[str]:
        """
        Obtiene una lista de todos los valores únicos de 'tipo_proceso' de las máquinas.
        Mantiene compatibilidad con: database_manager.get_distinct_machine_processes()

        Returns:
            Lista de tipos de proceso únicos
        """

        def _operation(session):
            result = session.query(Maquina.tipo_proceso).filter(
                Maquina.tipo_proceso.isnot(None),
                Maquina.tipo_proceso != ''
            ).distinct().order_by(Maquina.tipo_proceso).all()

            return [row[0] for row in result]

        return self.safe_execute(_operation) or []

    def add_machine(self, nombre: str, departamento: str, tipo_proceso: str, activa: bool = True,
                    machine_id: Optional[int] = None) -> Union[bool, str]:
        """
        Añade una nueva máquina o actualiza una existente si se proporciona un ID
        o si ya existe una máquina con el mismo nombre.
        Prioriza la actualización por ID si se proporciona.

        Args:
            nombre: Nombre de la máquina.
            departamento: Departamento.
            tipo_proceso: Tipo de proceso.
            activa: Estado de actividad (default True).
            machine_id: ID opcional para buscar y actualizar directamente.

        Returns:
            True si se añadió/actualizó, "UNIQUE_CONSTRAINT" si hay conflicto de nombre al añadir, False si error.
        """

        def _operation(session):
            target_machine = None
            # Prioridad 1: Buscar por ID si se proporciona
            if machine_id is not None:
                target_machine = session.query(Maquina).filter_by(id=machine_id).first()
                if not target_machine:
                    self.logger.warning(
                        f"Se intentó actualizar la máquina con ID {machine_id} pero no se encontró.")
                    # Podríamos decidir crearla, pero es más seguro fallar aquí
                    # return False

            # Prioridad 2: Si no hay ID o no se encontró por ID, buscar por nombre
            if target_machine is None:
                target_machine = session.query(Maquina).filter_by(nombre=nombre).first()

            if target_machine:
                # Actualizar máquina existente
                # Solo actualizamos si el ID coincide o si no se proporcionó ID explícito
                if machine_id is None or target_machine.id == machine_id:
                    target_machine.nombre = nombre  # Redundante si se busca por nombre, pero asegura consistencia
                    target_machine.departamento = departamento
                    target_machine.tipo_proceso = tipo_proceso
                    target_machine.activa = activa
                    self.logger.info(f"Máquina '{nombre}' (ID: {target_machine.id}) actualizada.")
                    return True
                else:
                    # Conflicto: Se proporcionó un ID que no coincide con la máquina encontrada por nombre
                    self.logger.error(
                        f"Conflicto al actualizar máquina: ID {machine_id} no coincide con la máquina '{nombre}' encontrada (ID: {target_machine.id}).")
                    return False  # Error por conflicto
            else:
                # Añadir nueva máquina (solo si no se encontró ni por ID ni por nombre)
                try:
                    nueva_maquina = Maquina(
                        # Si se pasó un ID para una máquina inexistente, lo ignoramos para que se autogenere
                        # id=machine_id if machine_id is not None else None, # Descomentar con precaución
                        nombre=nombre,
                        departamento=departamento,
                        tipo_proceso=tipo_proceso,
                        activa=activa
                    )
                    session.add(nueva_maquina)
                    session.flush()  # Para forzar la verificación de UNIQUE constraint
                    self.logger.info(f"Máquina '{nombre}' añadida con ID {nueva_maquina.id}.")
                    return True
                except IntegrityError:
                    # Captura el error si el nombre es duplicado (concurrencia u otro caso)
                    session.rollback()  # Necesario tras IntegrityError
                    self.logger.warning(
                        f"Error de integridad al añadir máquina '{nombre}', posible duplicado concurrente.")
                    # Intentamos buscarla de nuevo por si se creó justo ahora
                    existing = session.query(Maquina).filter_by(nombre=nombre).first()
                    if existing:
                        self.logger.info(
                            f"La máquina '{nombre}' ya existe (ID: {existing.id}), no se realizaron cambios.")
                        # Podríamos decidir actualizarla aquí si es necesario
                        return True  # Consideramos éxito si ya existe
                    return "UNIQUE_CONSTRAINT"  # Devolver código específico si sigue sin encontrarse

        # safe_execute manejará el commit y rollback general
        result = self.safe_execute(_operation)
        return result if isinstance(result, str) else (result or False)

    def update_machine(self, machine_id: int, nombre: str, departamento: str,
                       tipo_proceso: str, activa: bool) -> bool:
        """
        Actualiza una máquina existente.
        Mantiene compatibilidad con: database_manager.update_machine()

        Args:
            machine_id: ID de la máquina
            nombre: Nuevo nombre
            departamento: Nuevo departamento
            tipo_proceso: Nuevo tipo de proceso
            activa: Estado activa/inactiva

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """

        def _operation(session):
            maquina = session.query(Maquina).filter_by(id=machine_id).first()
            if not maquina:
                return False

            maquina.nombre = nombre
            maquina.departamento = departamento
            maquina.tipo_proceso = tipo_proceso
            maquina.activa = activa

            self.logger.info(f"Máquina ID {machine_id} actualizada a '{nombre}'.")
            return True

        return self.safe_execute(_operation) or False

    def delete_machine(self, machine_id: int) -> bool:
        """
        Elimina una máquina.
        Mantiene compatibilidad con: database_manager.delete_machine()
        
        Args:
            machine_id: ID de la máquina a eliminar
            
        Returns:
            True si se eliminó, False si no existía o error.
        """
        def _operation(session):
            maquina = session.query(Maquina).filter_by(id=machine_id).first()
            if not maquina:
                self.logger.warning(f"No se encontró la máquina ID {machine_id} para eliminar.")
                return False
            
            session.delete(maquina)
            self.logger.info(f"Máquina ID {machine_id} eliminada.")
            return True

        return self.safe_execute(_operation) or False

    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str) -> bool:
        """
        Añade un nuevo registro de mantenimiento para una máquina.
        Mantiene compatibilidad con: database_manager.add_machine_maintenance()

        Args:
            machine_id: ID de la máquina
            maintenance_date: Fecha del mantenimiento
            notes: Notas del mantenimiento

        Returns:
            True si se añadió correctamente, False en caso contrario
        """

        def _operation(session):
            mantenimiento = MachineMaintenanc(
                machine_id=machine_id,
                maintenance_date=maintenance_date,
                notes=notes
            )
            session.add(mantenimiento)
            return True

        return self.safe_execute(_operation) or False

    def get_machine_maintenance_history(self, machine_id: int) -> List[MachineMaintenanceDTO]:
        """
        Obtiene el historial de mantenimientos para una máquina específica.
        Devuelve objetos MachineMaintenanceDTO.

        Args:
            machine_id: ID de la máquina

        Returns:
            Lista de objetos MachineMaintenanceDTO
        """

        def _operation(session):
            mantenimientos = session.query(MachineMaintenanc).filter_by(
                machine_id=machine_id
            ).order_by(MachineMaintenanc.maintenance_date.desc()).all()

            return [
                MachineMaintenanceDTO(
                    maintenance_date=m.maintenance_date,
                    notes=m.notes
                ) for m in mantenimientos
            ]

        return self.safe_execute(_operation) or []

        # --- MÉTODOS PARA GRUPOS Y PASOS DE PREPARACIÓN ---

    def add_prep_group(self, machine_id: int, name: str, description: str,
                       producto_codigo: Optional[str] = None) -> Union[int, str, None]:
        """
        [MIGRADO] Añade un nuevo grupo de preparación a una máquina.
        Mantiene compatibilidad con: database_manager.add_prep_group()
        CORREGIDO: Comprueba duplicados explícitamente antes de insertar.

        Args:
            machine_id: ID de la máquina
            name: Nombre del grupo
            description: Descripción del grupo
            producto_codigo: Código de producto asociado (opcional)

        Returns:
            ID del grupo creado, "UNIQUE_CONSTRAINT" si ya existe, o None si hay otro error.
        """

        def _operation(session):
            from ..models import GrupoPreparacion # Importar modelo aquí

            # Comprobar si ya existe un grupo con el mismo nombre para esta máquina
            existing_group = session.query(GrupoPreparacion).filter_by(
                maquina_id=machine_id,
                nombre=name
            ).first()

            if existing_group:
                self.logger.warning(f"Intento de añadir grupo duplicado '{name}' a máquina {machine_id}. Ya existe.")
                return "UNIQUE_CONSTRAINT" # Devolver el código esperado directamente

            # Si no existe, proceder a crear el nuevo grupo
            nuevo_grupo = GrupoPreparacion(
                maquina_id=machine_id,
                nombre=name,
                descripcion=description,
                producto_codigo=producto_codigo
            )
            session.add(nuevo_grupo)
            # No es estrictamente necesario el flush aquí si el commit se hace fuera,
            # pero lo mantenemos por si acaso y para obtener el ID si es necesario.
            session.flush()
            self.logger.info(f"Grupo de preparación '{name}' añadido a máquina {machine_id} con ID {nuevo_grupo.id}.")
            return nuevo_grupo.id # Devolver el ID si todo va bien

        # No necesitamos el try/except IntegrityError externo ahora,
        # safe_execute manejará otros posibles errores.
        # Si _operation devuelve "UNIQUE_CONSTRAINT", safe_execute lo devolverá tal cual.
        result = self.safe_execute(_operation)
        # Si safe_execute devuelve None (por otro error), devolvemos None.
        # Si devuelve ID o "UNIQUE_CONSTRAINT", lo devolvemos tal cual.
        return result

    def get_groups_for_machine(self, machine_id: int) -> List[PreparationGroupDTO]:
        """
        [MIGRADO] Obtiene todos los grupos de preparación para una máquina específica.
        Devuelve objetos PreparationGroupDTO.

        Args:
            machine_id: ID de la máquina

        Returns:
            Lista de objetos PreparationGroupDTO
        """
        def _operation(session):
            grupos = session.query(GrupoPreparacion).filter_by(
                maquina_id=machine_id
            ).order_by(GrupoPreparacion.nombre).all()

            return [
                PreparationGroupDTO(
                    id=g.id,
                    nombre=g.nombre,
                    descripcion=g.descripcion,
                    producto_codigo=g.producto_codigo
                ) for g in grupos
            ]

        # Usar safe_execute y devolver lista vacía en caso de error
        return self.safe_execute(_operation) or []

    def get_group_details(self, group_id: int) -> Optional[PreparationGroupDTO]:
        """
        Obtiene los detalles de un grupo de preparación.
        Devuelve PreparationGroupDTO.
        """
        def _operation(session):
            from ..models import GrupoPreparacion
            g = session.query(GrupoPreparacion).filter_by(id=group_id).first()
            if not g:
                return None
            return PreparationGroupDTO(
                id=g.id,
                nombre=g.nombre,
                descripcion=g.descripcion,
                producto_codigo=g.producto_codigo
            )
        return self.safe_execute(_operation)

    def update_prep_group(self, group_id: int, name: str, description: str,
                          producto_codigo: Optional[str] = None) -> bool:
        """
        [MIGRADO] Actualiza el nombre, descripción y producto asociado de un grupo de preparación.
        Mantiene compatibilidad con: database_manager.update_prep_group()

        Args:
            group_id: ID del grupo a actualizar
            name: Nuevo nombre
            description: Nueva descripción
            producto_codigo: Nuevo código de producto asociado (o None para quitarlo)

        Returns:
            True si se actualizó correctamente, False si no se encontró o hubo error.
        """

        def _operation(session):
            from ..models import GrupoPreparacion  # Importar modelo

            grupo = session.query(GrupoPreparacion).filter_by(id=group_id).first()

            if not grupo:
                self.logger.warning(f"No se encontró el grupo de preparación con ID {group_id} para actualizar.")
                return False  # Grupo no encontrado

            # Actualizar campos
            grupo.nombre = name
            grupo.descripcion = description
            grupo.producto_codigo = producto_codigo  # SQLAlchemy maneja bien el None

            self.logger.info(f"Grupo de preparación ID {group_id} actualizado a nombre '{name}'.")
            return True  # Éxito

        # safe_execute devuelve True o None (o el default si lo cambiamos), así que usamos 'or False'
        return self.safe_execute(_operation) or False

    def add_prep_step(self, group_id: int, name: str, time: float,
                       description: str, is_daily: bool) -> Optional[int]:
        """
        [MIGRADO] Añade un nuevo paso de preparación a un grupo.
        Mantiene compatibilidad con: database_manager.add_prep_step()
        INCLUYE el campo 'es_diario'.

        Args:
            group_id: ID del grupo al que pertenece el paso
            name: Nombre del paso
            time: Tiempo estimado para el paso (en minutos)
            description: Descripción del paso
            is_daily: Booleano que indica si es un paso diario

        Returns:
            ID del paso creado, o None si hay error.
        """
        def _operation(session):
            from ..models import PreparacionPaso # Importar modelo

            nuevo_paso = PreparacionPaso(
                grupo_id=group_id,
                nombre=name,
                tiempo_fase=time,
                descripcion=description,
                es_diario=is_daily # Añadido el campo booleano
            )
            session.add(nuevo_paso)
            session.flush() # Para obtener el ID antes del commit

            self.logger.info(f"Paso de preparación '{name}' añadido al grupo {group_id} con ID {nuevo_paso.id}.")
            return nuevo_paso.id # Devolver el ID

        # safe_execute devuelve el ID o None (valor por defecto en BaseRepository)
        return self.safe_execute(_operation)

    def update_prep_step(self, step_id: int, data: Dict[str, Any]) -> bool:
        """
        [MIGRADO] Actualiza una fase de preparación existente.
        Mantiene compatibilidad con: database_manager.update_prep_step()
        El diccionario 'data' debe contener: 'nombre', 'tiempo_fase', 'descripcion', 'es_diario'.

        Args:
            step_id: ID del paso a actualizar
            data: Diccionario con los nuevos datos del paso

        Returns:
            True si se actualizó, False si no se encontró o hubo error.
        """

        def _operation(session):
            from ..models import PreparacionPaso  # Importar modelo

            paso = session.query(PreparacionPaso).filter_by(id=step_id).first()

            if not paso:
                self.logger.warning(f"No se encontró el paso de preparación ID {step_id} para actualizar.")
                return False  # Paso no encontrado

            # Actualizar campos desde el diccionario 'data'
            # Usar .get() con valor por defecto por si alguna clave falta
            paso.nombre = data.get('nombre', paso.nombre)  # Mantener valor si no viene
            paso.tiempo_fase = data.get('tiempo_fase', paso.tiempo_fase)
            paso.descripcion = data.get('descripcion', paso.descripcion)
            paso.es_diario = data.get('es_diario', paso.es_diario)  # Default es False o el valor actual

            self.logger.info(f"Paso de preparación ID {step_id} actualizado a nombre '{paso.nombre}'.")
            return True  # Éxito

        return self.safe_execute(_operation) or False

    def get_steps_for_group(self, group_id: int) -> List[PreparationStepDTO]:
        """
        [MIGRADO] Obtiene todos los pasos de preparación para un grupo específico.
        Devuelve objetos PreparationStepDTO.

        Args:
            group_id: ID del grupo

        Returns:
            Lista de objetos PreparationStepDTO
        """
        def _operation(session):
            pasos = session.query(PreparacionPaso).filter_by(
                grupo_id=group_id
            ).order_by(PreparacionPaso.id).all() # Ordenar por ID para mantener consistencia

            return [
                PreparationStepDTO(
                    id=p.id,
                    nombre=p.nombre,
                    tiempo_fase=float(p.tiempo_fase),
                    descripcion=p.descripcion,
                    es_diario=bool(p.es_diario)
                ) for p in pasos
            ]

        return self.safe_execute(_operation) or []

    def delete_prep_group(self, group_id: int) -> bool:
        """
        [MIGRADO] Elimina un grupo de preparación (y sus pasos asociados gracias a ON DELETE CASCADE).
        Mantiene compatibilidad con: database_manager.delete_prep_group()

        Args:
            group_id: ID del grupo a eliminar

        Returns:
            True si se eliminó correctamente, False si no se encontró o hubo error.
        """
        def _operation(session):
            from ..models import GrupoPreparacion # Importar modelo

            grupo = session.query(GrupoPreparacion).filter_by(id=group_id).first()

            if not grupo:
                self.logger.warning(f"No se encontró el grupo de preparación con ID {group_id} para eliminar.")
                return False # Grupo no encontrado

            # Eliminar el grupo. SQLAlchemy y la configuración CASCADE en el modelo
            # se encargarán de eliminar los pasos asociados.
            session.delete(grupo)
            self.logger.info(f"Grupo de preparación ID {group_id} ('{grupo.nombre}') marcado para eliminación (pasos asociados también).")
            return True # Éxito

        # safe_execute devuelve True o None, usamos 'or False'
        return self.safe_execute(_operation) or False

    def get_machine_usage_stats(self) -> List[Tuple[str, float]]:
        """ Calcula el tiempo total de uso (en minutos) para cada máquina. """

        def _operation(session):
            from ..models import Subfabricacion
            from sqlalchemy import func

            # ESTA ES LA CONSULTA CORRECTA QUE UNE POR ID NUMÉRICO
            result = session.query(
                Maquina.nombre,
                func.sum(Subfabricacion.tiempo).label('total_minutos')
            ).join(
                Subfabricacion, Maquina.id == Subfabricacion.maquina_id  # Une por ID
            ).group_by(
                Maquina.nombre
            ).order_by(
                func.sum(Subfabricacion.tiempo).desc()
            ).all()
            return [(row.nombre, float(row.total_minutos)) for row in result]

        return self.safe_execute(_operation) or []

    def delete_prep_step(self, step_id: int) -> bool:
        """
        [MIGRADO] Elimina un paso de preparación.
        Mantiene compatibilidad con: database_manager.delete_prep_step()

        Args:
            step_id: ID del paso a eliminar

        Returns:
            True si se eliminó correctamente, False si no se encontró o hubo error.
        """

        def _operation(session):
            from ..models import PreparacionPaso  # Importar modelo

            paso = session.query(PreparacionPaso).filter_by(id=step_id).first()

            if not paso:
                self.logger.warning(f"No se encontró el paso de preparación ID {step_id} para eliminar.")
                return False  # Paso no encontrado

            # Eliminar el paso
            session.delete(paso)
            self.logger.info(f"Paso de preparación ID {step_id} ('{paso.nombre}') marcado para eliminación.")
            return True  # Éxito

        return self.safe_execute(_operation) or False