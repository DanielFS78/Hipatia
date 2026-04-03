# time_calculator.py
"""
Lógica o utilidades del núcleo (`time_calculator`): tipos, servicios auxiliares o infraestructura compartida fuera de la capa de interfaz.
"""

import logging
from datetime import datetime, time, timedelta, date
from typing import Any

class CalculadorDeTiempos:
    """
    Clase robusta para realizar cálculos de tiempo respetando los horarios laborales,
    descansos y días festivos definidos en la configuración.
    
    Matemáticas y Heurísticas (Forward-Iteration):
    El algoritmo evita calcular minuto a minuto (O(N) ineficiente). En su lugar, itera a
    través del tiempo segmentándolo en "bloques ininterrumpidos de trabajo" definidos por:
    - Inicio de jornada (WORK_START_TIME).
    - Descansos predefinidos (parsed_breaks).
    - Fin de jornada (WORK_END_TIME).
    
    Para añadir tiempo, el algoritmo salta al inicio del siguiente bloque continuo.
    Calcula escalarmente el tamaño del bloque frente al saldo de tiempo requerido;
    si el bloque acomoda el saldo entero, se suma algebraicamente, logrando una altísima
    precisión O(1) por salto sobre noches, fines de semana y festivos.
    """

    def __init__(self, schedule_config: Any) -> None:
        self.schedule_config = schedule_config
        self.logger = logging.getLogger(__name__)

        # Pre-procesar los descansos para un acceso más rápido
        self.parsed_breaks = sorted(
            [(datetime.strptime(b['start'], '%H:%M').time(), datetime.strptime(b['end'], '%H:%M').time())
             for b in self.schedule_config.BREAKS],
            key=lambda x: x[0]
        )

    def is_workday(self, current_date: date) -> bool:
        """Verifica si un día es laborable (no es fin de semana ni festivo)."""
        if current_date.weekday() >= 5:  # 5=Sábado, 6=Domingo
            return False
        if current_date in self.schedule_config.HOLIDAYS:
            return False
        return True

    def find_next_workday(self, current_date: date) -> date:
        """Encuentra el siguiente día laborable a partir de una fecha dada."""
        next_day = current_date
        while not self.is_workday(next_day):
            next_day += timedelta(days=1)
        return next_day

    def _move_to_next_valid_work_moment(self, current_dt: datetime) -> datetime:
        """
        Ajusta un datetime al siguiente momento laborable disponible.
        Salta fines de semana, festivos, horarios no laborales y descansos.
        """
        # 1. Asegurarse de que el DÍA es laborable
        work_date = self.find_next_workday(current_dt.date())

        # Si la fecha tuvo que cambiar, empezamos al inicio de la jornada de ese nuevo día
        if work_date != current_dt.date():
            return datetime.combine(work_date, self.schedule_config.WORK_START_TIME)

        current_dt_with_correct_date = datetime.combine(work_date, current_dt.time())

        # 2. Ajustar la HORA al horario laboral
        if current_dt_with_correct_date.time() < self.schedule_config.WORK_START_TIME:
            return datetime.combine(work_date, self.schedule_config.WORK_START_TIME)

        if current_dt_with_correct_date.time() >= self.schedule_config.WORK_END_TIME:
            # Si ya terminó la jornada, saltar al inicio del siguiente día laborable
            next_day = self.find_next_workday(work_date + timedelta(days=1))
            return datetime.combine(next_day, self.schedule_config.WORK_START_TIME)

        # 3. Ajustar para saltar DESCANSOS
        for start_break, end_break in self.parsed_breaks:
            if start_break <= current_dt_with_correct_date.time() < end_break:
                return datetime.combine(work_date, end_break)

        return current_dt_with_correct_date

    def add_work_minutes(self, start_datetime: datetime, minutes_to_add: float) -> datetime:
        """
        Calcula una nueva fecha proyectando Carga de Trabajo (Workload) hacia el futuro.
        
        Matemáticas Puras - Modelo Geométrico de Proyección:
        Dada una carga de trabajo constante req_mins y un calendario de bloques de tiempo B_i:
        
        T_actual = {max(start_datetime, S_0_start)}
        while req_mins > 0:
            S_i = {bloque válido horario actual}
            dT_i = abs(S_i_end - T_actual)
            if dT_i >= req_mins:
                return T_actual + req_mins  (O(1) Aritmética)
            else:
                req_mins = req_mins - dT_i
                T_actual = {saltar_noche_y_descanso_hacia(S_i+1_start)}

        Esta heurística evita calcular `for minute in req_mins: check_is_workday()`.
        Salta segmentos masivos reduciendo la complejidad de O(Minutos) a O(Bloques).
        """
        if minutes_to_add <= 0:
            return start_datetime

        remaining_minutes = minutes_to_add
        # Asegura que el punto de partida sea un momento válido para trabajar
        current_time = self._move_to_next_valid_work_moment(start_datetime)

        while remaining_minutes > 1e-6:  # Usar una pequeña tolerancia para evitar errores de punto flotante
            # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
            self.logger.debug(f"  -> Bucle add_work_minutes:")
            self.logger.debug(f"     Current Time   : {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.debug(f"     Remaining Mins : {remaining_minutes:.4f}")
            # === FIN: AÑADIR LOGS DE DEPURACIÓN ===

            # Límite final del día de trabajo actual
            end_of_day = datetime.combine(current_time.date(), self.schedule_config.WORK_END_TIME)

            # Determinar el final del segmento de trabajo actual (o el inicio del próximo descanso)
            next_event_time = end_of_day
            for start_break, _ in self.parsed_breaks:
                break_time_on_current_day = datetime.combine(current_time.date(), start_break)
                if current_time < break_time_on_current_day < next_event_time:
                    next_event_time = break_time_on_current_day

            # Minutos de trabajo disponibles en este bloque de tiempo ininterrumpido
            minutes_in_segment = (next_event_time - current_time).total_seconds() / 60

            # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
            self.logger.debug(f"     Next Event Time: {next_event_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.debug(f"     Mins in Segment: {minutes_in_segment:.4f}")
            # === FIN: AÑADIR LOGS DE DEPURACIÓN ===

            if minutes_in_segment >= remaining_minutes:
                # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
                self.logger.debug(f"     Remaining fits in segment. Adding {remaining_minutes:.4f} mins.")
                # === FIN: AÑADIR LOGS DE DEPURACIÓN ===
                current_time += timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
                self.logger.debug(
                    f"     Remaining ({remaining_minutes:.4f}) > segment ({minutes_in_segment:.4f}). Consuming segment.")
                # === FIN: AÑADIR LOGS DE DEPURACIÓN ===
                remaining_minutes -= minutes_in_segment
                current_time = self._move_to_next_valid_work_moment(next_event_time)
                # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
                self.logger.debug(f"     Moved to next valid time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                # === FIN: AÑADIR LOGS DE DEPURACIÓN ===

            # === INICIO: AÑADIR LOGS DE DEPURACIÓN ===
        self.logger.debug(f"  <- Fin add_work_minutes. Returning: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        # === FIN: AÑADIR LOGS DE DEPURACIÓN ===
        return current_time

    def count_workdays(self, start_dt: datetime, end_dt: datetime) -> int:
        """Cuenta los días laborables entre dos fechas."""
        if not start_dt or not end_dt or start_dt.date() > end_dt.date():
            return 0

        days = 0
        current_date = start_dt.date()
        while current_date <= end_dt.date():
            if self.is_workday(current_date):
                days += 1
            current_date += timedelta(days=1)
        return days

    def calculate_work_minutes_between(self, start_datetime: datetime, end_datetime: datetime) -> float:
        """
        Calcula los minutos REALES de trabajo (W_total) entre dos instantes de tiempo espaciados (t0, t1).
        
        Cálculo Integral Analítico - Segmentación Temporal:
        El lapso total Delta(t) = t1 - t0 se intersecta con la función bool is_working(T).
        Para evitar iteración continua, se aplica el Teorema de Superposición de Intervalos:
        
        B = Conjunto de bloques ininterrumpidos laborales en el calendario
        W_total = Sumatoria(para cada i en B) de [ min(t1, B_i.end) - max(t0, B_i.start) ]
        
        La sumatoria ignora matemáticamente aquellos subconjuntos donde max > min
        (es decir, saltos completos de domingos o madrugadas sin colisión métrica),
        permitiendo resolver lapsos de meses en milisegundos O(días_afectados).

        Args:
            start_datetime: Fecha y hora de inicio (t0).
            end_datetime: Fecha y hora de fin (t1).

        Returns:
            float: Sumatoria escalar (W_total) de los minutos de intersección válidos.
        """
        if not start_datetime or not end_datetime:
            return 0.0

        if start_datetime >= end_datetime:
            return 0.0

        total_minutes = 0.0

        # Ajustar el inicio al siguiente momento laboral válido
        current_time = self._move_to_next_valid_work_moment(start_datetime)

        # Si el inicio ajustado ya está después del fin, no hay tiempo trabajado
        if current_time >= end_datetime:
            return 0.0

        # Iterar por bloques de tiempo hasta llegar al fin
        while current_time < end_datetime:
            # Límite final del día de trabajo actual
            end_of_day = datetime.combine(current_time.date(), self.schedule_config.WORK_END_TIME)

            # Determinar el final del segmento de trabajo actual
            next_event_time = end_of_day
            for start_break, _ in self.parsed_breaks:
                break_time_on_current_day = datetime.combine(current_time.date(), start_break)
                if current_time < break_time_on_current_day < next_event_time:
                    next_event_time = break_time_on_current_day

            # El segmento termina donde llegue primero: el evento o la hora final buscada
            segment_end = min(next_event_time, end_datetime)

            # Calcular minutos trabajados en este segmento
            if segment_end > current_time:
                minutes_in_segment = (segment_end - current_time).total_seconds() / 60
                total_minutes += minutes_in_segment

            # Si ya llegamos al final, terminamos
            if segment_end >= end_datetime:
                break

            # Si no, saltamos al siguiente momento laboral válido
            current_time = self._move_to_next_valid_work_moment(segment_end)

            # Protección contra bucles infinitos
            if current_time >= end_datetime:
                break

        return round(total_minutes, 2)