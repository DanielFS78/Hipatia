"""
Tests unitarios para ui/dialogs/effects/*.
Cubre las clases de efectos visuales tras la modularización.
"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QEvent

# ==============================================================================
# Helpers — real QWidget parents
# ==============================================================================
@pytest.fixture
def parent_widgets(qapp):
    """Crea un canvas y card reales para los tests."""
    canvas = QWidget()
    canvas.resize(400, 300)
    card = QWidget(canvas)
    card.setGeometry(10, 10, 100, 50)
    card.show()
    canvas.show()
    yield card, canvas
    # No usamos deleteLater() aquí para evitar ruidos en el bucle de eventos durante el teardown
    # El recolector de basura se encargará o el qapp al cerrar.
    # O mejor, cerramos explícitamente.
    card.close()
    canvas.close()

# ==============================================================================
# TEST CLASS: GoldenGlowEffect
# ==============================================================================
@pytest.mark.unit
class TestGoldenGlowEffect:
    MOD = "ui.dialogs.effects.golden_glow"

    def test_init_basic(self, parent_widgets):
        from ui.dialogs.effects.golden_glow import GoldenGlowEffect
        card, canvas = parent_widgets
        effect = GoldenGlowEffect(card)
        assert effect.parent_card is card
        assert effect.rotation_angle == 0
        effect.close()

    def test_paint_event(self, parent_widgets):
        from ui.dialogs.effects.golden_glow import GoldenGlowEffect
        card, canvas = parent_widgets
        with patch(f"{self.MOD}.QPainter") as mock_painter, \
             patch(f"{self.MOD}.QColor"), \
             patch(f"{self.MOD}.QPen"), \
             patch(f"{self.MOD}.QBrush"), \
             patch(f"{self.MOD}.QConicalGradient"):
            effect = GoldenGlowEffect(card)
            effect.paintEvent(MagicMock(spec=[]))
            effect.close()
        # paintEvent invoca QPainter para renderizar el efecto
        mock_painter.assert_called()

    def test_event_filter(self, parent_widgets):
        from ui.dialogs.effects.golden_glow import GoldenGlowEffect
        card, canvas = parent_widgets
        effect = GoldenGlowEffect(card)
        event = MagicMock(spec=QEvent)
        event.type.return_value = QEvent.Type.Move
        assert effect.eventFilter(card, event) is False
        effect.close()

# ==============================================================================
# TEST CLASS: SimulationProgressEffect
# ==============================================================================
@pytest.mark.unit
class TestSimulationProgressEffect:
    MOD = "ui.dialogs.effects.progress"

    def test_init(self, parent_widgets):
        from ui.dialogs.effects.progress import SimulationProgressEffect
        card, canvas = parent_widgets
        effect = SimulationProgressEffect(card)
        assert effect.parent_card is card
        effect.close()

    def test_paint_event(self, parent_widgets):
        from ui.dialogs.effects.progress import SimulationProgressEffect
        card, canvas = parent_widgets
        with patch(f"{self.MOD}.QPainter") as mock_painter, \
             patch(f"{self.MOD}.QColor"), \
             patch(f"{self.MOD}.QPen"):
            effect = SimulationProgressEffect(card)
            effect.paintEvent(MagicMock(spec=[]))
            effect.close()
        mock_painter.assert_called()

# ==============================================================================
# TEST CLASS: GreenCycleEffect
# ==============================================================================
@pytest.mark.unit
class TestGreenCycleEffect:
    MOD = "ui.dialogs.effects.green_cycle"

    def test_init(self, parent_widgets):
        from ui.dialogs.effects.green_cycle import GreenCycleEffect
        card, canvas = parent_widgets
        effect = GreenCycleEffect(card)
        assert effect.parent_card is card
        effect.close()

    def test_paint_event(self, parent_widgets):
        from ui.dialogs.effects.green_cycle import GreenCycleEffect
        card, canvas = parent_widgets
        with patch(f"{self.MOD}.QPainter") as mock_painter, \
             patch(f"{self.MOD}.QColor"), \
             patch(f"{self.MOD}.QPen"):
            effect = GreenCycleEffect(card)
            effect.paintEvent(MagicMock(spec=[]))
            effect.close()
        mock_painter.assert_called()

# ==============================================================================
# TEST CLASS: MixedGoldGreenEffect
# ==============================================================================
@pytest.mark.unit
class TestMixedGoldGreenEffect:
    MOD = "ui.dialogs.effects.mixed_gold_green"

    def test_init(self, parent_widgets):
        from ui.dialogs.effects.mixed_gold_green import MixedGoldGreenEffect
        card, canvas = parent_widgets
        effect = MixedGoldGreenEffect(card)
        assert effect.parent_card is card
        effect.close()

    def test_paint_event(self, parent_widgets):
        from ui.dialogs.effects.mixed_gold_green import MixedGoldGreenEffect
        card, canvas = parent_widgets
        with patch(f"{self.MOD}.QPainter") as mock_painter, \
             patch(f"{self.MOD}.QColor"), \
             patch(f"{self.MOD}.QPen"):
            effect = MixedGoldGreenEffect(card)
            effect.paintEvent(MagicMock(spec=[]))
            effect.close()
        mock_painter.assert_called()

# ==============================================================================
# TEST CLASS: ProcessingGlowEffect
# ==============================================================================
@pytest.mark.unit
class TestProcessingGlowEffect:
    MOD = "ui.dialogs.effects.processing_glow"

    def test_init(self, parent_widgets):
        from ui.dialogs.effects.processing_glow import ProcessingGlowEffect
        card, canvas = parent_widgets
        effect = ProcessingGlowEffect(card)
        assert effect.parent_card is card
        effect.close()

    def test_paint_event(self, parent_widgets):
        from ui.dialogs.effects.processing_glow import ProcessingGlowEffect
        card, canvas = parent_widgets
        with patch(f"{self.MOD}.QPainter") as mock_painter, \
             patch(f"{self.MOD}.QColor"), \
             patch(f"{self.MOD}.QPen"):
            effect = ProcessingGlowEffect(card)
            effect.paintEvent(MagicMock(spec=[]))
            effect.close()
        mock_painter.assert_called()
