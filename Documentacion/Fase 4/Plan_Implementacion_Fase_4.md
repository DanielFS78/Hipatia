# Plan de Implementación - Fase 4: Trazabilidad Avanzada y Flujo de Producción Inteligente

## 1. Introducción y Objetivos
El objetivo principal de esta fase es dotar al sistema de "inteligencia" en el seguimiento de la producción, permitiendo un flujo de trabajo contextualizado y multicapa. El sistema entenderá el contexto de fabricación (Pedido, Unidades) y aplicará capas de información basadas en el **Rol/Tarea del Trabajador** activo.

## 2. Análisis del Estado Actual
- **`TrackingRepository`**: Soporta `iniciar_nuevo_paso` para añadir "capas" a un QR existente.
- **`AppController`**: Necesita gestionar el **Contexto de Sesión**.
- **`Trabajador`**: Tiene un campo `role` (String). Deberemos usar esto o una nueva asignación de "Tarea Actual" para definir la capa.

## 3. Arquitectura Propuesta

### A. Gestión del "Contexto de Producción"
**`ProductionContext`** almacenará:
- `current_order_number`: Nº Pedido actual.
- `target_units`: Cantidad total.
- `units_completed`: Contador local.
- **`current_process_name`**:  Determinado automáticamente por el rol/tarea del trabajador logueado (ej. "Inserción", "Soldadura", "Control Calidad").

### B. Flujo de Escaneo Inteligente
Máquina de estados en `AppController`:
1.  **Estado IDLE**: Esperando escaneo.
2.  **Estado SETUP**: Al detectar el primer QR de una serie, si no hay contexto activo, solicita datos (Nº Pedido, Cantidad).
3.  **Estado PRODUCTION**:
    - Escaneos subsiguientes añaden el paso correspondiente a la "Capa" del trabajador actual.
    - Feedback UI: "Unidad X de Y - [Nombre Proceso] Completado".
4.  **Estado WARNING**: Alertas por duplicados o exceso de cantidad.

### C. Multiproceso (Definición Dinámica de Capas)
En lugar de un selector manual, la "capa" se define por el trabajador:
- Al hacer Login (o seleccionar usuario): Se carga el `role` del trabajador (o se pide seleccionar la tarea actual si tiene múltiples roles).
- Al escanear QR:
    - El sistema busca si ya existe el `TrabajoLog` para ese QR.
    - **Si NO existe**: Crea `TrabajoLog` + `PasoTrazabilidad` (Tipo = Rol Trabajador).
    - **Si YA existe**: Añade `PasoTrazabilidad` (Tipo = Rol Trabajador).
- Esto permite que el QR pase de "Montaje" -> "Soldadura" -> "Calidad" simplemente cambiando de manos.

## 4. Plan de Trabajo Estructurado

### Fase 4.1: Infraestructura del Contexto y Roles
**Objetivo**: Que el sistema sepa "quién hace qué" y "dónde estamos".

1.  **Gestor de Contexto (`ProductionContext`)**:
    - Clase para manejar estado de pedido y contadores.
    - Integración en `AppController`.
2.  **Definición de Tareas/Roles**:
    - Verificar si `Trabajador.role` es suficiente o crear un método para mapear "Rol" -> "Nombre de Paso Trazable".
    - UI para confirmar "Tarea Actual" al iniciar sesión si el rol es ambiguo.
3.  **UI de Configuración de Pedido**:
    - Diálogo `OrderSetupDialog` al primer escaneo.

### Fase 4.2: Lógica de Registro Inteligente (1 de X)
**Objetivo**: Automatizar flujos secuenciales.

1.  **Detección de Primer Escaneo**: Lógica para distinguir inicio de lote vs continuidad.
2.  **Registro Automático**:
    - `QRScanner` envía señal -> `AppController` consulta Contexto -> Llama a Repositorio con `tipo_paso` contextual.
3.  **Feedback Visual**: Barra de progreso "Unidad 5 de 100".

### Fase 4.3: Trazabilidad Multicapa Dinámica
**Objetivo**: Soportar múltiples procesos sobre el mismo QR.

1.  **Lógica `upsert` Inteligente**:
    - Modificar `TrackingRepository` para detectar conflicto de `role` (si el mismo trabajador intenta hacer el mismo paso dos veces al mismo QR -> Alerta).
    - Permitir múltiples pasos de *diferentes* tipos en el mismo QR.

### Fase 4.4: Seguridad y Cierre
**Objetivo**: Validaciones finales.

1.  **Advertencias**: "Pedido completado", "Paso duplicado".
2.  **Persistencia**: Guardar estado parcial para recuperación ante fallos.
