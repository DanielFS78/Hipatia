# utils.py
import logging
import constants
from datetime import datetime
from PyQt6.QtCore import QDate
from PyQt6.QtCharts import QChart, QChartView
from PyQt6.QtWidgets import QWidget
try:
    from constants import VALIDATION
except ImportError:
    # Valores por defecto si no se encuentra constants.py
    VALIDATION = {
        'MIN_SEARCH_LENGTH': 2,
        'MAX_PRODUCT_CODE_LENGTH': 50,
        'MAX_DESCRIPTION_LENGTH': 200
    }

def format_datetime_for_display(dt):
    """Formatea un datetime para mostrar al usuario."""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return dt
    return dt.strftime('%d/%m/%Y %H:%M') if dt else 'N/A'


def format_date_for_display(date_obj):
    """Formatea una fecha para mostrar al usuario."""
    if isinstance(date_obj, QDate):
        date_obj = date_obj.toPyDate()
    return date_obj.strftime('%d/%m/%Y') if date_obj else 'N/A'


def validate_positive_number(value, field_name="campo"):
    """Valida que un valor sea un número positivo."""
    try:
        num = float(str(value).replace(",", "."))
        if num <= 0:
            raise ValueError(f"El {field_name} debe ser positivo.")
        return num
    except (ValueError, TypeError):
        raise ValueError(f"El {field_name} debe ser un número válido.")


def create_chart_view():
    """Crea un QChartView estándar para los gráficos."""
    chart_view = QChartView()
    chart_view.setRenderHint(chart_view.painter().Antialiasing)
    chart_view.setMinimumHeight(300)
    return chart_view


def setup_module_logger(module_name):
    """Configura un logger específico para un módulo."""
    return logging.getLogger(f"EvolucionTiemposApp.{module_name}")


def validate_product_code(code):
    """Valida que un código de producto tenga el formato correcto."""
    if not code or not code.strip():
        raise ValueError("El código del producto no puede estar vacío.")

    code = code.strip()
    if len(code) > VALIDATION['MAX_PRODUCT_CODE_LENGTH']:
        raise ValueError(
            f"El código no puede tener más de {constants.VALIDATION['MAX_PRODUCT_CODE_LENGTH']} caracteres.")

    # Validar caracteres permitidos (letras, números, guiones, puntos)
    import re
    if not re.match(r'^[A-Za-z0-9._-]+$', code):
        raise ValueError("El código solo puede contener letras, números, puntos, guiones y guiones bajos.")

    return code


def validate_description(description, field_name="descripción"):
    """Valida que una descripción tenga el formato correcto."""
    if not description or not description.strip():
        raise ValueError(f"La {field_name} no puede estar vacía.")

    description = description.strip()
    if len(description) > VALIDATION['MAX_DESCRIPTION_LENGTH']:
        raise ValueError(
            f"La {field_name} no puede tener más de {constants.VALIDATION['MAX_DESCRIPTION_LENGTH']} caracteres.")

    return description