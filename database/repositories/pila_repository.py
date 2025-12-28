# repositories/pila_repository.py
"""
Repositorio para la gestión de pilas de producción.
Mantiene compatibilidad exacta con los métodos existentes en pilas_database_manager.py
"""

from typing import List, Tuple, Optional, Dict, Any, Union
import json
import uuid
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

from .base import BaseRepository
from pila_serializer import PilaJSONEncoder, decode_pila_json
from ..models import Pila, PasoPila, DiarioBitacora, EntradaDiario
from core.dtos import PilaDTO


class PilaRepository(BaseRepository):
    """
    Repositorio para la gestión de pilas de producción.
    Replica exactamente la interfaz de los métodos en pilas_database_manager.py
    """

    def get_all_pilas(self) -> List[PilaDTO]:
        """
        Obtiene una lista de todas las pilas guardadas.
        Mantiene compatibilidad con: pilas_database_manager.get_all_pilas()

        Returns:
            Lista de objetos PilaDTO
        """

        def _operation(session):
            pilas = session.query(Pila).order_by(Pila.nombre).all()
            return [
                PilaDTO(
                    id=p.id,
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    producto_origen_codigo=p.producto_origen_codigo
                ) for p in pilas
            ]

        return self.safe_execute(_operation) or []

    def search_pilas(self, query: str) -> List[PilaDTO]:
        """
        Busca pilas por nombre o descripción.
        Mantiene compatibilidad con: pilas_database_manager.search_pilas()

        Args:
            query: Término de búsqueda

        Returns:
            Lista de objetos PilaDTO
        """

        def _operation(session):
            from sqlalchemy import or_
            pilas = session.query(Pila).filter(
                or_(
                    Pila.nombre.like(f"%{query}%"),
                    Pila.descripcion.like(f"%{query}%")
                )
            ).all()
            return [
                PilaDTO(
                    id=p.id,
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    producto_origen_codigo=p.producto_origen_codigo
                ) for p in pilas
            ]

        return self.safe_execute(_operation) or []

    def find_pilas_by_producto_codigo(self, producto_codigo: str) -> List[PilaDTO]:
        """
        Busca todas las pilas asociadas a un código de producto de origen.
        Mantiene compatibilidad con: pilas_database_manager.find_pilas_by_producto_codigo()

        Args:
            producto_codigo: Código del producto de origen

        Returns:
            Lista de objetos PilaDTO
        """

        def _operation(session):
            pilas = session.query(Pila).filter_by(
                producto_origen_codigo=producto_codigo
            ).order_by(Pila.fecha_creacion.desc()).all()

            return [
                PilaDTO(
                    id=p.id,
                    nombre=p.nombre,
                    descripcion=p.descripcion or "",
                    producto_origen_codigo=p.producto_origen_codigo
                ) for p in pilas
            ]

        return self.safe_execute(_operation) or []

    def find_pila_by_name(self, nombre: str) -> Optional[int]:
        """
        Busca una pila por su nombre y devuelve su ID si la encuentra.
        Mantiene compatibilidad con: pilas_database_manager.find_pila_by_name()

        Args:
            nombre: Nombre de la pila

        Returns:
            ID de la pila o None si no existe
        """

        def _operation(session):
            pila = session.query(Pila).filter_by(nombre=nombre).first()
            return pila.id if pila else None

        return self.safe_execute(_operation)

    def _convert_indices_to_ids(self, production_flow: List[Dict]) -> None:
        """
        Prepara el production_flow para ser guardado.
        Asigna un 'unique_id' a cada paso y convierte índices
        (previous_task_index, next_cyclic_task_index) a IDs persistentes.
        """
        # Asegurarnos de que uuid esté importado
        import uuid  # <-- Añadir si no está ya importado al inicio del archivo

        # Primero, asigna un ID único a cada paso y crea un mapa de índice a ID.
        index_to_id_map = {}
        for i, step in enumerate(production_flow):
            # Si un paso ya tiene un ID (puede venir de una carga previa), lo respeta.
            # Si no, crea uno nuevo.
            if 'unique_id' not in step or not step['unique_id']:
                step['unique_id'] = str(uuid.uuid4())
            index_to_id_map[i] = step['unique_id']

        # Segundo, convierte los índices de dependencia a IDs únicos.
        for step in production_flow:
            # Convertir dependencia normal
            if 'previous_task_index' in step and step['previous_task_index'] is not None:
                prev_index = step.get('previous_task_index')
                if prev_index in index_to_id_map:
                    step['previous_task_id'] = index_to_id_map[prev_index]
                # Eliminamos la clave antigua para no guardarla
                del step['previous_task_index']

            # >>> INICIO: NUEVA LÓGICA PARA CICLOS <<<
            if 'next_cyclic_task_index' in step and step['next_cyclic_task_index'] is not None:
                next_idx = step.get('next_cyclic_task_index')
                if next_idx in index_to_id_map:
                    step['next_cyclic_task_id'] = index_to_id_map[next_idx]  # Guardamos el ID
                # Eliminamos la clave antigua del índice
                del step['next_cyclic_task_index']


    def _convert_ids_to_indices(self, production_flow: List[Dict]) -> None:
        """
        Procesa el production_flow después de cargarlo de la BD.
        Reconstruye índices (previous_task_index, next_cyclic_task_index)
        a partir de IDs persistentes y limpia los IDs.
        """
        # Crear un mapa de ID único a su nuevo índice en la lista cargada.
        # Es crucial que cada 'step' tenga un 'unique_id' al cargarlo.
        id_to_index_map = {step.get('unique_id'): i
                            for i, step in enumerate(production_flow)
                            if step.get('unique_id')}

        # Reconstruir índices y limpiar IDs
        for step in production_flow:
            # Reconstruir índice de dependencia normal
            if 'previous_task_id' in step and step['previous_task_id'] is not None:
                prev_id = step.get('previous_task_id')
                step['previous_task_index'] = id_to_index_map.get(prev_id, None)  # Usa get con default None
                # Limpiar ID persistente
                del step['previous_task_id']

            # >>> INICIO: NUEVA LÓGICA PARA CICLOS <<<
            if 'next_cyclic_task_id' in step and step['next_cyclic_task_id'] is not None:
                next_id = step.get('next_cyclic_task_id')
                step['next_cyclic_task_index'] = id_to_index_map.get(next_id, None)  # Usa get con default None
                # Limpiar ID persistente
                del step['next_cyclic_task_id']
            # >>> FIN: NUEVA LÓGICA PARA CICLOS <<<

            # Limpiamos el ID único ya que no se usa directamente en la UI
            if 'unique_id' in step:
                del step['unique_id']

    def save_pila(self, nombre: str, descripcion: str, pila_de_calculo: dict, production_flow: list,
                    simulation_results: list, producto_origen_codigo=None) -> Union[int, str, bool]:
        """
        Guarda una pila de producción completa en la base de datos.
        Usa PilaJSONEncoder para un guardado robusto y mantiene la lógica de IDs únicos.

        Args:
            nombre: Nombre de la pila
            descripcion: Descripción de la pila
            pila_de_calculo: Diccionario con la pila de cálculo (puede incluir 'unidades')
            production_flow: Lista de pasos del flujo de producción (con índices)
            simulation_results: Resultados de la simulación
            producto_origen_codigo: Código del producto origen (opcional)

        Returns:
            ID de la pila guardada, "UNIQUE_CONSTRAINT" si el nombre ya existe, o False si error
        """

        def _operation(session):
            # 1. Verificar si ya existe una pila con ese nombre
            existing_pila = session.query(Pila).filter_by(nombre=nombre).first()
            if existing_pila:
                self.logger.warning(f"Ya existe una pila con el nombre '{nombre}'.")
                return "UNIQUE_CONSTRAINT"

            # 2. Hacer una copia profunda del production_flow para no modificar el original
            import copy
            production_flow_copy = copy.deepcopy(production_flow)

            # 3. Convertir índices de dependencia (previous, cyclic) a IDs únicos persistentes
            #    Esta función ya asigna 'unique_id' y limpia los índices.
            self._convert_indices_to_ids(production_flow_copy)

            # 4. Limpiar IDs temporales del canvas de los datos de la tarea
            for step in production_flow_copy:
                task_data = step.get('task', {})
                if 'canvas_unique_id' in task_data:
                    del task_data['canvas_unique_id']
                if 'original_task_id' in task_data:
                    if 'id' not in task_data:
                        task_data['id'] = task_data['original_task_id']
                    del task_data['original_task_id']

            # 5. Serializar pila_de_calculo (YA NO es necesario copiar ni convertir fechas)

            # 6. Serializar simulation_results (YA NO es necesario copiar ni convertir fechas)

            # 7. Crear la entrada principal de la pila
            # ⚠️ CAMBIO: Usamos cls=PilaJSONEncoder en lugar de default=str
            nueva_pila = Pila(
                nombre=nombre,
                descripcion=descripcion,
                pila_de_calculo_json=json.dumps(pila_de_calculo, ensure_ascii=False, cls=PilaJSONEncoder),
                resultados_simulacion=json.dumps(simulation_results, ensure_ascii=False,
                                                    cls=PilaJSONEncoder) if simulation_results else None,
                producto_origen_codigo=producto_origen_codigo,
                fecha_creacion=datetime.now()
            )

            session.add(nueva_pila)
            session.flush()

            # 8. Guardar cada paso del flujo de producción con datos serializados
            for orden, step in enumerate(production_flow_copy):
                # YA NO es necesario convertir 'start_date' manualmente

                # ⚠️ CAMBIO: Usamos cls=PilaJSONEncoder en lugar de default=str
                paso_pila = PasoPila(
                    pila_id=nueva_pila.id,
                    orden=orden,
                    # Guardamos el paso ya procesado (con IDs únicos y sin IDs temporales)
                    datos_paso=json.dumps(step, ensure_ascii=False, cls=PilaJSONEncoder)
                )
                session.add(paso_pila)

            self.logger.info(
                f"✅ Pila '{nombre}' guardada con serializador robusto. ID {nueva_pila.id}, "
                f"{len(production_flow_copy)} pasos y "
                f"{len(simulation_results)} resultados."
            )

            return nueva_pila.id

        return self.safe_execute(_operation) or False

    def update_pila(self, pila_id: int, nombre: str = None, descripcion: str = None, 
                    pila_de_calculo: dict = None, production_flow: list = None,
                    simulation_results: list = None) -> bool:
        """
        Actualiza una pila existente.
        """
        def _operation(session):
            pila = session.query(Pila).filter_by(id=pila_id).first()
            if not pila:
                self.logger.warning(f"No se encontró pila con ID {pila_id} para actualizar.")
                return False

            if nombre:
                # Check uniqueness if name changed
                if nombre != pila.nombre:
                    existing = session.query(Pila).filter_by(nombre=nombre).first()
                    if existing:
                        return "UNIQUE_CONSTRAINT"
                pila.nombre = nombre
            
            if descripcion is not None:
                pila.descripcion = descripcion
            
            if pila_de_calculo is not None:
                pila.pila_de_calculo_json = json.dumps(pila_de_calculo, ensure_ascii=False, cls=PilaJSONEncoder)
                
            if simulation_results is not None:
                pila.resultados_simulacion = json.dumps(simulation_results, ensure_ascii=False, cls=PilaJSONEncoder)
            
            if production_flow is not None:
                # Replace steps
                session.query(PasoPila).filter_by(pila_id=pila_id).delete()
                
                import copy
                flow_copy = copy.deepcopy(production_flow)
                self._convert_indices_to_ids(flow_copy)
                
                # Cleanup temporary keys
                for step in flow_copy:
                    task_data = step.get('task', {})
                    if 'canvas_unique_id' in task_data: del task_data['canvas_unique_id']
                    if 'original_task_id' in task_data:
                        if 'id' not in task_data: task_data['id'] = task_data['original_task_id']
                        del task_data['original_task_id']

                for orden, step in enumerate(flow_copy):
                    paso = PasoPila(
                        pila_id=pila_id,
                        orden=orden,
                        datos_paso=json.dumps(step, ensure_ascii=False, cls=PilaJSONEncoder)
                    )
                    session.add(paso)
            
            session.commit()
            return True

        return self.safe_execute(_operation)
    def load_pila(self, pila_id: int) -> Tuple[Optional[Dict], Optional[Dict], Optional[List], Optional[List]]:
        """
        Carga una pila de producción desde la BD, deserializando los pasos,
        resultados y reconstruyendo los índices de dependencia para el editor visual.
        Usa decode_pila_json para una carga robusta.
        """

        def _operation(session):
            pila = session.query(Pila).filter_by(id=pila_id).first()
            if not pila:
                self.logger.warning(f"No se encontró la pila con ID {pila_id}.")
                return None, None, None, None

            # 1. Deserializar la pila de cálculo base
            # ⚠️ CAMBIO: Usamos object_hook=decode_pila_json
            pila_de_calculo = {}
            unidades = 1  # Valor por defecto

            if pila.pila_de_calculo_json:
                try:
                    pila_de_calculo = json.loads(pila.pila_de_calculo_json, object_hook=decode_pila_json)
                    unidades = pila_de_calculo.pop('unidades', 1)  # Extraer unidades
                    # YA NO es necesario convertir 'deadline' manualmente
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error deserializando pila_de_calculo_json: {e}")
                    pila_de_calculo = {}

            # 2. Construir metadata
            metadata = {
                "nombre": pila.nombre,
                "descripcion": pila.descripcion,
                "unidades": unidades,
                "producto_origen": pila.producto_origen_codigo,
                "fecha_creacion": pila.fecha_creacion
            }

            # 3. Deserializar resultados de simulación
            # ⚠️ CAMBIO: Usamos object_hook=decode_pila_json
            simulation_results = []
            if pila.resultados_simulacion:
                try:
                    simulation_results = json.loads(pila.resultados_simulacion, object_hook=decode_pila_json)
                    # YA NO es necesario convertir 'Inicio' y 'Fin' manualmente
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error deserializando resultados_simulacion: {e}")
                    simulation_results = []

            # 4. Obtener pasos de la pila
            pasos_db = session.query(PasoPila).filter_by(
                pila_id=pila_id
            ).order_by(PasoPila.orden).all()

            production_flow_loaded = []
            for paso in pasos_db:
                try:
                    # ⚠️ CAMBIO: Usamos object_hook=decode_pila_json
                    paso_data = json.loads(paso.datos_paso, object_hook=decode_pila_json)

                    # YA NO es necesario convertir 'start_date' manualmente
                    # YA NO es necesario añadir 'tipo_reasignacion' por defecto
                    # (si se guarda None, se cargará None, que es correcto)

                    production_flow_loaded.append(paso_data)
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Error deserializando datos del paso ID {paso.id} para la pila ID {pila_id}.")
                    continue  # Saltar este paso si está corrupto

            # 5. Post-procesar el flujo para reconstruir los índices de dependencia
            self._convert_ids_to_indices(production_flow_loaded)

            self.logger.info(
                f"✅ Pila ID '{pila_id}' cargada con serializador robusto: "
                f"{len(production_flow_loaded)} pasos y {len(simulation_results)} resultados. Índices reconstruidos."
            )
            return metadata, pila_de_calculo, production_flow_loaded, simulation_results

        result = self.safe_execute(_operation)
        if result is None:
            return None, None, None, None
        return result

    def delete_pila(self, pila_id: int) -> bool:
        """
        Elimina una pila y sus pasos asociados.
        Mantiene compatibilidad con: pilas_database_manager.delete_pila()

        Args:
            pila_id: ID de la pila a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """

        def _operation(session):
            pila = session.query(Pila).filter_by(id=pila_id).first()
            if not pila:
                self.logger.warning(f"No se encontró la pila con ID {pila_id} para eliminar.")
                return False

            session.delete(pila)  # Los pasos se eliminan automáticamente por CASCADE
            # ✅ NO hacer commit aquí - safe_execute lo maneja automáticamente
            self.logger.info(f"Pila ID '{pila_id}' marcada para eliminación.")
            return True

        result = self.safe_execute(_operation)
        if result:
            self.logger.info(f"Pila ID '{pila_id}' eliminada exitosamente de la BD.")
        return result or False

    def get_all_pilas_with_dates(self) -> List[PilaDTO]:
        """
        Obtiene una lista de todas las pilas con fechas calculadas de los resultados.
        Mantiene compatibilidad con: pilas_database_manager.get_all_pilas_with_dates()

        Returns:
            Lista de objetos PilaDTO
        """

        def _operation(session):
            pilas = session.query(Pila).order_by(Pila.fecha_creacion.desc()).all()

            results = []
            for pila in pilas:
                start_date, end_date = None, None

                if pila.resultados_simulacion:
                    try:
                        sim_data = json.loads(pila.resultados_simulacion)
                        if sim_data:
                            # Convertir strings a objetos datetime para comparar
                            all_dates = []
                            for task in sim_data:
                                if isinstance(task.get('Inicio'), str):
                                    all_dates.append(datetime.fromisoformat(task['Inicio']))
                                if isinstance(task.get('Fin'), str):
                                    all_dates.append(datetime.fromisoformat(task['Fin']))

                            if all_dates:
                                start_date = min(all_dates).date()
                                end_date = max(all_dates).date()
                    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                        self.logger.warning(f"No se pudieron parsear las fechas para la pila ID {pila.id}")

                results.append(PilaDTO(
                    id=pila.id,
                    nombre=pila.nombre,
                    descripcion=pila.descripcion,
                    producto_origen_codigo=pila.producto_origen_codigo,
                    start_date=start_date,
                    end_date=end_date
                ))

            return results

        return self.safe_execute(_operation) or []

    # ===============================================================================
    # MÉTODOS PARA BITÁCORA
    # ===============================================================================

    def create_diario_bitacora(self, pila_id: int) -> Optional[int]:
        """
        Crea una nueva bitácora para una pila si no existe.
        Mantiene compatibilidad con: pilas_database_manager.create_diario_bitacora()

        Args:
            pila_id: ID de la pila

        Returns:
            ID de la bitácora creada o None si error
        """

        def _operation(session):
            # Verificar si ya existe una bitácora para esta pila
            bitacora_existente = session.query(DiarioBitacora).filter_by(pila_id=pila_id).first()
            if bitacora_existente:
                return bitacora_existente.id

            bitacora = DiarioBitacora(pila_id=pila_id)
            session.add(bitacora)
            session.flush()  # Para obtener el ID

            self.logger.info(f"Bitácora creada para la pila '{pila_id}'.")
            return bitacora.id

        return self.safe_execute(_operation)

    def get_diario_bitacora(self, pila_id: int) -> Tuple[Optional[int], List[Tuple]]:
        """
        Obtiene la bitácora y sus entradas para una pila.
        Mantiene compatibilidad con: pilas_database_manager.get_diario_bitacora()

        Args:
            pila_id: ID de la pila

        Returns:
            Tupla de (bitacora_id, lista_entradas)
        """

        def _operation(session):
            bitacora = session.query(DiarioBitacora).filter_by(pila_id=pila_id).first()
            if not bitacora:
                return None, []

            entradas = session.query(EntradaDiario).filter_by(
                bitacora_id=bitacora.id
            ).order_by(EntradaDiario.dia_numero).all()

            # Convertir a tuplas manteniendo el formato esperado
            entradas_tuplas = []
            for entrada in entradas:
                entradas_tuplas.append((
                    entrada.fecha,
                    entrada.dia_numero,
                    entrada.plan_previsto,
                    entrada.trabajo_realizado,
                    entrada.notas
                ))

            return bitacora.id, entradas_tuplas

        result = self.safe_execute(_operation)
        if result is None:
            return None, []
        return result

    def add_diario_entry(self, pila_id: int, fecha: date, dia_numero: int,
                         plan_previsto: str, trabajo_realizado: str, notas: str) -> bool:
        """
        Añade o actualiza una entrada diaria a una bitácora existente.
        Mantiene compatibilidad con: pilas_database_manager.add_diario_entry()

        Args:
            pila_id: ID de la pila
            fecha: Fecha de la entrada
            dia_numero: Número del día
            plan_previsto: Plan previsto para ese día
            trabajo_realizado: Trabajo realmente realizado
            notas: Notas adicionales

        Returns:
            True si se añadió correctamente, False en caso contrario
        """

        def _operation(session):
            # Buscar o crear bitácora
            bitacora = session.query(DiarioBitacora).filter_by(pila_id=pila_id).first()
            if not bitacora:
                bitacora = DiarioBitacora(pila_id=pila_id)
                session.add(bitacora)
                session.flush()
                self.logger.info(f"Creada nueva bitácora para pila ID {pila_id}.")

            # Eliminar entrada existente para la misma fecha
            session.query(EntradaDiario).filter(
                EntradaDiario.bitacora_id == bitacora.id,
                EntradaDiario.fecha == fecha
            ).delete()

            # Crear nueva entrada
            entrada = EntradaDiario(
                bitacora_id=bitacora.id,
                fecha=fecha,
                dia_numero=dia_numero,
                plan_previsto=plan_previsto,
                trabajo_realizado=trabajo_realizado,
                notas=notas
            )
            session.add(entrada)

            self.logger.info(f"Entrada diaria añadida/actualizada en la bitácora {bitacora.id} para la fecha {fecha}.")
            return True

        return self.safe_execute(_operation) or False