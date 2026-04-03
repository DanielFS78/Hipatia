# -*- coding: utf-8 -*-
"""Tests unitarios para la utilidad de escalado dinámico (UIScaler).

Cubre calculate_scale_factor (1080p, 768p, límites min/max, entrada inválida),
generate_dynamic_qss y get_current_screen_height (widget.screen, fallback QApplication,
fallback por excepción). Decisión de mocking: mocks de widget/screen/rect con spec de
métodos usados (sin autospec en clases Qt).
"""
import pytest
from unittest.mock import MagicMock, patch
from core.utils.ui_scaler import UIScaler

pytestmark = pytest.mark.unit


class TestUIScaler:
    """Suite de pruebas unitarias para la clase UIScaler."""
    
    def test_calculate_scale_factor_standard_1080p(self) -> None:
        """Verifica que una altura estándar de 1080p devuelve factor 1.0."""
        assert UIScaler.calculate_scale_factor(1080) == 1.0
        
    def test_calculate_scale_factor_laptop_768p(self) -> None:
        """Verifica que una altura típica de portátil (768p) devuelve un factor reducido proporcionado."""
        factor = UIScaler.calculate_scale_factor(768)
        assert factor == 0.71  # 768 / 1080 = 0.7111... rounded to 2 is 0.71
        
    def test_calculate_scale_factor_min_limit(self) -> None:
        """Verifica que la reducción extrema está limitada por MIN_SCALE (0.6)."""
        factor = UIScaler.calculate_scale_factor(480)
        assert factor == 0.6
        
    def test_calculate_scale_factor_max_limit(self) -> None:
        """Verifica que el aumento extremo en 4k está limitado por MAX_SCALE (1.2)."""
        factor = UIScaler.calculate_scale_factor(2160)
        assert factor == 1.2
        
    def test_calculate_scale_factor_invalid_input(self) -> None:
        """Verifica que con entradas nulas o negativas se devuelve 1.0 preventivamente."""
        assert UIScaler.calculate_scale_factor(0) == 1.0
        assert UIScaler.calculate_scale_factor(-500) == 1.0
        
    def test_generate_dynamic_qss(self) -> None:
        """Verifica que se genera una hoja de estilos QSS con el factor insertado y las proporciones correctas."""
        # Generar para portátil (factor 0.7)
        qss_laptop = UIScaler.generate_dynamic_qss(0.7)
        
        # Test values calculation base:
        # f_base = 14 * 0.7 = 9.8 -> 10
        # f_h1 = 24 * 0.7 = 16.8 -> 17
        # p_base = 10 * 0.7 = 7
        
        assert "font-size: 10px;" in qss_laptop
        assert "font-size: 17px;" in qss_laptop
        assert "padding: 7px" in qss_laptop
        assert "Factor de Escala: 0.7" in qss_laptop
        
        # Generar para normal (factor 1.0)
        qss_desktop = UIScaler.generate_dynamic_qss(1.0)
        assert "font-size: 14px;" in qss_desktop
        assert "font-size: 24px;" in qss_desktop
        assert "padding: 10px" in qss_desktop
        assert "Factor de Escala: 1.0" in qss_desktop

    def test_get_current_screen_height_widget_screen(self) -> None:
        """Verifica la obtención de la altura utilizando el widget.screen() propio de PyQt6."""
        mock_widget = MagicMock(spec=['screen'])
        mock_screen = MagicMock(spec=['availableGeometry'])
        mock_rect = MagicMock(spec=['height'])
        mock_rect.height.return_value = 900
        mock_screen.availableGeometry.return_value = mock_rect
        mock_widget.screen.return_value = mock_screen

        height = UIScaler.get_current_screen_height(mock_widget)
        assert height == 900
        assert mock_widget.screen.call_count == 1
        mock_widget.screen.assert_called_once_with()
        
    @patch('PyQt6.QtWidgets.QApplication')
    def test_get_current_screen_height_fallback_qapplication(self, mock_qapp: MagicMock) -> None:
        """Verifica el fallback a QApplication.primaryScreen() si widget.screen() falla (ej. None)."""
        mock_widget = MagicMock(spec=['screen'])
        mock_widget.screen.return_value = None

        mock_app_instance = MagicMock(spec=['primaryScreen'])
        mock_primary_screen = MagicMock(spec=['availableGeometry'])
        mock_rect = MagicMock(spec=['height'])
        mock_rect.height.return_value = 1050
        mock_primary_screen.availableGeometry.return_value = mock_rect
        mock_app_instance.primaryScreen.return_value = mock_primary_screen

        mock_qapp.instance.return_value = mock_app_instance

        height = UIScaler.get_current_screen_height(mock_widget)
        assert height == 1050
        assert mock_qapp.instance.call_count == 1
        mock_qapp.instance.assert_called_once_with()
        
    def test_get_current_screen_height_exception_fallback(self) -> None:
        """Verifica que si ocurre una excepción total, se devuelve la altura base (1080)."""
        mock_widget = MagicMock(spec=['screen'])
        mock_widget.screen.side_effect = Exception("Qt Mock Error")

        height = UIScaler.get_current_screen_height(mock_widget)
        assert height == 1080
