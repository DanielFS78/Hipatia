# -*- coding: utf-8 -*-
"""
Constantes usadas por la ventana de arranque (StartupScreen).
Extraídas para reducir LOC del monolito y facilitar tests.
"""

# Colores por estado de verificación (hex, icono, etiqueta)
STATUS_COLORS = {
    "STABLE": ("#27ae60", "✅", "SISTEMA OPERATIVO"),
    "WARNING": ("#f39c12", "⚠️", "ADVERTENCIAS DETECTADAS"),
    "CRITICAL": ("#e74c3c", "❌", "ERRORES CRÍTICOS"),
}

# Segundos de cuenta atrás antes de entrar automáticamente (estado STABLE)
AUTO_ADVANCE_SECONDS = 3
