"""
Nombre del Módulo: core.health.constants

Descripción: Concentra datos de configuración o catálogos estáticos: ``CRITICAL_TABLES``, ``THRESHOLDS``, consumidos por la UI y controladores.
"""

TABLE_FRIENDLY: dict[str, tuple[str, str]] = {
    "trabajadores": ("Trabajadores", "Operarios y administradores del sistema"),
    "productos": ("Catálogo de Productos", "Productos con tiempos y procesos de fabricación"),
    "fabricaciones": ("Órdenes de Fabricación", "Órdenes de trabajo activas y completadas"),
    "maquinas": ("Máquinas", "Recursos físicos de planta disponibles"),
    "materiales": ("Materiales", "Materias primas y componentes (BOM)"),
    "preprocesos": ("Preprocesos", "Tareas preparatorias reutilizables"),
    "pilas": ("Planes de Producción", "Planes de simulación y optimización"),
    "lotes": ("Lotes", "Agrupaciones logísticas de fabricaciones"),
    "grupos_preparacion": ("Preparación de Máquinas", "Pasos de setup y preparación de máquinas"),
    "tracking_logs": ("Trazabilidad", "Registro de tiempos y movimientos en planta"),
    "audit_logs": ("Auditoría", "Historial de acciones del sistema"),
}

CRITICAL_TABLES = {"trabajadores", "productos", "maquinas"}

THRESHOLDS = {
    "stable_pass_rate": 0.95,
    "warning_pass_rate": 0.80,
}
