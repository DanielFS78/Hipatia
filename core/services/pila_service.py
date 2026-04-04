# -*- coding: utf-8 -*-
"""
Lógica o utilidades del núcleo (`pila_service`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import logging
from typing import Any
from dataclasses import asdict

from PyQt6.QtCore import QObject, pyqtSignal

from core.dtos import (
    PilaDTO, PreprocesoDTO, PreparationGroupDTO, MachineDTO,
    CalculationProductDTO, CalculationSubPartDTO
)
from database.database_manager import DatabaseManager
from database.repositories.pila import PilaRepository

class PilaService(QObject):
    """
    Servicio de dominio para gestionar Pilas de fabricación y Simulaciones.
    """
    
    pilas_changed_signal = pyqtSignal(str, str)
    simulation_finished_signal = pyqtSignal(object) 
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.logger = logging.getLogger("PilaService")

    @property
    def pila_repo(self) -> PilaRepository:
        return self.db.pila_repo

    def get_all_pilas(self) -> list[PilaDTO]:
        self.logger.info("Obteniendo todas las pilas guardadas.")
        return self.pila_repo.get_all_pilas()

    def get_all_pilas_with_dates(self) -> list[PilaDTO]:
        return self.pila_repo.get_all_pilas_with_dates()

    def load_pila(self, pila_id: int) -> tuple[PilaDTO | None, dict[Any, Any] | None, list[Any] | None, list[Any] | None]:
        self.logger.info(f"Cargando la pila con ID {pila_id}.")
        return self.pila_repo.load_pila(pila_id)

    def save_pila(self, nombre: str, descripcion: str, pila_de_calculo: dict[str, Any], production_flow: list[Any],
                  simulation_results: list[Any], producto_origen_codigo: str | None = None, unidades: int = 1) -> str | bool | int:
        self.logger.info(f"Intentando guardar la pila '{nombre}' usando el repositorio.")

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

    def delete_pila(self, pila_id: int) -> bool:
        self.logger.info(f"Eliminando la pila con ID {pila_id} usando el repositorio.")

        success = self.pila_repo.delete_pila(pila_id)

        if success:
            self.pilas_changed_signal.emit("Éxito", "La pila ha sido eliminada correctamente.")
        else:
            self.pilas_changed_signal.emit("Error al Eliminar", "No se pudo eliminar la pila seleccionada.")
        return success

    # --- Diario de Bitácora ---
    
    def get_diario_bitacora(self, pila_id: int) -> tuple[int | None, list[Any]]:
        return self.pila_repo.get_diario_bitacora(pila_id)

    def add_diario_entry(self, pila_id: int, fecha: Any, dia_numero: int, plan_previsto: str, trabajo_realizado: str, notas: str) -> bool:
        return self.pila_repo.add_diario_evento(pila_id, fecha, dia_numero, plan=plan_previsto, trabajo=trabajo_realizado, notas=notas)

    def add_diario_evento(self, pila_id: int, fecha: Any, dia_numero: int, plan_previsto: str, trabajo_realizado: str, notas: str) -> bool:
        """
        Alias de compatibilidad para el nombre histórico del método.

        La UI y `AppModel` usan `add_diario_evento`, pero el método canónico del servicio es
        `add_diario_entry`.
        """
        return self.add_diario_entry(pila_id, fecha, dia_numero, plan_previsto, trabajo_realizado, notas)

    def create_diario_bitacora(self, pila_id: int) -> bool:
        return self.pila_repo.create_diario_bitacora(pila_id) is not None

    # --- Simulación ---
    # Métodos que preparan datos para el motor de simulación
    
    def get_data_for_calculation(self, producto_codigo: str) -> list[CalculationProductDTO]:
        """
        Obtiene datos de un producto estructurados en DTOs para el motor de cálculo.
        """
        self.logger.info(f"PilaService: Preparando CalculationProductDTO para '{producto_codigo}'.")

        details = self.db.product_repo.get_product_details(producto_codigo)
        prod_data = details.producto
        sub_data = details.subfabricaciones
        procesos_data = details.procesos_mecanicos

        if not prod_data:
            return []

        # 2. Estructura principal
        sub_partes: list[CalculationSubPartDTO] = []

        # 3. Procesamos las subfabricaciones
        if prod_data.tiene_subfabricaciones:
            all_machines_data = self.db.machine_repo.get_all_machines(include_inactive=True)
            machines_dict = {m.id: m for m in all_machines_data}
            
            for sub_dto in sub_data:
                maquina_id = sub_dto.maquina_id
                tipo_maquina_requerido = None

                if maquina_id and maquina_id in machines_dict:
                    tipo_maquina_requerido = machines_dict[maquina_id].tipo_proceso

                sub_partes.append(CalculationSubPartDTO(
                    descripcion=sub_dto.descripcion,
                    tiempo=sub_dto.tiempo,
                    tipo_trabajador=sub_dto.tipo_trabajador,
                    requiere_maquina_tipo=tipo_maquina_requerido
                ))

        # 4. Procesamos los procesos adicionales
        for proceso_dto in procesos_data:
            sub_partes.append(CalculationSubPartDTO(
                descripcion=f"(Proceso) {proceso_dto.nombre}",
                tiempo=proceso_dto.tiempo,
                tipo_trabajador=proceso_dto.tipo_trabajador,
                requiere_maquina_tipo=None
            ))

        # 5. Retornamos el DTO principal
        return [CalculationProductDTO(
            codigo=prod_data.codigo,
            descripcion=prod_data.descripcion,
            departamento=prod_data.departamento,
            tipo_trabajador=prod_data.tipo_trabajador,
            donde=prod_data.donde,
            tiene_subfabricaciones=prod_data.tiene_subfabricaciones,
            tiempo_optimo=prod_data.tiempo_optimo,
            sub_partes=sub_partes
        )]

    def get_data_for_calculation_from_session(self, planning_session: list[CalculationProductDTO | dict[str, Any]]) -> list[CalculationProductDTO]:
        """
        Recopila las tareas para todos los lotes de la sesión, convirtiéndolos a DTOs.
        """
        all_task_groups: list[CalculationProductDTO] = []
        for lote_instance in planning_session:
            # 0. Si el item ya es un DTO, añadirlo directamente
            if isinstance(lote_instance, CalculationProductDTO):
                all_task_groups.append(lote_instance)
                continue

            deadline = lote_instance.get('deadline')
            identificador = lote_instance.get('identificador')
            units = lote_instance.get('unidades', 1)

            # 1. Obtener productos y fabricaciones del lote
            if "pila_de_calculo_directa" in lote_instance:
                lote_details_dict = lote_instance["pila_de_calculo_directa"]
                productos = []
                for codigo, data in lote_details_dict.get('productos', {}).items():
                    desc = data.get('descripcion', '') if isinstance(data, dict) else ''
                    productos.append((codigo, desc))

                fabricaciones = []
                for fab_key, data in lote_details_dict.get('fabricaciones', {}).items():
                    if isinstance(data, dict):
                        fab_id = data.get('id', fab_key)
                        try:
                            fabricaciones.append((int(fab_id), data.get('codigo', '')))
                        except (ValueError, TypeError):
                            continue
            else:
                lote_details = self.db.lote_repo.get_lote_details(lote_instance["lote_template_id"])
                if not lote_details:
                    continue
                productos = [(p.codigo, p.descripcion) for p in (lote_details.productos or [])]
                fabricaciones = [(f.id, f.codigo) for f in (lote_details.fabricaciones or [])]

            # 2. Procesar productos
            for prod_code, _ in productos:
                product_dtos = self.get_data_for_calculation(prod_code)
                if product_dtos:
                    dto = product_dtos[0]
                    dto.deadline = deadline
                    dto.fabricacion_id = identificador
                    dto.units_for_this_instance = units
                    all_task_groups.append(dto)

            # 3. Procesar fabricaciones
            for fab_id, _ in fabricaciones:
                try:
                    # 3.1. Añadir preprocesos de la fabricación
                    fab_details = self.db.preproceso_repo.get_fabricacion_by_id(fab_id)
                    if fab_details and fab_details.preprocesos:
                        for prep in fab_details.preprocesos:
                            # Convertir preproceso individual a CalculationProductDTO-like structure
                            # aunque sea una tarea única, se trata como un "producto" de preproceso
                            prep_dto = CalculationProductDTO(
                                codigo=f"PREP_{prep.id}",
                                descripcion=f"[PREPROCESO] {prep.nombre}",
                                departamento="Pre-Produccion",
                                tipo_trabajador=1,
                                donde="",
                                tiene_subfabricaciones=True,
                                tiempo_optimo=prep.tiempo,
                                sub_partes=[CalculationSubPartDTO(
                                    descripcion=prep.nombre,
                                    tiempo=prep.tiempo,
                                    tipo_trabajador=1,
                                    requiere_maquina_tipo=None
                                )],
                                deadline=deadline,
                                fabricacion_id=identificador,
                                units_for_this_instance=units
                            )
                            all_task_groups.append(prep_dto)

                    # 3.2. Productos dentro de la fabricación
                    fab_products = self.db.preproceso_repo.get_products_for_fabricacion(fab_id)
                    for fp_dto in fab_products:
                        product_dtos = self.get_data_for_calculation(fp_dto.producto_codigo)
                        if product_dtos:
                            dto = product_dtos[0]
                            dto.deadline = deadline
                            dto.fabricacion_id = identificador
                            dto.units_for_this_instance = units
                            # Importante: aquí el `cantidad_en_kit` debería venir de fp_dto
                            dto.cantidad_en_kit = fp_dto.cantidad
                            all_task_groups.append(dto)

                except Exception as e:
                    self.logger.error(f"Error procesando fabricación {fab_id}: {e}")
                    continue

        self.logger.info(f"Total de DTOs de cálculo recopilados: {len(all_task_groups)}")
        return all_task_groups

    # get_data_for_calculation_from_session y otros helpers complejos de preparación de datos
    # se pueden migrar aquí.
