# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui_scaler.py
Descripción: Proporciona la lógica matemática y de generación de estilos 
             para el escalado dinámico de la interfaz gráfica en función de la resolución,
             permitiendo que la aplicación se adapte a pantallas pequeñas (como portátiles).
"""

import math
from typing import Optional, Any
import logging
from typing import cast

class UIScaler:
    """
    Motor encargado de calcular factores de escala para la interfaz de usuario
    y generar hojas de estilo dinámicas (QSS) para mejorar la visualización en 
    diferentes resoluciones de pantalla.
    """
    
    BASE_HEIGHT = 1080.0
    MIN_SCALE = 0.6
    MAX_SCALE = 1.2
    
    @classmethod
    def calculate_scale_factor(cls, screen_height: int) -> float:
        """
        Calcula el factor de escala basado en la altura de la pantalla disponible.
        
        Args:
            screen_height: Altura disponible de la pantalla en píxeles.
            
        Returns:
            Un multiplicador (float) entre MIN_SCALE y MAX_SCALE.
        """
        if screen_height <= 0:
            logging.warning("Altura de pantalla inválida o nula proporcionada a UIScaler. Usando factor 1.0.")
            return 1.0
            
        factor = screen_height / cls.BASE_HEIGHT
        
        # Clamp value between MIN_SCALE and MAX_SCALE
        clamped_factor = max(cls.MIN_SCALE, min(factor, cls.MAX_SCALE))
        
        # Round to 2 decimal places for cleaner QSS
        return round(clamped_factor, 2)

    @classmethod
    def generate_dynamic_qss(cls, scale_factor: float) -> str:
        """
        Genera un bloque global de QSS (hoja de estilos Qt) con tamaños 
        ajustados en función del factor de escala.
        
        Args:
            scale_factor: El factor de escala previamente calculado.
            
        Returns:
            Una cadena de texto con el CSS/QSS dinámico listo para inyectar en QApplication.
        """
        # Definición base (1080p)
        base_font_size = 14
        h1_font_size = 24
        h2_font_size = 18
        h3_font_size = 16
        small_font_size = 12
        
        base_padding = 10
        small_padding = 5
        large_padding = 15
        
        base_margin = 10
        
        # Aplicamos el factor y aseguramos que sean enteros
        f_base = max(8, int(round(base_font_size * scale_factor)))
        f_h1 = max(14, int(round(h1_font_size * scale_factor)))
        f_h2 = max(12, int(round(h2_font_size * scale_factor)))
        f_h3 = max(10, int(round(h3_font_size * scale_factor)))
        f_small = max(8, int(round(small_font_size * scale_factor)))
        
        p_base = max(2, int(round(base_padding * scale_factor)))
        p_small = max(1, int(round(small_padding * scale_factor)))
        p_large = max(5, int(round(large_padding * scale_factor)))
        
        m_base = max(2, int(round(base_margin * scale_factor)))
        
        qss = f"""
        /* 
         * Hoja de Estilos Dinámica - Generada por UIScaler
         * Factor de Escala: {scale_factor}
         */
         
        QWidget {{
            font-size: {f_base}px;
        }}
        
        QPushButton {{
            padding: {p_base}px {p_large}px;
            margin: {p_small}px;
        }}
        
        QLabel {{
            margin: {p_small}px;
        }}
        
        /* Títulos (Convención usando objectName parcial o clases no estándar en Qt, 
           pero lo dejamos preparado para asignaciones directas o herencias) */
        QLabel[heading="h1"] {{
            font-size: {f_h1}px;
            font-weight: bold;
        }}
        
        QLabel[heading="h2"] {{
            font-size: {f_h2}px;
            font-weight: bold;
        }}
        
        QLabel[heading="h3"] {{
            font-size: {f_h3}px;
            font-weight: bold;
        }}
        
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
            padding: {p_small}px;
            font-size: {f_base}px;
        }}
        
        /* Paneles y Layouts base */
        QFrame[frameShape="1"], QFrame[frameShape="2"], QFrame[frameShape="3"], QFrame[frameShape="4"], QFrame[frameShape="5"], QFrame[frameShape="6"] {{
            margin: {m_base}px;
            padding: {p_base}px;
        }}
        """
        
        return qss

    @classmethod
    def get_current_screen_height(cls, active_widget: Any) -> int:
        """
        Intenta obtener la altura útil (available resolution) de la pantalla
        donde actualmente reside el widget proporcionado.
        
        Args:
            active_widget: Instancia de un QWidget visible (como MainView).
            
        Returns:
            Altura de la pantalla en píxeles o cls.BASE_HEIGHT si falla.
        """
        try:
            screen = active_widget.screen()
            if screen is not None:
                rect = screen.availableGeometry()
                return cast(int, rect.height())
                
            # Fallback en caso de que .screen() no devuelva nada
            from PyQt6.QtWidgets import QApplication
            app = cast(QApplication | None, QApplication.instance())
            if app is not None:
                primary_screen = app.primaryScreen()
                if primary_screen is not None:
                    return primary_screen.availableGeometry().height()
                    
        except Exception as e:
            logging.error(f"Error obteniendo altura de pantalla en UIScaler: {e}")
            
        return int(cls.BASE_HEIGHT)
