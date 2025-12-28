# database/models.py

from sqlalchemy import (Column, Integer, String, Float, ForeignKey, Table,
                        Boolean, Text, DateTime, Date)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

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
# ===============================================================================
# MODELOS CORE
# ===============================================================================

class Fabricacion(Base):
    __tablename__ = 'fabricaciones'

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(String)

    # Relación M-M con Preproceso
    preprocesos = relationship("Preproceso",
                               secondary=fabricacion_preproceso_link,
                               back_populates="fabricaciones")

    # Relaciones de trazabilidad
    trabajadores_asignados = relationship(
        "Trabajador",
        secondary=trabajador_fabricacion_link,
        back_populates="fabricaciones_asignadas"
    )
    trabajo_logs = relationship("TrabajoLog", back_populates="fabricacion", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fabricacion(id={self.id}, codigo='{self.codigo}')>"

class Preproceso(Base):
    __tablename__ = 'preprocesos'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    tiempo = Column(Float, nullable=False, default=0.0)
    tipo_trabajador = Column(Integer, nullable=False, default=1)
    materiales = relationship("Material",
                              secondary=preproceso_material_link,
                              back_populates="preprocesos")

    fabricaciones = relationship("Fabricacion",
                                 secondary=fabricacion_preproceso_link,
                                 back_populates="preprocesos")

    # ✅ PROPIEDAD PARA COMPATIBILIDAD HACIA ATRÁS
    @property
    def componentes(self):
        return self.materiales

    @componentes.setter
    def componentes(self, value):
        """Setter para mantener compatibilidad."""
        self.materiales = value

    def __repr__(self):
        return f"<Preproceso(id={self.id}, nombre='{self.nombre}')>"

class Producto(Base):
    __tablename__ = 'productos'

    codigo = Column(String, primary_key=True)
    descripcion = Column(String, nullable=False)
    departamento = Column(String, nullable=False)
    tipo_trabajador = Column(Integer, nullable=False)
    donde = Column(String)
    tiene_subfabricaciones = Column(Boolean, nullable=False)
    tiempo_optimo = Column(Float)

    # Relaciones
    subfabricaciones = relationship("Subfabricacion", back_populates="producto", cascade="all, delete-orphan")
    materiales = relationship("Material", secondary=producto_material_link, back_populates="productos")
    procesos_mecanicos = relationship("ProcesoMecanico", back_populates="producto", cascade="all, delete-orphan")
    iteraciones = relationship("ProductIteration", back_populates="producto", cascade="all, delete-orphan")

    # Relación de trazabilidad
    trabajo_logs = relationship("TrabajoLog", back_populates="producto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Producto(codigo='{self.codigo}', descripcion='{self.descripcion}')>"

class Trabajador(Base):
    __tablename__ = 'trabajadores'

    id = Column(Integer, primary_key=True)
    nombre_completo = Column(String, nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True)
    notas = Column(Text)
    username = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String)
    tipo_trabajador = Column(Integer, nullable=False, default=1)
    # Relaciones
    anotaciones = relationship("TrabajadorPilaAnotacion", back_populates="trabajador", cascade="all, delete-orphan")

    # Relaciones de trazabilidad
    fabricaciones_asignadas = relationship(
        "Fabricacion",
        secondary=trabajador_fabricacion_link,
        back_populates="trabajadores_asignados"
    )
    trabajo_logs = relationship("TrabajoLog", back_populates="trabajador")
    incidencias = relationship("IncidenciaLog", back_populates="trabajador")

    def __repr__(self):
        return f"<Trabajador(id={self.id}, nombre='{self.nombre_completo}')>"

class Maquina(Base):
    __tablename__ = 'maquinas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)
    departamento = Column(String, nullable=False)
    tipo_proceso = Column(String)
    activa = Column(Boolean, nullable=False, default=True)

    # Relaciones
    mantenimientos = relationship("MachineMaintenanc", back_populates="maquina", cascade="all, delete-orphan")
    grupos_preparacion = relationship("GrupoPreparacion", back_populates="maquina", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Maquina(id={self.id}, nombre='{self.nombre}')>"

class Pila(Base):
    __tablename__ = 'pilas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)
    descripcion = Column(Text)
    fecha_creacion = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    resultados_simulacion = Column(Text)  # JSON string
    producto_origen_codigo = Column(String, ForeignKey('productos.codigo'))
    pila_de_calculo_json = Column(Text) # <-- AÑADE ESTA LÍNEA

    # Relaciones
    pasos = relationship("PasoPila", back_populates="pila", cascade="all, delete-orphan")
    producto_origen = relationship("Producto")
    bitacora = relationship("DiarioBitacora", back_populates="pila", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pila(id={self.id}, nombre='{self.nombre}')>"

# ===============================================================================
# MODELOS AUXILIARES
# ===============================================================================

class Subfabricacion(Base):
    __tablename__ = 'subfabricaciones'

    id = Column(Integer, primary_key=True)
    producto_codigo = Column(String, ForeignKey('productos.codigo'), nullable=False)
    descripcion = Column(String, nullable=False)
    tiempo = Column(Float, nullable=False)
    tipo_trabajador = Column(Integer, nullable=False)
    maquina_id = Column(Integer, ForeignKey('maquinas.id'), nullable=True)
    maquina = relationship("Maquina")

    # Relación inversa
    producto = relationship("Producto", back_populates="subfabricaciones")

    def __repr__(self):
        return f"<Subfabricacion(id={self.id}, producto='{self.producto_codigo}')>"

class ProcesoMecanico(Base):
    __tablename__ = 'procesos_mecanicos'

    id = Column(Integer, primary_key=True)
    producto_codigo = Column(String, ForeignKey('productos.codigo'), nullable=False)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    tiempo = Column(Float, nullable=False)
    tipo_trabajador = Column(Integer, nullable=False)

    # Relación inversa
    producto = relationship("Producto", back_populates="procesos_mecanicos")

    def __repr__(self):
        return f"<ProcesoMecanico(id={self.id}, nombre='{self.nombre}')>"

class ProductIteration(Base):
    __tablename__ = 'iteraciones_producto'

    id = Column(Integer, primary_key=True)
    producto_codigo = Column(String, ForeignKey('productos.codigo', ondelete='CASCADE'), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    nombre_responsable = Column(String, nullable=False)
    descripcion_cambio = Column(Text)
    ruta_imagen = Column(String)
    tipo_fallo = Column(String)
    ruta_plano = Column(String)

    # Relaciones
    producto = relationship("Producto", back_populates="iteraciones")
    materiales = relationship("Material", secondary=iteracion_material_link, backref="iteraciones")

    def __repr__(self):
        return f"<ProductIteration(id={self.id}, producto='{self.producto_codigo}')>"

class Material(Base):
    __tablename__ = 'materiales'

    id = Column(Integer, primary_key=True)
    codigo_componente = Column(String, unique=True, nullable=False)
    descripcion_componente = Column(String)

    # Relación inversa con Producto (esta ya estaba bien)
    productos = relationship("Producto", secondary=producto_material_link, back_populates="materiales")

    preprocesos = relationship("Preproceso",
                               secondary=preproceso_material_link,
                               back_populates="materiales")

    def __repr__(self):
        return f"<Material(codigo='{self.codigo_componente}')>"

class PasoPila(Base):
    __tablename__ = 'pasos_pila'

    id = Column(Integer, primary_key=True)
    pila_id = Column(Integer, ForeignKey('pilas.id'), nullable=False)
    orden = Column(Integer, nullable=False)
    datos_paso = Column(Text, nullable=False)  # JSON string

    # Relación inversa
    pila = relationship("Pila", back_populates="pasos")

    def __repr__(self):
        return f"<PasoPila(id={self.id}, pila_id={self.pila_id}, orden={self.orden})>"

class MachineMaintenanc(Base):
    __tablename__ = 'machine_maintenance'

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey('maquinas.id'), nullable=False)
    maintenance_date = Column(String, nullable=False)  # Almacenado como string en formato YYYY-MM-DD
    notes = Column(Text)

    # Relación inversa
    maquina = relationship("Maquina", back_populates="mantenimientos")

    def __repr__(self):
        return f"<MachineMaintenanc(id={self.id}, machine_id={self.machine_id})>"

class TrabajadorPilaAnotacion(Base):
    __tablename__ = 'trabajador_pila_anotaciones'

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey('trabajadores.id'), nullable=False)
    pila_id = Column(Integer, ForeignKey('pilas.id'), nullable=False)
    fecha = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    anotacion = Column(Text, nullable=False)

    # Relaciones inversas
    trabajador = relationship("Trabajador", back_populates="anotaciones")
    pila = relationship("Pila")

    def __repr__(self):
        return f"<TrabajadorPilaAnotacion(id={self.id}, worker_id={self.worker_id})>"

class Configuration(Base):
    __tablename__ = 'configuracion'

    clave = Column(String, primary_key=True)
    valor = Column(String, nullable=False)

    def __repr__(self):
        return f"<Configuration(clave='{self.clave}', valor='{self.valor[:50]}...')>"

class GrupoPreparacion(Base):
    __tablename__ = 'grupos_preparacion'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    maquina_id = Column(Integer, ForeignKey('maquinas.id'), nullable=False)
    descripcion = Column(Text)
    producto_codigo = Column(String, ForeignKey('productos.codigo'))

    # Relaciones
    maquina = relationship("Maquina", back_populates="grupos_preparacion")
    producto = relationship("Producto")
    pasos = relationship("PreparacionPaso", back_populates="grupo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GrupoPreparacion(id={self.id}, nombre='{self.nombre}')>"

class PreparacionPaso(Base):
    __tablename__ = 'preparacion_pasos'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    tiempo_fase = Column(Float, nullable=False)
    grupo_id = Column(Integer, ForeignKey('grupos_preparacion.id'))
    es_diario = Column(Boolean, default=False)
    es_verificacion = Column(Boolean, default=False)

    # Relación inversa
    grupo = relationship("GrupoPreparacion", back_populates="pasos")

    def __repr__(self):
        return f"<PreparacionPaso(id={self.id}, nombre='{self.nombre}')>"

class DiarioBitacora(Base):
    __tablename__ = 'diario_bitacora'

    id = Column(Integer, primary_key=True)
    pila_id = Column(Integer, ForeignKey('pilas.id'), nullable=False, unique=True)

    # Relaciones
    pila = relationship("Pila", back_populates="bitacora")
    entradas = relationship("EntradaDiario", back_populates="bitacora", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DiarioBitacora(id={self.id}, pila_id={self.pila_id})>"

class EntradaDiario(Base):
    __tablename__ = 'entrada_diario'

    id = Column(Integer, primary_key=True)
    bitacora_id = Column(Integer, ForeignKey('diario_bitacora.id'), nullable=False)
    fecha = Column(Date, nullable=False)
    dia_numero = Column(Integer, nullable=False)
    plan_previsto = Column(Text)
    trabajo_realizado = Column(Text)
    notas = Column(Text)

    # Relación inversa
    bitacora = relationship("DiarioBitacora", back_populates="entradas")

    def __repr__(self):
        return f"<EntradaDiario(id={self.id}, fecha={self.fecha})>"

# ===============================================================================
# MODELOS PARA PLANTILLAS DE LOTE (VERSIÓN CORREGIDA)
# ===============================================================================

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

class Lote(Base):
    __tablename__ = 'lotes'

    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True, nullable=False)
    descripcion = Column(Text)
    fecha_creacion = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones M-M usando las tablas de enlace separadas
    productos = relationship("Producto", secondary=lote_producto_link)
    fabricaciones = relationship("Fabricacion", secondary=lote_fabricacion_link)

    def __repr__(self):
        return f"<Lote(id={self.id}, codigo='{self.codigo}')>"

# ===============================================================================
# MODELOS DE TRAZABILIDAD Y SEGUIMIENTO
# ===============================================================================

class TrabajoLog(Base):
    """
    Registro de tiempo de trabajo de una unidad individual.

    Cada registro representa una unidad producida con su tiempo de inicio y fin.
    El código QR identifica de forma única cada unidad.
    """
    __tablename__ = 'trabajo_logs'

    id = Column(Integer, primary_key=True)
    qr_code = Column(String, unique=True, nullable=False, index=True)

    orden_fabricacion = Column(String, nullable=True, index=True)

    # Relaciones con otras tablas
    trabajador_id = Column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'))
    fabricacion_id = Column(Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), nullable=False)
    producto_codigo = Column(String, ForeignKey('productos.codigo', ondelete='CASCADE'), nullable=False)

    # Tiempos de producción
    tiempo_inicio = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    tiempo_fin = Column(DateTime)
    duracion_segundos = Column(Integer)  # Calculado automáticamente

    # Estado del trabajo
    estado = Column(String, nullable=False, default='en_proceso')  # en_proceso, completado, pausado, cancelado

    # Información adicional
    notas = Column(Text)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones inversas
    trabajador = relationship("Trabajador", back_populates="trabajo_logs")
    fabricacion = relationship("Fabricacion", back_populates="trabajo_logs")
    producto = relationship("Producto", back_populates="trabajo_logs")
    incidencias = relationship("IncidenciaLog", back_populates="trabajo_log", cascade="all, delete-orphan")

    pasos_trazabilidad = relationship("PasoTrazabilidad", back_populates="trabajo_log", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TrabajoLog(id={self.id}, qr='{self.qr_code}', estado='{self.estado}')>"


class PasoTrazabilidad(Base):
    """
    Registro de un paso de trabajo individual para una unidad (TrabajoLog).
    Permite que múltiples trabajadores registren diferentes etapas
    para el mismo código QR.
    """
    __tablename__ = 'pasos_trazabilidad'

    id = Column(Integer, primary_key=True)

    # --- Vínculos ---
    # El "pasaporte" al que pertenece este "sello"
    trabajo_log_id = Column(Integer, ForeignKey('trabajo_logs.id', ondelete='CASCADE'), nullable=False, index=True)
    # El trabajador que realizó este paso
    trabajador_id = Column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'), nullable=True)
    # La máquina utilizada (si aplica)
    maquina_id = Column(Integer, ForeignKey('maquinas.id', ondelete='SET NULL'), nullable=True)

    # --- Detalles del Paso ---
    # Nombre legible del paso (ej: "Corte", "Ensamblaje", "Proceso Mecánico: Torneado")
    paso_nombre = Column(String, nullable=False)
    # Tipo de paso para búsquedas (ej: "subfabricacion", "proceso_mecanico")
    tipo_paso = Column(String)

    # --- Tiempos del Paso ---
    tiempo_inicio_paso = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    tiempo_fin_paso = Column(DateTime)
    duracion_paso_segundos = Column(Integer)

    # Estado de este paso específico
    estado_paso = Column(String, nullable=False, default='en_proceso')  # en_proceso, completado, pausado

    # --- Relaciones Inversas ---
    trabajo_log = relationship("TrabajoLog", back_populates="pasos_trazabilidad")
    trabajador = relationship("Trabajador")
    maquina = relationship("Maquina")

    def __repr__(self):
        return f"<PasoTrazabilidad(id={self.id}, trabajo_log_id={self.trabajo_log_id}, paso='{self.paso_nombre}')>"

class IncidenciaLog(Base):
    """
    Registro de incidencias durante la producción.

    Cada incidencia está asociada a un trabajo específico y puede tener
    múltiples fotografías adjuntas.
    """
    __tablename__ = 'incidencia_logs'

    id = Column(Integer, primary_key=True)

    # Relación con el trabajo
    trabajo_log_id = Column(Integer, ForeignKey('trabajo_logs.id', ondelete='CASCADE'), nullable=False)

    # Relación con trabajador que reporta
    trabajador_id = Column(Integer, ForeignKey('trabajadores.id', ondelete='SET NULL'))

    # Información de la incidencia
    tipo_incidencia = Column(String, nullable=False)  # defecto, pausa, problema_material, problema_maquina, otro
    descripcion = Column(Text, nullable=False)
    fecha_reporte = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Estado y resolución
    estado = Column(String, nullable=False, default='abierta')  # abierta, en_revision, resuelta, cerrada
    resolucion = Column(Text)
    fecha_resolucion = Column(DateTime)

    # Relaciones inversas
    trabajo_log = relationship("TrabajoLog", back_populates="incidencias")
    trabajador = relationship("Trabajador", back_populates="incidencias")
    adjuntos = relationship("IncidenciaAdjunto", back_populates="incidencia", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IncidenciaLog(id={self.id}, tipo='{self.tipo_incidencia}', estado='{self.estado}')>"

class IncidenciaAdjunto(Base):
    """
    Adjuntos fotográficos de incidencias.

    Almacena las rutas de las fotografías tomadas para documentar
    cada incidencia reportada.
    """
    __tablename__ = 'incidencia_adjuntos'

    id = Column(Integer, primary_key=True)
    incidencia_id = Column(Integer, ForeignKey('incidencia_logs.id', ondelete='CASCADE'), nullable=False)

    # Información del archivo
    ruta_archivo = Column(String, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    tipo_mime = Column(String)  # image/jpeg, image/png, etc.
    tamano_bytes = Column(Integer)

    # Metadatos
    fecha_subida = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    descripcion = Column(Text)

    # Relación inversa
    incidencia = relationship("IncidenciaLog", back_populates="adjuntos")

    def __repr__(self):
        return f"<IncidenciaAdjunto(id={self.id}, archivo='{self.nombre_archivo}')>"


class FabricacionContador(Base):
    """
    Contador para numeración de etiquetas de fabricación.
    Reemplaza la antigua base de datos 'etiquetas.db'.
    """
    __tablename__ = 'fabricacion_contadores'

    fabricacion_id = Column(Integer, ForeignKey('fabricaciones.id', ondelete='CASCADE'), primary_key=True)
    ultimo_numero_unidad = Column(Integer, nullable=False, default=0)

    # Relación para integridad referencial
    fabricacion = relationship("Fabricacion")

    def __repr__(self):
        return f"<FabricacionContador(fabricacion_id={self.fabricacion_id}, ultimo={self.ultimo_numero_unidad})>"
