# =================================================================================
# ui/dialogs/visual_effects.py
# Contiene los efectos visuales para las tarjetas del flujo de producción.
# =================================================================================

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient


class GoldenGlowEffect(QWidget):
    """
    Widget que dibuja un círculo dorado giratorio alrededor de una tarjeta
    para indicar que es una tarea de inicio de ciclo.
    """

    def __init__(self, parent_card):
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

    def eventFilter(self, obj, event):
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

    def _update_geometry(self):
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

    def paintEvent(self, event):
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

    def stop_animation(self):
        """Detiene la animación y limpia recursos."""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()

        # Remover filtros de eventos
        if self.parent_card:
            self.parent_card.removeEventFilter(self)
        if self.parent():
            self.parent().removeEventFilter(self)


class SimulationProgressEffect(QWidget):
    """
    Widget que dibuja un aro azulado grisáceo giratorio con efecto neón
    para indicar que una tarjeta está siendo procesada por la simulación.
    """

    def __init__(self, parent_card):
        # El padre debe ser el canvas (el contenedor de las tarjetas)
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        # Instalar filtro de eventos en la tarjeta padre
        self.parent_card.installEventFilter(self)

        # También instalar filtro en el canvas
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        # Configurar geometría inicial
        self._update_geometry()

        # Hacer invisible a eventos de ratón
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Mostrar y asegurar que esté por encima
        self.show()
        self.raise_()

    def eventFilter(self, obj, event):
        """Filtra eventos para actualizar geometría cuando sea necesario."""
        if obj == self.parent_card:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                QEvent.Type.Show, QEvent.Type.Hide):
                self._update_geometry()
                return False

        if obj == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
                self._update_geometry()
                return False

        return super().eventFilter(obj, event)

    def _update_geometry(self):
        """Actualiza posición y tamaño para rodear la tarjeta."""
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return

        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 20  # Ligeramente más grande que el efecto dorado

        card_pos = self.parent_card.pos()
        card_size = self.parent_card.size()

        self.setGeometry(
            card_pos.x() - margin,
            card_pos.y() - margin,
            card_size.width() + 2 * margin,
            card_size.height() + 2 * margin
        )

        self.show()
        self.raise_()

    def paintEvent(self, event):
        """Dibuja un efecto neón azulado con luz circulante continua."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensiones del rectángulo interno
        margin = 20
        inner_rect_x = margin
        inner_rect_y = margin
        inner_rect_w = self.width() - 2 * margin
        inner_rect_h = self.height() - 2 * margin


class GreenCycleEffect(QWidget):
    """
    Widget que dibuja un aro verde con efecto neón para tareas intermedias del ciclo.
    """

    def __init__(self, parent_card):
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        # Instalar filtro de eventos
        self.parent_card.installEventFilter(self)
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        self._update_geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()
        self.raise_()

    def eventFilter(self, obj, event):
        if obj == self.parent_card:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                QEvent.Type.Show, QEvent.Type.Hide):
                self._update_geometry()
                return False
        if obj == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
                self._update_geometry()
                return False
        return super().eventFilter(obj, event)

    def _update_geometry(self):
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return
        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 15
        card_pos = self.parent_card.pos()
        card_size = self.parent_card.size()

        self.setGeometry(
            card_pos.x() - margin,
            card_pos.y() - margin,
            card_size.width() + 2 * margin,
            card_size.height() + 2 * margin
        )
        self.show()
        self.raise_()

    def paintEvent(self, event):
        """Efecto neón verde ESTÁTICO (sin animación)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 15
        inner_rect = QRectF(
            margin, margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )
        corner_radius = 10

        # Solo 3 capas
        for i in range(3, 0, -1):
            alpha = int(80 * (1 - i / 3))
            pen_width = max(1, 4 - i)

            layer_color = QColor(40, 167, 69, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = i * 2
            current_rect = inner_rect.adjusted(-expansion, -expansion, expansion, expansion)
            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # Línea central
        painter.setPen(QPen(QColor(40, 167, 69, 255), 2))
        painter.drawRoundedRect(inner_rect, corner_radius, corner_radius)

    def stop_animation(self):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        if self.parent_card:
            self.parent_card.removeEventFilter(self)
        if self.parent():
            self.parent().removeEventFilter(self)


class MixedGoldGreenEffect(QWidget):
    """
    Widget que dibuja un aro con efecto mixto dorado-verde para tareas finales de ciclo.
    """

    def __init__(self, parent_card):
        canvas_parent = parent_card.parent()
        super().__init__(canvas_parent)
        self.parent_card = parent_card
        self.rotation_angle = 0

        self.parent_card.installEventFilter(self)
        if canvas_parent:
            canvas_parent.installEventFilter(self)

        self._update_geometry()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()
        self.raise_()

    def eventFilter(self, obj, event):
        if obj == self.parent_card:
            if event.type() in (QEvent.Type.Move, QEvent.Type.Resize,
                                QEvent.Type.Show, QEvent.Type.Hide):
                self._update_geometry()
                return False
        if obj == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
                self._update_geometry()
                return False
        return super().eventFilter(obj, event)

    def _update_geometry(self):
        if not self.parent_card or not self.parent_card.isVisible():
            self.hide()
            return
        canvas = self.parent()
        if not canvas:
            self.hide()
            return

        margin = 15
        card_pos = self.parent_card.pos()
        card_size = self.parent_card.size()

        self.setGeometry(
            card_pos.x() - margin,
            card_pos.y() - margin,
            card_size.width() + 2 * margin,
            card_size.height() + 2 * margin
        )
        self.show()
        self.raise_()

    def paintEvent(self, event):
        """Efecto neón mixto ESTÁTICO (sin animación)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 15
        inner_rect = QRectF(
            margin, margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )
        corner_radius = 10

        # Capas doradas (izquierda/arriba)
        for i in range(3, 0, -1):
            alpha = int(60 * (1 - i / 3))
            pen_width = max(1, 4 - i)

            layer_color = QColor(255, 215, 0, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = i * 2
            current_rect = inner_rect.adjusted(-expansion, -expansion, expansion, expansion)
            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # Capas verdes (derecha/abajo)
        for i in range(3, 0, -1):
            alpha = int(60 * (1 - i / 3))
            pen_width = max(1, 4 - i)

            layer_color = QColor(40, 167, 69, alpha)
            pen = QPen(layer_color, pen_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            expansion = i * 1.5  # Ligeramente diferente para mezcla
            current_rect = inner_rect.adjusted(-expansion, -expansion, expansion, expansion)
            painter.drawRoundedRect(current_rect, corner_radius + i, corner_radius + i)

        # Línea central mixta (un color intermedio)
        painter.setPen(QPen(QColor(147, 191, 39, 255), 2))  # Verde-amarillento
        painter.drawRoundedRect(inner_rect, corner_radius, corner_radius)

    def stop_animation(self):
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        if self.parent_card:
            self.parent_card.removeEventFilter(self)
        if self.parent():
            self.parent().removeEventFilter(self)


class ProcessingGlowEffect(QWidget):
    """
    Widget que dibuja un círculo naranja pulsante alrededor de una tarjeta
    para indicar que está siendo procesada por la simulación.
    """

    def __init__(self, parent_card):
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

    def _update_geometry(self):
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

    def paintEvent(self, event):
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

    def stop_animation(self):
        """Detiene la animación del pulso."""
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
