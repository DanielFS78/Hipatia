# core/simulation/simulation_adapter.py
"""
Adaptador de Compatibilidad para el Motor de Simulación.

Proporciona una interfaz compatible con el antiguo Scheduler mientras
utiliza internamente el nuevo Motor de Eventos reactivo.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional


from .event_engine import MotorDeEventos
from core.services.calculation_audit import CalculationDecision, DecisionStatus
from core.services.time_calculator import CalculadorDeTiempos

class AdaptadorScheduler:
    """
    Clase adaptadora que tiene la misma interfaz que el antiguo Scheduler,
    pero utiliza internamente el nuevo MotorDeEventos.
    """

    # NUEVO: Añadir 'visual_dialog_reference=None' como parámetro opcional
    def __init__(self, production_flow: List[Dict[str, Any]], all_workers_with_skills: List[Any], available_machines: Dict[int, Any],
                 schedule_config: Any, time_calculator: CalculadorDeTiempos, start_date: datetime | None = None, visual_dialog_reference: Any = None) -> None: # <-- NUEVO PARÁMETRO

        self.logger = logging.getLogger(__name__)
        self.progress_signal = None # Este parece no usarse, pero lo mantenemos por si acaso

        # NUEVO: Guardar la referencia al diálogo visual (Fase 8.4)
        self.visual_dialog_reference = visual_dialog_reference
        # NOTA: La señal task_processing_signal la emitirá el MotorDeEventos

        # --- 1. Inicialización del Nuevo Motor ---
        # Pasamos el 'time_calculator' Y LA REFERENCIA AL DIÁLOGO al constructor del motor
        machines_str_keys: Dict[str, Any] = {str(k): v for k, v in available_machines.items()}
        self.motor = MotorDeEventos(
            production_flow=production_flow,
            all_workers_data=all_workers_with_skills,
            all_machines_data=machines_str_keys,
            schedule_config=schedule_config,
            time_calculator=time_calculator,
            start_date=start_date or datetime.now(),
            visual_dialog_reference=self.visual_dialog_reference # <-- NUEVO: Pasar la referencia
        )

        self.time_calculator = time_calculator
        # Mapeo id -> task (se mantiene igual)
        self.tasks_info = {step['task']['id']: step['task']
                           for step in production_flow
                           if isinstance(step, dict) and 'task' in step and isinstance(step['task'], dict) and 'id' in step['task']}

        # 📍 REEMPLAZA ESTE BLOQUE (Líneas 38-51 de tu archivo)

        # ✨ OPTIMIZACIÓN: Deshabilitar visualización para simulaciones grandes
        num_tasks = len(production_flow) if production_flow else 0
        self.large_simulation_mode = num_tasks > 20  # Umbral configurable [cite: 5]

        if self.large_simulation_mode:
            self.logger.info(
                f"⚡ MODO ALTA PERFORMANCE: {num_tasks} tareas detectadas.\n"
            f"   • Efectos visuales: DESHABILITADOS\n"
            f"   • Animaciones: ELIMINADAS TEMPORALMENTE\n"
            f"   • Actualizaciones UI: MINIMIZADAS"
            )
            # self.motor._visual_updates_enabled = False
            # ⚠️ CAMBIO: De _pause_all_animations a _destroy_all_visual_effects
            if self.visual_dialog_reference:
                self._destroy_all_visual_effects(self.visual_dialog_reference)
        else:
            self.logger.info(f"Simulación pequeña ({num_tasks} tareas). Efectos visuales ACTIVOS.")
            # self.motor._visual_updates_enabled = True

    def _find_task_index_by_id(self, tarea_id: str) -> int | None:
        """Compatibilidad temporal: delega la resolución de índice al motor."""
        if hasattr(self.motor, 'find_task_index_by_id'):
            return self.motor.find_task_index_by_id(tarea_id)
        return None

    def run_simulation(self) -> tuple[Any, Any]:
        """
        Ejecuta la simulación a través del nuevo MotorDeEventos,
        captura los resultados ya compilados, emite señal de finalización y cierra los recursos.
        """
        self.logger.info("ADAPTADOR: Ejecutando simulación a través del nuevo MotorDeEventos...")

        # ¡IMPORTANTE! El bucle principal de eventos está DENTRO de ejecutar_simulacion.
        # La emisión de 'simulation_processing_task' debe ocurrir ALLÍ.

        try:
            # --- 1. Ejecutar la simulación ---
            # El motor, al tener la referencia al diálogo, emitirá las señales de progreso internamente.
            results, audit_log = self.motor.ejecutar_simulacion()

            self.logger.info(
                f"ADAPTADOR: Simulación completada. Obtenidos {len(results)} resultados y {len(audit_log)} eventos de auditoría.")

            # NUEVO: Emitir señal de finalización SI hay una referencia al diálogo (Fase 8.4)
            if self.visual_dialog_reference and hasattr(self.visual_dialog_reference, 'simulation_finished'):
                try:
                    self.visual_dialog_reference.simulation_finished.emit()
                    self.logger.info("ADAPTADOR: Señal 'simulation_finished' emitida al diálogo.")
                except Exception as e:
                    self.logger.error(f"ADAPTADOR: Error al emitir 'simulation_finished': {e}")


            # --- 2. Devolver los resultados ---
            return results, audit_log

        finally:
            # --- 3. Asegurarnos de cerrar la conexión ---
            self.logger.info("ADAPTADOR: Cerrando la conexión a la base de datos de eventos (si aplica).")
            if self.motor and hasattr(self.motor, 'registro_temporal') and hasattr(self.motor.registro_temporal, 'close'):
                # Añadir verificación por si registro_temporal es None o no tiene 'close'
                try:
                    self.motor.registro_temporal.close()
                except Exception as e:
                    self.logger.warning(f"ADAPTADOR: No se pudo cerrar registro_temporal: {e}")

    # 📍 AÑADE ESTAS DOS FUNCIONES (antes de _pause_all_animations)

    def _destroy_all_visual_effects(self, dialog: Any) -> None:
        """
        🗑️ ELIMINA COMPLETAMENTE todos los efectos visuales para máximo rendimiento. [cite: 7]
        Los efectos se recrearán al finalizar la simulación. [cite: 8]
        """
        try:
            effects_removed = 0
            for canvas_task in dialog.canvas_tasks:
                # Eliminar efecto dorado
                effect = canvas_task.get('golden_glow_effect_widget')
                if effect:
                    effect.stop_animation()
                    effect.deleteLater()
                    canvas_task['golden_glow_effect_widget'] = None
                    effects_removed += 1

                # Eliminar efecto verde
                effect = canvas_task.get('green_cycle_effect_widget')
                if effect:
                    effect.stop_animation()
                    effect.deleteLater()
                    canvas_task['green_cycle_effect_widget'] = None
                    effects_removed += 1

                # Eliminar efecto mixto
                effect = canvas_task.get('mixed_effect_widget')
                if effect:
                    effect.stop_animation()
                    effect.deleteLater()
                    canvas_task['mixed_effect_widget'] = None
                    effects_removed += 1

            self.logger.info(f"✅ {effects_removed} efectos visuales eliminados para optimización")
        except Exception as e:
            self.logger.error(f"Error eliminando efectos visuales: {e}")

    def _restore_all_visual_effects(self, dialog: Any) -> None:
        """
        🎨 RESTAURA todos los efectos visuales basándose en la configuración de cada tarjeta. [cite: 12]
        Se llama al finalizar la simulación en modo alta performance. [cite: 13]
        """
        try:
            self.logger.info("🎨 Restaurando efectos visuales...")

            # Llamar al método existente del diálogo que aplica efectos según config
            if hasattr(dialog, '_update_all_cycle_start_effects'):
                dialog._update_all_cycle_start_effects()

            if hasattr(dialog, '_update_all_cycle_effects'):
                dialog._update_all_cycle_effects()

            self.logger.info("✅ Efectos visuales restaurados")
        except Exception as e:
            self.logger.error(f"Error restaurando efectos: {e}")

    def _pause_all_animations(self, dialog: Any) -> None:
        """Pausa todas las animaciones de efectos visuales durante la simulación."""
        try:
            for canvas_task in dialog.canvas_tasks:
                # Pausar efecto dorado
                effect = canvas_task.get('golden_glow_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.stop()

                # Pausar efecto verde
                effect = canvas_task.get('green_cycle_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.stop()

                # Pausar efecto mixto
                effect = canvas_task.get('mixed_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.stop()

            self.logger.info("✓ Animaciones pausadas para optimizar rendimiento")
        except Exception as e:
            self.logger.warning(f"Error pausando animaciones: {e}")

    def _resume_all_animations(self, dialog: Any) -> None:
        """Reanuda todas las animaciones después de la simulación."""
        try:
            for canvas_task in dialog.canvas_tasks:
                # Reanudar efecto dorado
                effect = canvas_task.get('golden_glow_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.start(30)

                # Reanudar efecto verde
                effect = canvas_task.get('green_cycle_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.start(30)

                # Reanudar efecto mixto
                effect = canvas_task.get('mixed_effect_widget')
                if effect and hasattr(effect, 'animation_timer'):
                    effect.animation_timer.start(30)

            self.logger.info("✓ Animaciones reanudadas")
        except Exception as e:
            self.logger.warning(f"Error reanudando animaciones: {e}")