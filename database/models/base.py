"""
Modelos ORM base (SQLAlchemy): DeclarativeBase, metadatos compartidos y tablas de
enlace many-to-many entre productos, materiales y preprocesos.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

# ===============================================================================
# TABLAS DE ENLACE (Many-to-Many relationships)
# ===============================================================================

# Tabla de enlace para la relación muchos-a-muchos entre Producto y Material
producto_material_link = Table('producto_material_link', Base.metadata,
                               Column('producto_codigo', String, ForeignKey('productos.codigo')),
                               Column('material_id', Integer, ForeignKey('materiales.id'))
                               )

# Tabla de enlace para la relación muchos-a-muchos entre Preproceso y Material
preproceso_material_link = Table('preproceso_material_link', Base.metadata,
                                 Column('preproceso_id', Integer, ForeignKey('preprocesos.id')),
                                 Column('material_id', Integer, ForeignKey('materiales.id'))
                                 )

# Tabla de enlace para la relación muchos-a-muchos entre Fabricacion y Preproceso
fabricacion_preproceso_link = Table('fabricacion_preproceso_link', Base.metadata,
                                    Column('fabricacion_id', Integer, ForeignKey('fabricaciones.id')),
                                    Column('preproceso_id', Integer, ForeignKey('preprocesos.id'))
                                    )

# Tabla de enlace para Iteración <-> Material
iteracion_material_link = Table('iteracion_material_link', Base.metadata,
    Column('iteracion_id', Integer, ForeignKey('iteraciones_producto.id', ondelete='CASCADE'), primary_key=True),
    Column('material_id', Integer, ForeignKey('materiales.id', ondelete='CASCADE'), primary_key=True)
)

trabajador_fabricacion_link = Table(
    'trabajador_fabricacion_link',
    Base.metadata,
    Column('trabajador_id', Integer, ForeignKey('trabajadores.id', ondelete='CASCADE'), primary_key=True),
    Column('fabricacion_id', Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), primary_key=True),
    Column('fecha_asignacion', DateTime, default=lambda: datetime.now(timezone.utc)),
    Column('estado', String, default='activo')  # activo, completado, cancelado
)

# Tabla de enlace para la relación muchos-a-muchos entre Fabricacion y Producto
fabricacion_productos = Table(
    'fabricacion_productos',
    Base.metadata,
    Column('fabricacion_id', Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), primary_key=True),
    Column('producto_codigo', String, ForeignKey('productos.codigo', ondelete='CASCADE'), primary_key=True),
    Column('cantidad', Integer, nullable=False, default=1)
)

# Tabla de enlace para la relación Lote <-> Producto
lote_producto_link = Table('lote_producto_link', Base.metadata,
    Column('lote_id', Integer, ForeignKey('lotes.id'), primary_key=True),
    Column('producto_codigo', String, ForeignKey('productos.codigo'), primary_key=True)
)

# Tabla de enlace para la relación Lote <-> Fabricacion
lote_fabricacion_link = Table('lote_fabricacion_link', Base.metadata,
    Column('lote_id', Integer, ForeignKey('lotes.id'), primary_key=True),
    Column('fabricacion_id', Integer, ForeignKey('fabricaciones.id'), primary_key=True)
)
