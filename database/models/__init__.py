# database/models/__init__.py

"""
Nombre del Módulo: database.models

Descripción: Concentra datos de configuración o catálogos estáticos: ``__all__``, consumidos por la UI y controladores. Integración típica con: ``base``, ``product``, ``fabrication``, ``worker``, ``tracking``, ``machine``.
"""

from .base import (
    Base,
    producto_material_link,
    preproceso_material_link,
    fabricacion_preproceso_link,
    iteracion_material_link,
    trabajador_fabricacion_link,
    fabricacion_productos,
    lote_producto_link,
    lote_fabricacion_link
)

from .product import (
    Producto,
    Preproceso,
    Subfabricacion,
    ProcesoMecanico,
    ProductIteration
)

from .fabrication import (
    Fabricacion,
    FabricacionContador
)

from .worker import (
    Trabajador,
    TrabajadorPilaAnotacion
)

from .tracking import (
    TrabajoLog,
    PasoTrazabilidad,
    IncidenciaLog,
    IncidenciaAdjunto
)

from .machine import (
    Maquina,
    MachineMaintenanc,
    GrupoPreparacion,
    PreparacionPaso
)

from .inventory import (
    Material,
    Pila,
    PasoPila,
    DiarioBitacora,
    EntradaDiario,
    Lote
)

from .security import (
    Configuration,
    LoginAttempt,
    AuditLog
)

# Export all symbols to maintain backward compatibility with 'from database.models import ...'
__all__ = [
    'Base',
    'producto_material_link',
    'preproceso_material_link',
    'fabricacion_preproceso_link',
    'iteracion_material_link',
    'trabajador_fabricacion_link',
    'fabricacion_productos',
    'lote_producto_link',
    'lote_fabricacion_link',
    'Producto',
    'Preproceso',
    'Subfabricacion',
    'ProcesoMecanico',
    'ProductIteration',
    'Fabricacion',
    'FabricacionContador',
    'Trabajador',
    'TrabajadorPilaAnotacion',
    'TrabajoLog',
    'PasoTrazabilidad',
    'IncidenciaLog',
    'IncidenciaAdjunto',
    'Maquina',
    'MachineMaintenanc',
    'GrupoPreparacion',
    'PreparacionPaso',
    'Material',
    'Pila',
    'PasoPila',
    'DiarioBitacora',
    'EntradaDiario',
    'Lote',
    'Configuration',
    'LoginAttempt',
    'AuditLog'
]
