# Análisis de `models.py`

**Ruta completa:** `/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/models.py`


## Importaciones
- `datetime.datetime`
- `datetime.timezone`
- `sqlalchemy.Boolean`
- `sqlalchemy.Column`
- `sqlalchemy.Date`
- `sqlalchemy.DateTime`
- `sqlalchemy.Float`
- `sqlalchemy.ForeignKey`
- `sqlalchemy.Integer`
- `sqlalchemy.String`
- `sqlalchemy.Table`
- `sqlalchemy.Text`
- `sqlalchemy.orm.declarative_base`
- `sqlalchemy.orm.relationship`

## Variables de Módulo
- `Base` (línea 8)
- `producto_material_link` (línea 15)
- `preproceso_material_link` (línea 20)
- `fabricacion_preproceso_link` (línea 25)
- `iteracion_material_link` (línea 30)
- `trabajador_fabricacion_link` (línea 34)
- `fabricacion_productos` (línea 43)
- `lote_producto_link` (línea 385)
- `lote_fabricacion_link` (línea 391)

## Clases

### Clase `Fabricacion`
- **Línea:** 54
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `codigo`
- `descripcion`
- `preprocesos`
- `trabajadores_asignados`
- `trabajo_logs`

#### Métodos
- `__repr__`(self)

### Clase `Preproceso`
- **Línea:** 77
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre`
- `descripcion`
- `tiempo`
- `tipo_trabajador`
- `materiales`
- `fabricaciones`

#### Métodos
- `componentes`(self)
- `componentes`(self, value)
  - _Setter para mantener compatibilidad._
- `__repr__`(self)

### Clase `Producto`
- **Línea:** 106
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `codigo`
- `descripcion`
- `departamento`
- `tipo_trabajador`
- `donde`
- `tiene_subfabricaciones`
- `tiempo_optimo`
- `subfabricaciones`
- `materiales`
- `procesos_mecanicos`
- `iteraciones`
- `trabajo_logs`

#### Métodos
- `__repr__`(self)

### Clase `Trabajador`
- **Línea:** 129
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre_completo`
- `activo`
- `notas`
- `username`
- `password_hash`
- `role`
- `tipo_trabajador`
- `anotaciones`
- `fabricaciones_asignadas`
- `trabajo_logs`
- `incidencias`

#### Métodos
- `__repr__`(self)

### Clase `Maquina`
- **Línea:** 155
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre`
- `departamento`
- `tipo_proceso`
- `activa`
- `mantenimientos`
- `grupos_preparacion`

#### Métodos
- `__repr__`(self)

### Clase `Pila`
- **Línea:** 171
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre`
- `descripcion`
- `fecha_creacion`
- `resultados_simulacion`
- `producto_origen_codigo`
- `pila_de_calculo_json`
- `pasos`
- `producto_origen`
- `bitacora`

#### Métodos
- `__repr__`(self)

### Clase `Subfabricacion`
- **Línea:** 194
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `producto_codigo`
- `descripcion`
- `tiempo`
- `tipo_trabajador`
- `maquina_id`
- `maquina`
- `producto`

#### Métodos
- `__repr__`(self)

### Clase `ProcesoMecanico`
- **Línea:** 211
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `producto_codigo`
- `nombre`
- `descripcion`
- `tiempo`
- `tipo_trabajador`
- `producto`

#### Métodos
- `__repr__`(self)

### Clase `ProductIteration`
- **Línea:** 227
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `producto_codigo`
- `fecha_creacion`
- `nombre_responsable`
- `descripcion_cambio`
- `ruta_imagen`
- `tipo_fallo`
- `ruta_plano`
- `producto`
- `materiales`

#### Métodos
- `__repr__`(self)

### Clase `Material`
- **Línea:** 246
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `codigo_componente`
- `descripcion_componente`
- `productos`
- `preprocesos`

#### Métodos
- `__repr__`(self)

### Clase `PasoPila`
- **Línea:** 263
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `pila_id`
- `orden`
- `datos_paso`
- `pila`

#### Métodos
- `__repr__`(self)

### Clase `MachineMaintenanc`
- **Línea:** 277
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `machine_id`
- `maintenance_date`
- `notes`
- `maquina`

#### Métodos
- `__repr__`(self)

### Clase `TrabajadorPilaAnotacion`
- **Línea:** 291
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `worker_id`
- `pila_id`
- `fecha`
- `anotacion`
- `trabajador`
- `pila`

#### Métodos
- `__repr__`(self)

### Clase `Configuration`
- **Línea:** 307
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `clave`
- `valor`

#### Métodos
- `__repr__`(self)

### Clase `GrupoPreparacion`
- **Línea:** 316
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre`
- `maquina_id`
- `descripcion`
- `producto_codigo`
- `maquina`
- `producto`
- `pasos`

#### Métodos
- `__repr__`(self)

### Clase `PreparacionPaso`
- **Línea:** 333
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `nombre`
- `descripcion`
- `tiempo_fase`
- `grupo_id`
- `es_diario`
- `es_verificacion`
- `grupo`

#### Métodos
- `__repr__`(self)

### Clase `DiarioBitacora`
- **Línea:** 350
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `pila_id`
- `pila`
- `entradas`

#### Métodos
- `__repr__`(self)

### Clase `EntradaDiario`
- **Línea:** 363
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `bitacora_id`
- `fecha`
- `dia_numero`
- `plan_previsto`
- `trabajo_realizado`
- `notas`
- `bitacora`

#### Métodos
- `__repr__`(self)

### Clase `Lote`
- **Línea:** 396
- **Hereda de:** `Base`

#### Variables de Clase
- `__tablename__`
- `id`
- `codigo`
- `descripcion`
- `fecha_creacion`
- `productos`
- `fabricaciones`

#### Métodos
- `__repr__`(self)

### Clase `TrabajoLog`
- **Línea:** 415
- **Hereda de:** `Base`
- **Docstring:** Registro de tiempo de trabajo de una unidad individual.

Cada registro representa una unidad producida con su tiempo de inicio y fin.
El código QR identifica de forma única cada unidad....

#### Variables de Clase
- `__tablename__`
- `id`
- `qr_code`
- `orden_fabricacion`
- `trabajador_id`
- `fabricacion_id`
- `producto_codigo`
- `tiempo_inicio`
- `tiempo_fin`
- `duracion_segundos`
- `estado`
- `notas`
- `created_at`
- `updated_at`
- `trabajador`
- `fabricacion`
- `producto`
- `incidencias`
- `pasos_trazabilidad`

#### Métodos
- `__repr__`(self)

### Clase `PasoTrazabilidad`
- **Línea:** 459
- **Hereda de:** `Base`
- **Docstring:** Registro de un paso de trabajo individual para una unidad (TrabajoLog).
Permite que múltiples trabajadores registren diferentes etapas
para el mismo código QR....

#### Variables de Clase
- `__tablename__`
- `id`
- `trabajo_log_id`
- `trabajador_id`
- `maquina_id`
- `paso_nombre`
- `tipo_paso`
- `tiempo_inicio_paso`
- `tiempo_fin_paso`
- `duracion_paso_segundos`
- `estado_paso`
- `trabajo_log`
- `trabajador`
- `maquina`

#### Métodos
- `__repr__`(self)

### Clase `IncidenciaLog`
- **Línea:** 499
- **Hereda de:** `Base`
- **Docstring:** Registro de incidencias durante la producción.

Cada incidencia está asociada a un trabajo específico y puede tener
múltiples fotografías adjuntas....

#### Variables de Clase
- `__tablename__`
- `id`
- `trabajo_log_id`
- `trabajador_id`
- `tipo_incidencia`
- `descripcion`
- `fecha_reporte`
- `estado`
- `resolucion`
- `fecha_resolucion`
- `trabajo_log`
- `trabajador`
- `adjuntos`

#### Métodos
- `__repr__`(self)

### Clase `IncidenciaAdjunto`
- **Línea:** 534
- **Hereda de:** `Base`
- **Docstring:** Adjuntos fotográficos de incidencias.

Almacena las rutas de las fotografías tomadas para documentar
cada incidencia reportada....

#### Variables de Clase
- `__tablename__`
- `id`
- `incidencia_id`
- `ruta_archivo`
- `nombre_archivo`
- `tipo_mime`
- `tamano_bytes`
- `fecha_subida`
- `descripcion`
- `incidencia`

#### Métodos
- `__repr__`(self)

### Clase `FabricacionContador`
- **Línea:** 563
- **Hereda de:** `Base`
- **Docstring:** Contador para numeración de etiquetas de fabricación.
Reemplaza la antigua base de datos 'etiquetas.db'....

#### Variables de Clase
- `__tablename__`
- `fabricacion_id`
- `ultimo_numero_unidad`
- `fabricacion`

#### Métodos
- `__repr__`(self)