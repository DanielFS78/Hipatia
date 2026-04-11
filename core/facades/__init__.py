# -*- coding: utf-8 -*-
"""
Nombre del Módulo: core.facades

Descripción: Expone ``Facade`` como API estable de aplicación sobre servicios ya inyectados; no contiene reglas de persistencia directa. Integración típica con: ``__future__``, ``core``.
"""

from __future__ import annotations

from core.facades.planning_facade import PlanningFacade
from core.facades.product_facade import ProductFacade

__all__ = ["PlanningFacade", "ProductFacade"]
