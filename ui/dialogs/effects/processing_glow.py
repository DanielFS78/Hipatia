# -*- coding: utf-8 -*-
"""
Nombre del Módulo: ui.dialogs.effects.processing_glow
Descripción: Efecto visual o animación para el canvas de flujo o simulación (pintado con QTimer).
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen
from typing import Any

class ProcessingGlowEffect(QWidget):
    """
    Widget que dibuja un círculo naranja pulsante alrededor de una tarjeta
    para indicar que está siendo procesada por la simulación.
    
    Rendimiento Visual y Optimización Matemática:
    El efecto de respiración (pulso) se basa en la interpolación lineal algorítmica
    del canal alfa de colores directos sobre capas progresivamente concéntricas.
    Para salvaguardar el Frame-Rate durante simulaciones pesadas (en threads remotos), 
    este componente permanece aislado en el Thread Principal, siendo inerte a clicks, 
    gestionando la opacidad en una variable `pulse_value` que repinta (`drawEllipse`) 
    a golpe de latidos guiados por el `QEventLoop` del sistema, evitando atascos.
    """

    def __init__(self, parent_card: Any) -> None:
        # El padre debe ser el canvas, no la tarjeta
        super().__init__(parent_card.parent())
        self.parent_card = parent_card
        self.pulse_value = 0  # Controla la intensidad del pulso (0 a 100)
        self.pulse_direction = 1  # 1 para aumentar, -1 para disminuir

        # Configurar geometría inicial y hacerlo invisible a eventos de ratón
        self._update_geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()
        # Asegurar que esté por encima de la tarjeta
        self.raise_()

        # Conectar a la señal 'moved' de la tarjeta para reposicionar el efecto
        if hasattr(self.parent_card, 'moved'):
            try:
                # Desconectar primero por si acaso
                self.parent_card.moved.disconnect(self._update_geometry)
            except TypeError:
                pass  # No estaba conectado
            self.parent_card.moved.connect(self._update_geometry)

    def _update_geometry(self) -> None:
        """Actualiza posición y tamaño para rodear la tarjeta."""
        if not self.parent_card or not self.parent_card.isVisible():  # Comprobar si la tarjeta existe y es visible
            self.hide()
            return
        card_rect = self.parent_card.geometry()
        margin = 20  # Espacio extra alrededor de la tarjeta para el efecto

        self.setGeometry(
            card_rect.x() - margin,
            card_rect.y() - margin,
            card_rect.width() + 2 * margin,
            card_rect.height() + 2 * margin
        )

    def paintEvent(self, event: Any) -> None:
        """Dibuja el círculo naranja pulsante con efecto neón."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Color naranja base
        base_orange = QColor(255, 140, 0)

        # Centro y radio del círculo
        center_x = self.width() // 2
        center_y = self.height() // 2
        # Usar min() para asegurar que sea circular si el widget no es cuadrado
        radius = min(self.width(), self.height()) // 2 - 5  # Radio base

        # Dibujar múltiples círculos concéntricos para efecto neón
        num_layers = 4  # Número de capas de brillo
        for i in range(num_layers):
            # Calcular alpha basado en el pulso y la capa
            # La capa interna (i=0) es la más brillante y pulsante
            # Las capas externas (i>0) son más tenues y pulsan menos
            layer_pulse_factor = 1.0 - (i * 0.2)  # Reduce el efecto de pulso para capas externas
            base_alpha = 150 - (i * 40)  # Alpha base disminuye para capas externas
            pulse_alpha_variation = 80 * layer_pulse_factor  # Cuánto varía el alpha con el pulso
            current_alpha = int(base_alpha + (self.pulse_value / 100.0) * pulse_alpha_variation)

            # Asegurar que alpha esté en el rango válido [0, 255]
            current_alpha = max(0, min(255, current_alpha))

            # Ancho del pen disminuye para capas externas
            pen_width = max(1, num_layers - i)

            # Crear color y pen
            layer_color = QColor(base_orange.red(), base_orange.green(), base_orange.blue(), current_alpha)
            pen = QPen(layer_color, pen_width)

            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # Sin relleno

            # Dibujar el círculo (elipse)
            # Las capas externas son ligeramente más grandes
            current_radius = radius + i
            painter.drawEllipse(
                center_x - current_radius,
                center_y - current_radius,
                current_radius * 2,
                current_radius * 2
            )

    def stop_animation(self) -> None:
        """Detiene la animación del pulso."""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
