# -*- coding: utf-8 -*-
"""Bridges de compatibilidad para AppModel por dominio.

Encapsulan la API legacy sobre :class:`core.facades.product_facade.ProductFacade`,
:class:`core.facades.planning_facade.PlanningFacade` y ``SystemIntegrationService``.
"""

from __future__ import annotations

from core.app_model_bridges.compat import AppModelCompatBridge
from core.app_model_bridges.planning import AppModelPlanningBridge
from core.app_model_bridges.product import AppModelProductBridge

__all__ = [
    "AppModelCompatBridge",
    "AppModelPlanningBridge",
    "AppModelProductBridge",
]
