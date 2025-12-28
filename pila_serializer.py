# pila_serializer.py
"""
🛡️ Serializador robusto para pilas de cálculo.
Maneja correctamente todos los tipos de datos y previene pérdida de información.
"""
import json
import logging
from datetime import datetime, date, time
from decimal import Decimal

logger = logging.getLogger(__name__)


class PilaJSONEncoder(json.JSONEncoder):
    """Encoder personalizado para serializar pilas con todos sus tipos de datos."""

    def default(self, obj):
        # Fechas y tiempos
        if isinstance(obj, datetime):
            return {'__datetime__': True, 'value': obj.isoformat()}
        if isinstance(obj, date):
            return {'__date__': True, 'value': obj.isoformat()}
        if isinstance(obj, time):
            return {'__time__': True, 'value': obj.isoformat()}

        # Números decimales
        if isinstance(obj, Decimal):
            return {'__decimal__': True, 'value': str(obj)}

        # Sets (por si acaso)
        if isinstance(obj, set):
            return {'__set__': True, 'value': list(obj)}

        return super().default(obj)


def decode_pila_json(dct):
    """
    Decoder personalizado para restaurar objetos complejos desde JSON.
    Se usa con json.loads(data, object_hook=decode_pila_json)
    """
    if '__datetime__' in dct:
        return datetime.fromisoformat(dct['value'])
    if '__date__' in dct:
        return date.fromisoformat(dct['value'])
    if '__time__' in dct:
        return time.fromisoformat(dct['value'])
    if '__decimal__' in dct:
        return Decimal(dct['value'])
    if '__set__' in dct:
        return set(dct['value'])
    return dct

def serialize_production_flow(production_flow):
    """
    ✅ Serializa un flujo de producción con validación completa.
    Retorna una tupla (json_string, validation_summary)
    """
    if not production_flow:
        logger.warning("Flujo de producción vacío al serializar")
        return json.dumps([]), {'status': 'empty', 'steps': 0}

    # Validación pre-serialización
    validation_summary = {
        'status': 'ok',
        'steps': len(production_flow),
        'warnings': [],
        'critical_fields_saved': {
            'units_per_cycle': 0,
            'next_cyclic_task_index': 0,
            'positions': 0,
            'dependencies': 0
        }
    }

    for i, step in enumerate(production_flow):
        # Validar campos críticos
        if 'units_per_cycle' in step and step['units_per_cycle'] is not None:
            validation_summary['critical_fields_saved']['units_per_cycle'] += 1
        else:
            validation_summary['warnings'].append(
                f"Step {i}: Falta units_per_cycle"
            )

        if 'next_cyclic_task_index' in step and step['next_cyclic_task_index'] is not None:
            validation_summary['critical_fields_saved']['next_cyclic_task_index'] += 1

        if 'position' in step:
            validation_summary['critical_fields_saved']['positions'] += 1
        else:
            validation_summary['warnings'].append(
                f"Step {i}: Falta posición visual"
            )

        if 'previous_task_index' in step and step['previous_task_index'] is not None:
            validation_summary['critical_fields_saved']['dependencies'] += 1

    # Serializar con encoder robusto
    try:
        json_string = json.dumps(production_flow, cls=PilaJSONEncoder, indent=2)
        logger.info(f"✅ Flujo serializado: {len(json_string)} bytes, "
                    f"{validation_summary['steps']} pasos")
        return json_string, validation_summary
    except Exception as e:
        logger.error(f"❌ Error serializando flujo: {e}", exc_info=True)
        raise


# 📍 AÑADE ESTE BLOQUE DE CÓDIGO (al final del archivo)

def deserialize_production_flow(json_string):
    """
    ✅ Deserializa un flujo de producción con validación completa.
    Retorna una tupla (production_flow, validation_summary)
    """
    if not json_string or json_string.strip() == '[]':
        logger.warning("JSON de flujo vacío al deserializar")
        return [], {'status': 'empty', 'steps': 0}

    try:
        production_flow = json.loads(json_string, object_hook=decode_pila_json)
    except Exception as e:
        logger.error(f"❌ Error parseando JSON del flujo: {e}", exc_info=True)
        raise

    # Validación post-deserialización
    validation_summary = {
        'status': 'ok',
        'steps': len(production_flow),
        'warnings': [],
        'critical_fields_loaded': {
            'units_per_cycle': 0,
            'next_cyclic_task_index': 0,
            'positions': 0,
            'dependencies': 0
        }
    }

    for i, step in enumerate(production_flow):
        # Verificar que los campos críticos existen y tienen valores válidos
        if 'units_per_cycle' not in step or step['units_per_cycle'] is None:
            validation_summary['warnings'].append(
                f"Step {i}: units_per_cycle perdido, usando default=1"
            )
            step['units_per_cycle'] = 1
        else:
            validation_summary['critical_fields_loaded']['units_per_cycle'] += 1

        if 'next_cyclic_task_index' in step and step['next_cyclic_task_index'] is not None:
            validation_summary['critical_fields_loaded']['next_cyclic_task_index'] += 1

        if 'position' not in step:
            validation_summary['warnings'].append(
                f"Step {i}: Posición perdida, se regenerará"
            )
            step['position'] = {'x': 50, 'y': 50 + (i * 100)}  # Posición por defecto
        else:
            validation_summary['critical_fields_loaded']['positions'] += 1

        if 'previous_task_index' in step and step['previous_task_index'] is not None:
            validation_summary['critical_fields_loaded']['dependencies'] += 1

    logger.info(f"✅ Flujo deserializado: {validation_summary['steps']} pasos, "
                f"{len(validation_summary['warnings'])} advertencias")

    return production_flow, validation_summary