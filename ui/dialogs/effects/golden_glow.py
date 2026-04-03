"""
Interfaz PyQt6 (`golden_glow`): widgets, diálogos o recursos visuales conectados al flujo de usuario.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient
from typing import Any

class GoldenGlowEffect(QWidget):
    """
    Widget que dibuja un círculo dorado giratorio alrededor de una tarjeta
    para indicar que es una tarea de inicio de ciclo.
    
    Rendimiento Visual (UI y Concurrencia):
    Dado que este widget pinta gradientes cónicos (QConicalGradient) constantemente 
    para simular un hilo de luz (efecto neón girando a 60 FPS), su arquitectura aísla 
    el dibujo delegando la iteración al EventLoop de PyQt6. En lugar de un loop 
    `while` bloqueante, se apoya en un `QTimer` que dispara señales intermitentes de  
    `update()` motivando a `paintEvent` sólo a demanda, minimizando la huella de CPU. 
    Usa EventFilters en sus padres para recálculos morfológicos "Lazy" optimizados.
    """

    def __init__(self, parent_card: Any) -> None:
        # El padre debe ser el canvas (el contenedor de las tarjetas)
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        # CRÍTICO: Instalar filtro de eventos en la tarjeta padre para detectar movimientos
        self.parent_card.installEventFilter(self)

        # También instalar filtro en el canvas para detectar scrolls o cambios
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        # Configurar geometría inicial
        self._update_geometry()

        # Hacer invisible a eventos de ratón para que no bloquee clicks en las tarjetas
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Mostrar y asegurar que esté por encima
        self.show()
        self.raise_()

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """
        Filtra eventos de la tarjeta padre y del canvas para actualizar la geometría
        cuando sea necesario.
        """
        # Si la tarjeta padre se mueve, cambia de tamaño, o se muestra/oculta
        if obj == self.parent_card:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                QEvent.Type.Show, QEvent.Type.Hide):
                self._update_geometry()
                return False

        # Si el canvas hace scroll o cambia de tamaño
        if obj == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
                self._update_geometry()
                return False

        return super().eventFilter(obj, event)

    def _update_geometry(self) -> None:
        """
        Actualiza posición y tamaño para rodear la tarjeta.
        CORREGIDO: Usa mapTo() para obtener las coordenadas correctas relativas al canvas.
        """
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return

        # Verificar que el padre del efecto (canvas) existe
        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 15  # Espacio alrededor de la tarjeta

        # CORRECCIÓN CRÍTICA: Obtener la posición de la tarjeta relativa al canvas
        # usando mapTo() en lugar de geometry() directamente
        card_pos = self.parent_card.pos()
        card_size = self.parent_card.size()

        # Establecer la geometría del efecto
        self.setGeometry(
            card_pos.x() - margin,
            card_pos.y() - margin,
            card_size.width() + 2 * margin,
            card_size.height() + 2 * margin
        )

        # Asegurar que esté visible y por encima
        self.show()
        self.raise_()

    def paintEvent(self, event: Any) -> None:
        """Dibuja un efecto neón con luz circulante continua, sin puntos discretos."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensiones del rectángulo interno
        margin = 15
        inner_rect_x = margin
        inner_rect_y = margin
        inner_rect_w = self.width() - 2 * margin
        inner_rect_h = self.height() - 2 * margin
        corner_radius = 10

        # Centro del rectángulo para el gradiente cónico
        center_x = inner_rect_x + inner_rect_w / 2
        center_y = inner_rect_y + inner_rect_h / 2

        # ✨ Capa base: Resplandor neón estático
        num_layers = 6
        for i in range(num_layers, 0, -1):
            alpha = int(100 * (1 - i / num_layers))
            pen_width = max(1, 5 - i)

            layer_color = QColor(255, 215, 0, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = i * 2
            current_rect = QRectF(
                inner_rect_x - expansion,
                inner_rect_y - expansion,
                inner_rect_w + 2 * expansion,
                inner_rect_h + 2 * expansion
            )

            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # ✨ NUEVO: Hilo de luz circulante INTERIOR
        gradient_inner = QConicalGradient(center_x, center_y, self.rotation_angle)
        gradient_inner.setColorAt(0.0, QColor(255, 255, 255, 200))  # Blanco brillante
        gradient_inner.setColorAt(0.15, QColor(255, 230, 100, 200))  # ✨ Amarillo más intenso
        gradient_inner.setColorAt(0.3, QColor(255, 200, 0, 130))  # ✨ Dorado más saturado
        gradient_inner.setColorAt(0.5, QColor(255, 215, 0, 30))  # Muy transparente
        gradient_inner.setColorAt(0.7, QColor(255, 200, 0, 130))  # ✨ Dorado más saturado
        gradient_inner.setColorAt(0.85, QColor(255, 230, 100, 200))  # ✨ Amarillo más intenso
        gradient_inner.setColorAt(1.0, QColor(255, 255, 255, 200))  # Blanco brillante

        pen_inner = QPen(QBrush(gradient_inner), 3)
        pen_inner.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_inner)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        inner_light_rect = QRectF(
            inner_rect_x,
            inner_rect_y,
            inner_rect_w,
            inner_rect_h
        )
        painter.drawRoundedRect(inner_light_rect, corner_radius, corner_radius)

        # ✨ NUEVO: Hilo de luz circulante EXTERIOR (más separado y con rotación opuesta)
        gradient_outer = QConicalGradient(center_x, center_y, -self.rotation_angle)  # Rotación inversa
        gradient_outer.setColorAt(0.0, QColor(255, 255, 255, 150))  # Blanco brillante
        gradient_outer.setColorAt(0.15, QColor(255, 230, 100, 150))  # ✨ Amarillo más intenso
        gradient_outer.setColorAt(0.3, QColor(255, 200, 0, 100))  # ✨ Dorado más saturado
        gradient_outer.setColorAt(0.5, QColor(255, 215, 0, 20))  # Muy transparente
        gradient_outer.setColorAt(0.7, QColor(255, 200, 0, 100))  # ✨ Dorado más saturado
        gradient_outer.setColorAt(0.85, QColor(255, 230, 100, 150))  # ✨ Amarillo más intenso
        gradient_outer.setColorAt(1.0, QColor(255, 255, 255, 150))  # Blanco brillante

        pen_outer = QPen(QBrush(gradient_outer), 2.5)
        pen_outer.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        outer_expansion = 8
        outer_light_rect = QRectF(
            inner_rect_x - outer_expansion,
            inner_rect_y - outer_expansion,
            inner_rect_w + 2 * outer_expansion,
            inner_rect_h + 2 * outer_expansion
        )
        painter.drawRoundedRect(outer_light_rect, corner_radius + outer_expansion, corner_radius + outer_expansion)

    def stop_animation(self) -> None:
        """Detiene la animación y limpia recursos."""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        # Remover filtros de eventos
        if self.parent_card:
            self.parent_card.removeEventFilter(self)
        parent = self.parent()
        if parent:
            parent.removeEventFilter(self)
