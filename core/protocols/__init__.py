# -*- coding: utf-8 -*-
"""Protocolos de dominio compartidos (servicios). Implementados nominalmente en `core.services`."""

from core.protocols.domain import IFabricacionService, IMaterialService, IProductService

__all__ = ["IFabricacionService", "IMaterialService", "IProductService"]
