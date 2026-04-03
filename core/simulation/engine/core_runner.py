# core/simulation/engine/core_runner.py
"""
Módulo del Ejecutor Core de la Simulación.

Gestiona la cola de prioridad de eventos, el avance del tiempo y la
persistencia de estados mediante checkpoints (serialización).
"""
import logging
import heapq
import time
import pickle
import os
from datetime import datetime
from typing import List, Any, Sequence, Optional, Dict
from threading import Lock

class CoreSimulationRunner:
    """
    Gestiona el bucle principal de la simulación y la cola de eventos.
    """
    def __init__(self, state: Any, lock: Lock):
        self.state = state
        self.lock = lock
        self.logger = logging.getLogger(__name__)

    def programar_eventos(self, eventos: Sequence[Any]) -> None:
        """Añade una lista de eventos al heap de forma segura para hilos."""
        with self.lock:
            # self.logger.info(f"📥 programar_eventos: Recibidos {len(eventos)} eventos")
            for evento in eventos:
                heapq.heappush(self.state.eventos_futuros, (evento.timestamp, self.state.event_counter, evento))
                self.state.event_counter += 1

    def cancelar_eventos(self, eventos_a_cancelar: List[Any]) -> None:
        """Marca eventos para cancelación."""
        for evento in eventos_a_cancelar:
            evento.cancelado = True
        self.logger.debug(f"Marcados {len(eventos_a_cancelar)} eventos para cancelación.")

    def tiene_evento_futuro(self, tarea_id: str, numero_unidad: int, id_instancia: Optional[str] = None) -> bool:
        """Verifica si ya existe un evento programado para una unidad/instancia."""
        with self.lock:
            for _, _, evento in self.state.eventos_futuros:
                if not evento.cancelado and hasattr(evento, 'tipo_evento'):
                    datos = getattr(evento, 'datos', {})
                    if (datos.get('tarea_id') == tarea_id and
                            datos.get('unidad') == numero_unidad):
                        if id_instancia:
                            if datos.get('id_instancia') == id_instancia:
                                return True
                        else:
                            return True
            return False

    def save_checkpoint(self, gestor_recursos: Any, checkpoint_path: str = 'simulation_checkpoint.pkl') -> None:
        """Guarda el estado actual en un archivo."""
        self.logger.info(f"Guardando checkpoint de la simulación en: {checkpoint_path}")
        simulation_state = {
            'tiempo_actual': self.state.tiempo_actual,
            'eventos_futuros': self.state.eventos_futuros,
            'event_counter': self.state.event_counter,
            'lineas_temporales': self.state.lineas_temporales,
            'gestor_recursos': gestor_recursos,
        }
        try:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(simulation_state, f)
            self.logger.info("Checkpoint guardado con éxito.")
        except (pickle.PicklingError, IOError) as e:
            self.logger.critical(f"No se pudo guardar el checkpoint de la simulación: {e}")

    def load_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """Carga el estado desde un archivo."""
        self.logger.info(f"Reanudando simulación desde checkpoint: {checkpoint_path}")
        try:
            with open(checkpoint_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    return data
                raise ValueError("Checkpoint data is not a dictionary")
        except (pickle.UnpicklingError, IOError, KeyError) as e:
            self.logger.critical(f"No se pudo cargar el checkpoint: {e}.")
            raise RuntimeError(f"El archivo de checkpoint está corrupto o es incompatible: {e}")
