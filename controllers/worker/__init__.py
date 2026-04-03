# controllers/worker/__init__.py
"""
Coordinación y señales del subsistema «__init__»: enlaza UI, servicios y persistencia para este ámbito de la aplicación Hipatia.
"""

from .controller import WorkerController

__all__ = ["WorkerController"]
