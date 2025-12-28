# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date
from dataclasses import asdict

from PyQt6.QtCore import QObject, pyqtSignal

from database.database_manager import DatabaseManager

class AppModel(QObject):
    """Modelo de la aplicación."""
    product_added_signal = pyqtSignal(str)
    product_updated_signal = pyqtSignal()
    product_deleted_signal = pyqtSignal()
    pilas_changed_signal = pyqtSignal(str, str)
    workers_changed_signal = pyqtSignal()
    machines_changed_signal = pyqtSignal()
    prep_steps_changed_signal = pyqtSignal()

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager  # Guardamos la instancia del gestor principal

        # Corrección: Usar db_manager para acceder a los repositorios ya inicializados
        self.product_repo = db_manager.product_repo
        self.worker_repo = db_manager.worker_repo
        self.machine_repo = db_manager.machine_repo
        self.pila_repo = db_manager.pila_repo
        self.preproceso_repo = db_manager.preproceso_repo
        self.lote_repo = db_manager.lote_repo
        self.iteration_repo = db_manager.iteration_repo
        self.tracking_repo = db_manager.tracking_repo
        self.material_repo = db_manager.material_repo

        self.logger = logging.getLogger("EvolucionTiemposApp")
        self.logger.info("Modelo inicializado con acceso directo a repositorios.")

        # Test completo de repositorios
        try:
            test_results = db_manager.test_all_repositories()
            logging.info(f"Test de repositorios completado: {test_results}")
        except Exception as e:
            logging.error(f"Error en test de repositorios: {e}")

    def get_latest_fabricaciones(self, limit=5):
        """Solicita al repositorio las últimas fabricaciones añadidas."""
        self.logger.info(f"Modelo: Obteniendo las Últimas {limit} fabricaciones.")
        return self.preproceso_repo.get_latest_fabricaciones(limit)

    def search_fabricaciones(self, query: str):
        """Busca fabricaciones usando el repositorio de preprocesos."""
        try:
            return self.preproceso_repo.search_fabricaciones(query)
        except Exception as e:
            self.logger.error(f"Error buscando fabricaciones a través del repositorio: {e}")
            return []

    def create_fabricacion(self, codigo: str, descripcion: str):
        """Pasa la solicitud de crear una fabricación al repositorio."""
        return self.preproceso_repo.create_fabricacion(codigo, descripcion)

    def update_fabricacion_preprocesos(self, fabricacion_id: int, preproceso_ids: list):
        """Pasa la solicitud de actualizar los preprocesos de una fabricación al repositorio."""
        return self.preproceso_repo.update_fabricacion_preprocesos(fabricacion_id, preproceso_ids)

    def get_product_iterations(self, codigo_producto):
        return self.iteration_repo.get_product_iterations(codigo_producto)

    def get_diario_bitacora(self, pila_id: int):
        return self.pila_repo.get_diario_bitacora(pila_id)

    def add_diario_entry(self, pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas):
        return self.pila_repo.add_diario_entry(pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas)

    def create_diario_bitacora(self, pila_id: int):
        return self.pila_repo.create_diario_bitacora(pila_id)

    def add_product_iteration(self, codigo_producto, responsable, descripcion, tipo_fallo, materiales_list,
                              ruta_imagen=None, ruta_plano=None):
        return self.iteration_repo.add_product_iteration(codigo_producto, responsable, descripcion, tipo_fallo, materiales_list,
                                             ruta_imagen, ruta_plano)

    def update_product_iteration(self, iteracion_id, responsable, descripcion, tipo_fallo):
        return self.iteration_repo.update_product_iteration(iteracion_id, responsable, descripcion, tipo_fallo)

    def get_materials_for_product(self, producto_codigo: str):
        """Obtiene los materiales asociados a un producto específico."""
        self.logger.info(f"Modelo: Obteniendo materiales para el producto '{producto_codigo}'.")
        return self.product_repo.get_materials_for_product(producto_codigo)

    def add_material_to_iteration(self, iteracion_id, codigo, descripcion):
        material_id = self.db.material_repo.add_material(codigo, descripcion)
        if material_id:
            return self.db.material_repo.link_material_to_iteration(iteracion_id, material_id)
        return False

    def get_all_materials_for_selection(self) -> list:
        """
        Obtiene todos los materiales disponibles para usar en diálogos de selección.

        Returns:
            list: Lista de objetos MaterialDTO.
        """
        try:
            # Usar el método que acabamos de implementar en DatabaseManager
            materials = self.db.material_repo.get_all_materials()
            if not materials:
                self.logger.info("No se encontraron materiales en la base de datos.")
                return []

            self.logger.info(f"Obtenidos {len(materials)} materiales para selección.")
            return materials

        except Exception as e:
            self.logger.error(f"Error obteniendo materiales para selección: {e}")
            return []

    def update_material(self, material_id, nuevo_codigo, nueva_descripcion):
        return self.db.material_repo.update_material(material_id, nuevo_codigo, nueva_descripcion)

    def delete_material_link(self, iteracion_id, material_id):
        return self.db.material_repo.delete_material_link_from_iteration(iteracion_id, material_id)

    def delete_product_iteration(self, iteracion_id):
        return self.iteration_repo.delete_product_iteration(iteracion_id)

    def get_data_for_calculation(self, producto_codigo: str):
        """Obtiene datos de un producto, asegurando que el tipo de máquina se resuelva."""
        self.logger.info(f"Modelo: Obteniendo y preparando datos para cálculo de producto '{producto_codigo}'.")

        # Esta llamada ya funciona bien y obtiene los datos del repositorio
        prod_data, sub_data, procesos_data = self.product_repo.get_product_details(producto_codigo)

        if not prod_data:
            return []

        # Estructura base para los datos de cálculo
        calculation_data = [{
            "codigo": prod_data.codigo,
            "descripcion": prod_data.descripcion,
            "departamento": prod_data.departamento,
            "tipo_trabajador": prod_data.tipo_trabajador,
            "donde": prod_data.donde,
            "tiene_subfabricaciones": prod_data.tiene_subfabricaciones,
            "tiempo_optimo": prod_data.tiempo_optimo,
            "sub_partes": []
        }]

        # 🔍 LOGGING TEMPORAL PARA VALIDACIÓN (Fase 3.1)
        self.logger.info(f"Producto {producto_codigo} - tiempo_optimo: {prod_data.tiempo_optimo}")

        # Procesamos las subfabricaciones para "rehidratar" el tipo de máquina
        if prod_data.tiene_subfabricaciones:  # si tiene_subfabricaciones
            for sub_dto in sub_data:
                maquina_id = sub_dto.maquina_id  # atributo DTO
                tipo_maquina_requerido = None

                # Si hay un ID de máquina, buscamos su tipo de proceso
                if maquina_id:
                    # Obtenemos TODAS las máquinas una vez y las guardamos en un dict para búsquedas rápidas
                    all_machines_data = self.machine_repo.get_all_machines(include_inactive=True)
                    # Ahora usamos atributos DTO en lugar de índices
                    machines_dict = {m.id: m for m in all_machines_data}

                    machine_details = machines_dict.get(maquina_id)
                    if machine_details:
                        tipo_maquina_requerido = machine_details.tipo_proceso

                # ✅ CAMBIO CRÍTICO: Usar "tiempo" en lugar de "duration"
                calculation_data[0]["sub_partes"].append({
                    "descripcion": sub_dto.descripcion,
                    "tiempo": sub_dto.tiempo,  # ✅ Tiempo real de la subfabricación
                    "tipo_trabajador": sub_dto.tipo_trabajador,
                    "requiere_maquina_tipo": tipo_maquina_requerido
                })

                # 🔍 LOGGING TEMPORAL PARA VALIDACIÓN (Fase 3.1)
                self.logger.info(f"  Subfabricación: {sub_dto.descripcion} - tiempo: {sub_dto.tiempo}")

        for proceso_dto in procesos_data:
            calculation_data[0]["sub_partes"].append({
                "descripcion": f"(Proceso) {proceso_dto.nombre}",
                "tiempo": proceso_dto.tiempo,  # ✅ Tiempo real del proceso
                "tipo_trabajador": proceso_dto.tipo_trabajador,
                "requiere_maquina_tipo": None
            })

        return calculation_data

    def get_data_for_calculation_from_session(self, planning_session):
        """
        CORREGIDO: Recopila las tareas, AÑADE los preprocesos faltantes,
        y AÑADE la 'deadline' y el 'identificador' a cada grupo de tareas.
        """
        all_task_groups = []
        for lote_instance in planning_session:
            # Obtenemos los datos de esta entrega parcial usando .get() para evitar errores
            deadline = lote_instance.get('deadline')  # Puede ser None si no existe
            identificador = lote_instance.get('identificador')
            units = lote_instance.get('unidades', 1)  # Por defecto 1 si no se especifica

            # Usamos la "pila_de_calculo" si viene de una Pila cargada
            if "pila_de_calculo_directa" in lote_instance:
                lote_details_dict = lote_instance["pila_de_calculo_directa"]

                # 🔍 LOG DE DEPURACIÓN: Ver estructura completa
                self.logger.info(f"🔍 DEBUG: Estructura de pila_de_calculo_directa:")
                self.logger.info(f"🔍 Tipo: {type(lote_details_dict)}")
                self.logger.info(
                    f"🔍 Claves: {lote_details_dict.keys() if isinstance(lote_details_dict, dict) else 'No es dict'}")
                self.logger.info(f"🔍 Contenido completo: {lote_details_dict}")

                # ✅ CORRECCIÓN: Procesar productos correctamente
                productos = []
                for codigo, data in lote_details_dict.get('productos', {}).items():
                    if isinstance(data, dict):
                        productos.append((codigo, data.get('descripcion', '')))
                    else:
                        productos.append((codigo, ''))

                # ✅ CORRECCIÓN: Procesar fabricaciones correctamente
                fabricaciones = []
                for fab_key, data in lote_details_dict.get('fabricaciones', {}).items():
                    if isinstance(data, dict):
                        # Usar la clave como ID si no hay 'id' en data
                        fab_id = data.get('id', fab_key)
                        try:
                            fab_id = int(fab_id)
                            fabricaciones.append((fab_id, data.get('codigo', '')))
                        except (ValueError, TypeError):
                            self.logger.warning(f"ID de fabricación inválido: {fab_id}")
                            continue

            # O cargamos desde la plantilla de Lote si es un cálculo nuevo
            else:
                lote_details = self.lote_repo.get_lote_details(lote_instance["lote_template_id"])
                if not lote_details:
                    continue
                productos = [(p.codigo, p.descripcion) for p in lote_details.productos]
                fabricaciones = [(f.id, f.codigo) for f in lote_details.fabricaciones]

            # Procesar productos del lote
            for prod_code, _ in productos:
                product_data_list = self.get_data_for_calculation(prod_code)
                if product_data_list:
                    product_data = product_data_list[0]
                    product_data['deadline'] = deadline
                    product_data['fabricacion_id'] = identificador
                    product_data['units_for_this_instance'] = units
                    all_task_groups.append(product_data)

            # Procesar fabricaciones del lote
            for fab_id, _ in fabricaciones:
                # ✅ AÑADIDO: Log para debugging
                self.logger.info(f"Procesando fabricación ID {fab_id} con preprocesos")

                try:
                    # 1. AÑADIMOS LA CARGA DE PREPROCESOS ASOCIADOS A LA FABRICACIÓN
                    fab_details = self.preproceso_repo.get_fabricacion_by_id(fab_id)
                    if fab_details and fab_details.preprocesos:
                        for prep in fab_details.preprocesos:
                            preproceso_task = {
                                "codigo": f"PREP_{prep.id}",
                                "descripcion": f"[PREPROCESO] {prep.nombre}",
                                "departamento": "Pre-Produccion",
                                "tipo_trabajador": 1,
                                "donde": "",
                                "tiene_subfabricaciones": True,
                                "tiempo_optimo": prep.tiempo,
                                "sub_partes": [{
                                    "descripcion": prep.nombre,
                                    "tiempo": prep.tiempo,
                                    "tipo_trabajador": 1,
                                    "requiere_maquina_tipo": None
                                }],
                                'deadline': deadline,
                                'fabricacion_id': identificador,
                                'units_for_this_instance': units
                            }
                            all_task_groups.append(preproceso_task)

                    # 2. MANTENEMOS LA LÓGICA EXISTENTE PARA LOS PRODUCTOS DENTRO DE LA FABRICACIÓN
                    fab_products = self.db.preproceso_repo.get_products_for_fabricacion(fab_id)
                    for fp_dto in fab_products:
                        product_data_list = self.get_data_for_calculation(fp_dto.producto_codigo)
                        if product_data_list:
                            product_data = product_data_list[0]
                            product_data['deadline'] = deadline
                            product_data['fabricacion_id'] = identificador
                            product_data['units_for_this_instance'] = units
                            all_task_groups.append(product_data)

                except Exception as e:
                    self.logger.error(f"Error procesando fabricación {fab_id}: {e}", exc_info=True)
                    continue

        # ✅ AÑADIDO: Log para verificar resultados
        self.logger.info(f"Total de grupos de tareas recopilados: {len(all_task_groups)}")
        return all_task_groups

    def delete_machine(self, machine_id):
        """Elimina una máquina y emite una señal de cambio."""
        logging.info(f"Modelo: Eliminando máquina ID {machine_id}.")
        success = self.machine_repo.delete_machine(machine_id)
        if success:
            self.machines_changed_signal.emit()
        return success

    def get_machine_usage_stats(self):
        return self.machine_repo.get_machine_usage_stats()

    def get_worker_load_stats(self):
        """
        Calcula el tiempo total de trabajo (en minutos) asignado a cada trabajador
        a través de todas las pilas de producción guardadas.
        VERSIÓN CORREGIDA: Interpreta correctamente los datos del nuevo motor de simulación.
        """
        self.logger.info("Modelo: Calculando estadísticas de carga de trabajo reales.")
        try:
            all_workers = self.worker_repo.get_all_workers(include_inactive=False)
            worker_minutes = {w.nombre_completo: 0 for w in all_workers}

            pilas_data = self.pila_repo.get_all_pilas_with_dates()

            for pila in pilas_data:
                _, _, _, simulation_results = self.pila_repo.load_pila(pila.id)

                if not simulation_results:
                    continue

                for task in simulation_results:
                    duration = task.get('Duracion (min)', 0)
                    if duration == 0:
                        continue

                    # --- INICIO DE LA CORRECCIÓN ---
                    # Lógica robusta para obtener la lista de trabajadores
                    workers_for_task = []
                    # 1. Prioridad 1: Usar la lista explícita (del nuevo motor)
                    if 'Lista Trabajadores' in task and isinstance(task['Lista Trabajadores'], list):
                        workers_for_task = task['Lista Trabajadores']

                    # 2. Prioridad 2: Usar el campo principal, comprobando si es lista o texto
                    elif 'Trabajador Asignado' in task:
                        assigned = task['Trabajador Asignado']
                        if isinstance(assigned, list):
                            # Formato antiguo: ya es una lista
                            workers_for_task = assigned
                        elif isinstance(assigned, str):
                            # Formato nuevo: es un string, hay que dividirlo
                            workers_for_task = [name.strip() for name in assigned.split(',')]
                    # --- FIN DE LA CORRECCIÓN ---

                    if not workers_for_task:
                        continue

                    # La duración del resultado es el tiempo que cada trabajador estuvo ocupado.
                    # Se suma directamente a cada trabajador que participó.
                    for worker_name in workers_for_task:
                        if worker_name in worker_minutes:
                            worker_minutes[worker_name] += duration

            final_stats = sorted(worker_minutes.items(), key=lambda item: item[1], reverse=True)
            self.logger.info(f"Cálculo de carga de trabajo completado: {final_stats}")
            return final_stats

        except Exception as e:
            self.logger.error(f"Error crítico al calcular las estadísticas de carga de trabajo: {e}", exc_info=True)
            return []

    def get_problematic_components_stats(self):
        return self.material_repo.get_problematic_components_stats()

    def search_products(self, query: str):
        if not query:
            return self.product_repo.get_all_products()
        if len(query) < 2:
            return []
        return self.product_repo.search_products(query)

    def get_latest_products(self, limit=10):
        """Solicita a la BD los últimos productos añadidos."""
        self.logger.info(f"Modelo: Obteniendo los últimos {limit} productos.")
        return self.product_repo.get_latest_products(limit)

    def get_product_details(self, codigo: str):
        return self.product_repo.get_product_details(codigo)

    def get_prep_step_details_by_ids(self, step_ids):
        # Este método no existe en el gestor de BD, se mantiene como placeholder.
        # La lógica actual obtiene los detalles de uno en uno.
        return {}

    def get_worker_details(self, worker_id):
        return self.db.worker_repo.get_worker_details(worker_id)

    def get_prep_step_details(self, step_id):
        return self.db.get_prep_step_details(step_id)

    def get_all_iterations_with_dates(self):
        return self.db.get_all_iterations_with_dates()

    def get_all_pilas_with_dates(self):
        return self.pila_repo.get_all_pilas_with_dates()

    def add_product(self, data, sub_data=None):
        """Valida y añade un producto usando el repositorio."""

        if not data.get("codigo") or not data.get("descripcion"):
            self.logger.error("Error de validación: Código y descripción son obligatorios.")
            return "MISSING_FIELDS"

        if not data.get("tiene_subfabricaciones"):
            try:
                tiempo_str = data.get("tiempo_optimo")
                if tiempo_str is None or str(tiempo_str).strip() == "":
                    raise ValueError("El tiempo óptimo no puede estar vacío.")
                tiempo = float(str(tiempo_str).replace(",", "."))
                if tiempo <= 0:
                    raise ValueError("El tiempo óptimo debe ser un número positivo.")
                data["tiempo_optimo"] = tiempo
            except (ValueError, TypeError):
                self.logger.error(f"Error de validación: Tiempo óptimo inválido para {data.get('codigo')}.")
                return "INVALID_TIME"

        # Pasar los datos al repositorio
        success = self.product_repo.add_product(data, sub_data)
        if success:
            self.product_added_signal.emit(data['codigo'])
            return "SUCCESS"
        else:
            return "DB_ERROR"

    def update_product(self, codigo_original, data, subfabricaciones=None):
        return self.product_repo.update_product(codigo_original, data, subfabricaciones)

    def delete_product(self, codigo):
        return self.product_repo.delete_product(codigo)

    def update_product_iteration(self, iteracion_id, responsable, descripcion):
        return self.db.update_product_iteration(iteracion_id, responsable, descripcion)

    def get_group_details(self, group_id):
        return self.machine_repo.get_group_details(group_id)

    def link_material_to_product(self, producto_codigo, material_id):
        return self.db.material_repo.link_material_to_product(producto_codigo, material_id)

    def unlink_material_from_product(self, producto_codigo, material_id):
        return self.db.material_repo.unlink_material_from_product(producto_codigo, material_id)

    def save_pila(self, nombre: str, descripcion: str, pila_de_calculo: dict, production_flow: list,
                  simulation_results: list, producto_origen_codigo=None, unidades=1):
        self.logger.info(f"Modelo: Intentando guardar la pila '{nombre}' usando el repositorio.")

        result = self.pila_repo.save_pila(
            nombre,
            descripcion,
            pila_de_calculo,
            production_flow,
            simulation_results,
            producto_origen_codigo
            # Nota: 'unidades' se omite intencionadamente ya que será un parámetro dinámico.
        )

        if result is not False and result != "UNIQUE_CONSTRAINT":
            self.pilas_changed_signal.emit("Éxito", f"La pila '{nombre}' se ha guardado correctamente.")
        elif result == "UNIQUE_CONSTRAINT":
            self.pilas_changed_signal.emit("Error al Guardar",
                                           f"El nombre de pila '{nombre}' ya existe. Por favor, elija otro.")
        else:
            self.pilas_changed_signal.emit("Error al Guardar",
                                           f"No se pudo guardar la pila '{nombre}'. Consulte el log.")
        return result

    def get_all_pilas(self):
        logging.info("Modelo: Obteniendo todas las pilas guardadas.")
        return self.pila_repo.get_all_pilas()

    def load_pila(self, pila_id: int):
        logging.info(f"Modelo: Cargando la pila con ID {pila_id}.")
        return self.pila_repo.load_pila(pila_id)

    def delete_pila(self, pila_id: int):
        logging.info(f"Modelo: Eliminando la pila con ID {pila_id} usando el repositorio.")

        success = self.pila_repo.delete_pila(pila_id)

        if success:
            self.pilas_changed_signal.emit("Éxito", "La pila ha sido eliminada correctamente.")
        else:
            self.pilas_changed_signal.emit("Error al Eliminar", "No se pudo eliminar la pila seleccionada.")
        return success

    def import_database(self, source_path):
        return self.db.import_from_old_db(source_path)

    def get_all_workers(self, include_inactive=False):
        logging.info("Modelo: Obteniendo lista de trabajadores.")
        return self.worker_repo.get_all_workers(include_inactive)

    def get_latest_workers(self, limit=10):
        """Solicita a la BD los últimos trabajadores añadidos."""
        self.logger.info(f"Modelo: Obteniendo los últimos {limit} trabajadores.")
        return self.worker_repo.get_latest_workers(limit)

    def get_latest_machines(self, limit=10):
        """Solicita a la BD las últimas máquinas añadidas."""
        self.logger.info(f"Modelo: Obteniendo las últimas {limit} máquinas.")
        return self.machine_repo.get_latest_machines(limit)

    def add_worker(self, nombre, notas, tipo_trabajador=1, username=None, password_hash=None, role=None):
        logging.info(f"Modelo: Añadiendo trabajador '{nombre}' con usuario '{username}'.")
        # Llama al repositorio con los nuevos parámetros
        # worker_id es None por defecto en el repo, lo que indica "crear nuevo"
        result = self.worker_repo.add_worker(
            nombre_completo=nombre,
            notas=notas,
            tipo_trabajador=tipo_trabajador,
            activo=True,  # Los nuevos trabajadores siempre se añaden como activos
            username=username,
            password_hash=password_hash,
            role=role
        )
        if result is True:
            self.workers_changed_signal.emit()
        return result

    def update_worker(self, worker_id, nombre, activo, notas, tipo_trabajador, username=None, password_hash=None,
                      role=None):
        """Actualiza un trabajador existente usando la lógica upsert del repositorio."""
        logging.info(f"Modelo: Actualizando trabajador ID {worker_id} (vía add_worker) con usuario '{username}'.")

        # Llamamos a la función 'add_worker' del repositorio, que maneja el "upsert"
        # Pasamos el worker_id para forzar la actualización
        result = self.worker_repo.add_worker(
            nombre_completo=nombre,
            notas=notas,
            tipo_trabajador=tipo_trabajador,
            activo=activo,
            worker_id=worker_id,  # <-- Esto activa el modo "update" en el repo
            username=username,
            password_hash=password_hash,
            role=role
        )

        success = (result is True)  # Convertir a booleano
        if success:
            self.workers_changed_signal.emit()
        return success

    def delete_worker(self, worker_id):
        logging.info(f"Modelo: Eliminando trabajador ID {worker_id}.")
        success = self.worker_repo.delete_worker(worker_id)
        if success:
            self.workers_changed_signal.emit()
        return success

    def assign_task_to_worker(self, worker_id, product_code, quantity, orden_fabricacion=None):
        """
        Crea una nueva 'Fabricación' simple, le añade un producto y se la asigna a un trabajador.

        Args:
            worker_id: ID del trabajador
            product_code: Código del producto
            quantity: Cantidad a fabricar
            orden_fabricacion: Número de Orden de Fabricación (opcional)
        """
        self.logger.info(
            f"Asignando Tarea: W_ID={worker_id}, Prod={product_code}, Qty={quantity}, OF={orden_fabricacion}")
        try:
            # 1. Obtener detalles
            worker_details = self.worker_repo.get_worker_details(worker_id)  # Esto devuelve un DICIONARIO
            prod_details, _, _ = self.product_repo.get_product_details(product_code)  # Esto devuelve una TUPLA

            if not worker_details or not prod_details:
                return False, "No se encontraron detalles del trabajador o producto."

            # --- INICIO DE LA CORRECCIÓN ---
            # Accedemos a 'worker_details' como un diccionario
            worker_full_name = worker_details.get('nombre_completo', 'Trabajador')
            worker_name = worker_full_name.split(' ')[0]  # Primer nombre

            # Accedemos a 'prod_details' como el DTO que es
            prod_description = prod_details.descripcion
            # --- FIN DE LA CORRECCIÓN ---

            timestamp = datetime.now().strftime("%Y%m%d-%H%M")

            # 2. Crear una nueva Fabricación
            fab_codigo = f"TASK-{worker_name.upper()}-{product_code}-{timestamp}"

            # --- CORRECCIÓN ---
            # Usamos las nuevas variables para construir la descripción
            # Incluimos la OF si se proporcionó
            if orden_fabricacion:
                fab_desc = f"OF: {orden_fabricacion} | Tarea para {worker_full_name} - {quantity} x {prod_description}"
            else:
                fab_desc = f"Tarea para {worker_full_name} - {quantity} x {prod_description}"

            fab_data = {
                "codigo": fab_codigo,
                "descripcion": fab_desc,
                "preproceso_ids": []  # Es una tarea simple, sin preprocesos
            }
            # Este método devuelve True/False, no el ID.
            creation_success = self.preproceso_repo.create_fabricacion_with_preprocesos(fab_data)

            if not creation_success:
                return False, "Error al crear la fabricación. ¿Código duplicado?"

            # Ahora, buscamos la fabricación que acabamos de crear usando su código único
            # para obtener el ID numérico real.
            fab_id = None
            search_results = self.preproceso_repo.search_fabricaciones(fab_codigo)
            for res in search_results:
                if res.codigo == fab_codigo:
                    fab_id = res.id
                    break

            if not fab_id:
                self.logger.error(
                    f"¡Error crítico! Se creó la fabricación {fab_codigo} pero no se pudo encontrar su ID.")
                return False, "Error al recuperar la fabricación recién creada."

            self.logger.info(f"Fabricación {fab_codigo} creada con ID numérico: {fab_id}")

            # 3. Añadir el producto a la Fabricación
            add_prod_success = self.preproceso_repo.add_product_to_fabricacion(fab_id, product_code, quantity)
            if not add_prod_success:
                self.preproceso_repo.delete_fabricacion(fab_id)
                return False, "Error al añadir el producto a la fabricación."

            # 4. Asignar la Fabricación al Trabajador
            assign_success = self.db.tracking_repo.asignar_trabajador_a_fabricacion(worker_id, fab_id)
            if not assign_success:
                self.preproceso_repo.delete_fabricacion(fab_id)
                return False, "Error al asignar la fabricación al trabajador."

            self.logger.info(f"Tarea (Fab ID: {fab_id}) asignada con éxito.")

            of_msg = f" para OF: {orden_fabricacion}" if orden_fabricacion else ""
            return True, f"Tarea '{fab_codigo}'{of_msg} asignada a {worker_full_name}."

        except Exception as e:
            self.logger.error(f"Error crítico en assign_task_to_worker: {e}", exc_info=True)
            return False, f"Error inesperado: {e}"

    def get_all_machines(self, include_inactive=False):
        logging.info("Modelo: Obteniendo lista de máquinas.")
        return self.machine_repo.get_all_machines(include_inactive)

    def get_machines_by_process_type(self, tipo_proceso):
        logging.info(f"Modelo: Obteniendo máquinas para el proceso '{tipo_proceso}'.")
        return self.machine_repo.get_machines_by_process_type(tipo_proceso)

    def add_machine(self, nombre, departamento, tipo_proceso):
        logging.info(f"Modelo: Añadiendo máquina '{nombre}'.")
        result = self.machine_repo.add_machine(nombre, departamento, tipo_proceso)
        if result is True:
            self.machines_changed_signal.emit()
        return result

    def update_machine(self, machine_id, nombre, departamento, tipo_proceso, activa):
        logging.info(f"Modelo: Actualizando máquina ID {machine_id}.")
        success = self.machine_repo.update_machine(machine_id, nombre, departamento, tipo_proceso, activa)
        if success:
            self.machines_changed_signal.emit()
        return success

    def get_groups_for_machine(self, machine_id):
        return self.machine_repo.get_groups_for_machine(machine_id)

    def add_prep_group(self, machine_id, name, description, producto_codigo=None):
        return self.machine_repo.add_prep_group(machine_id, name, description, producto_codigo)

    def update_prep_group(self, group_id, name, description, producto_codigo=None):
        return self.machine_repo.update_prep_group(group_id, name, description, producto_codigo)

    def delete_prep_group(self, group_id):
        return self.machine_repo.delete_prep_group(group_id)

    def get_steps_for_group(self, group_id):
        return self.machine_repo.get_steps_for_group(group_id)

    def add_prep_step(self, group_id, name, time, description, is_daily):
        return self.machine_repo.add_prep_step(group_id, name, time, description, is_daily)

    def update_prep_step(self, step_id, data):
        return self.machine_repo.update_prep_step(step_id, data)

    def delete_prep_step(self, step_id):
        return self.machine_repo.delete_prep_step(step_id)

    def get_prep_info_for_product(self, producto_codigo):
        # TODO: Implement this method in a repository if needed
        # return self.db.get_prep_info_for_product(producto_codigo)
        return []

    def get_distinct_machine_processes(self):
        return self.machine_repo.get_distinct_machine_processes()

    def get_all_prep_steps(self):
        # TODO: Implement this method in a repository if needed
        # return self.db.get_all_prep_steps()
        return []

    # --- INICIO: NUEVOS MÉTODOS PARA HISTORIALES ---
    def get_machine_history(self, machine_id: int):
        """
        Obtiene el historial completo de una máquina, incluyendo mantenimientos
        y, en el futuro, un resumen de su uso en fabricaciones.
        """
        maintenance_history = self.machine_repo.get_machine_maintenance_history(machine_id)

        # Lógica para calcular horas totales y fabricaciones (requiere acceso a pilas.db)
        # Esto se implementará en una fase posterior para mantener los pasos manejables.
        num_fabrications = 0  # Placeholder
        total_hours = 0.0  # Placeholder

        last_maintenance_date = maintenance_history[0].maintenance_date if maintenance_history else None
        hours_since_maintenance = 0.0  # Placeholder

        return {
            'num_fabrications': num_fabrications,
            'total_hours': total_hours,
            'hours_since_maintenance': hours_since_maintenance,
            'maintenance_history': maintenance_history
        }

    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str):
        """Pasa la solicitud de añadir un registro de mantenimiento a la BD."""
        success = self.machine_repo.add_machine_maintenance(machine_id, maintenance_date, notes)
        if success:
            self.machines_changed_signal.emit()  # Para refrescar la vista si es necesario
        return success

    def get_worker_history(self, worker_id: int):
        """
        Obtiene el historial de un trabajador, incluyendo las fabricaciones asignadas
        y las anotaciones asociadas.
        """
        # Obtener anotaciones (esto ya funcionaba)
        annotations = self.worker_repo.get_worker_annotations(worker_id)

        # Obtener fabricaciones/tareas asignadas usando el tracking_repo
        try:
            fabrication_history_dtos = self.db.tracking_repo.get_fabricaciones_por_trabajador(worker_id)
            # Convertir DTOs a diccionarios para compatibilidad con UI existente
            fabrication_history = [asdict(dto) for dto in fabrication_history_dtos]
            self.logger.info(f"Obtenidas {len(fabrication_history)} tareas para trabajador {worker_id}")
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de tareas: {e}", exc_info=True)
            fabrication_history = []

        return fabrication_history, annotations

    def get_worker_activity_log(self, worker_id: int):
        """
        Obtiene el historial de fichajes (logs de trabajo) de un trabajador.
        """
        self.logger.info(f"Modelo: Obteniendo log de actividad para el trabajador ID {worker_id}.")
        # Llamamos al repositorio a través de la instancia de db_manager
        logs_dtos = self.db.tracking_repo.get_trabajo_logs_por_trabajador(worker_id)
        # Convertir a diccionarios
        return [asdict(log) for log in logs_dtos]

    def get_all_preprocesos_with_components(self) -> list:
        """
        Obtiene todos los preprocesos ya formateados desde el repositorio.
        """
        try:
            # El repositorio ahora hace todo el trabajo y devuelve la lista final.
            return self.preproceso_repo.get_all_preprocesos()
        except Exception as e:
            self.logger.error(f"Error obteniendo preprocesos: {e}", exc_info=True)
            return []

    def create_preproceso(self, data: dict) -> bool:
        """Crea un nuevo preproceso usando el repositorio."""
        # --- INICIO DE LA CORRECCIÓN ---
        # El error estaba en la llamada anterior, que pasaba los datos como
        # argumentos de palabra clave (nombre=data['nombre'], ...).
        # El repositorio espera recibir el diccionario 'data' directamente.
        # Esta llamada ahora es correcta.
        result = self.preproceso_repo.create_preproceso(data)
        # --- FIN DE LA CORRECCIÓN ---
        return result is not None

    def update_preproceso(self, preproceso_id: int, data: dict) -> bool:
        """Actualiza un preproceso existente."""
        # El diccionario 'data' ya contiene el tiempo, así que no se necesita cambio aquí.
        return self.preproceso_repo.update_preproceso(preproceso_id, data)

    def delete_preproceso(self, preproceso_id: int) -> bool:
        """
        Elimina un preproceso.

        Args:
            preproceso_id: ID del preproceso a eliminar

        Returns:
            bool: True si se eliminó exitosamente, False si falló
        """
        try:
            if not hasattr(self, 'preproceso_repo') or not self.preproceso_repo:
                self.logger.error("Repositorio de preprocesos no disponible.")
                return False

            success = self.preproceso_repo.delete_preproceso(preproceso_id)

            if success:
                self.logger.info(f"Preproceso ID {preproceso_id} eliminado exitosamente.")
            else:
                self.logger.warning(f"No se pudo eliminar el preproceso ID {preproceso_id}.")

            return success

        except Exception as e:
            self.logger.error(f"Error eliminando preproceso: {e}")
            return False
