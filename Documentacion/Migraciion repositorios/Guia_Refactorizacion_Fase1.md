# Guía de Refactorización Fase 1: Migración a SQLAlchemy

> **Fecha de creación**: 25 de Diciembre de 2025  
> **Estado actual**: Migración parcial en curso  
> **Prioridad**: Alta

---

## 1. Resumen Ejecutivo

Este documento describe el plan completo para la **Fase 1** de la refactorización del sistema de tiempos de fabricación, centrada en la migración completa desde consultas SQLite legacy hacia SQLAlchemy con patrón Repository.

### Estado Actual del Proyecto

| Componente | Estado | Detalles |
|------------|--------|----------|
| `database_manager.py` | 🟡 Parcial | 2016 líneas, ~60% métodos migrados |
| Repositorios SQLAlchemy | 🟢 Implementados | 13 repositorios activos |
| `models.py` | 🟢 Completo | 561 líneas, 54 modelos/tablas |
| Tests | 🔴 Mínimo | Solo `test_product_repository.py` (15 tests) |
| Migraciones BD | 🟢 Completo | 11 versiones de esquema |

---

## 2. Análisis Detallado

### 2.1 Arquitectura Actual (Híbrida)

El sistema utiliza actualmente una **arquitectura híbrida** donde:

```
┌─────────────────────────────────────────────────────────────┐
│                    DatabaseManager                          │
│                     (2016 líneas)                           │
├─────────────────────────────────────────────────────────────┤
│  [MIGRADO] ─────► Repositorios SQLAlchemy                   │
│  • get_all_products()    → ProductRepository                │
│  • get_all_workers()     → WorkerRepository                 │
│  • get_all_machines()    → MachineRepository                │
│  • get_setting()         → ConfigurationRepository          │
│  • ... ~60 métodos más                                      │
├─────────────────────────────────────────────────────────────┤
│  [LEGACY] ─────► Consultas SQLite directas                  │
│  • create_tables()       → SQL directo                      │
│  • _migrate_to_v1-v11()  → SQL directo                      │
│  • get_all_prep_steps()  → SQL directo                      │
│  • get_group_details()   → SQL directo                      │
│  • delete_product()      → SQL directo                      │
│  • ... ~40 métodos más                                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Repositorios Implementados

| Repositorio | Archivo | Líneas | Métodos | Cobertura Tests |
|-------------|---------|--------|---------|-----------------|
| `ProductRepository` | `product_repository.py` | 310 | 12 | ✅ 15 tests |
| `WorkerRepository` | `worker_repository.py` | 391 | 24 | ❌ Sin tests |
| `MachineRepository` | `machine_repository.py` | 715 | ~30 | ❌ Sin tests |
| `PilaRepository` | `pila_repository.py` | 1083 | ~35 | ❌ Sin tests |
| `TrackingRepository` | `tracking_repository.py` | 1542 | 34 | ❌ Sin tests |
| `PreprocesoRepository` | `preproceso_repository.py` | 546 | ~20 | ❌ Sin tests |
| `IterationRepository` | `iteration_repository.py` | 420 | ~15 | ❌ Sin tests |
| `MaterialRepository` | `material_repository.py` | 510 | ~18 | ❌ Sin tests |
| `ConfigurationRepository` | `configuration_repository.py` | 180 | 8 | ❌ Sin tests |
| `LoteRepository` | `lote_repository.py` | 156 | 6 | ❌ Sin tests |
| `MaintenanceRepository` | `maintenance_repository.py` | 45 | 3 | ❌ Sin tests |
| `LabelCounterRepository` | `label_counter_repository.py` | 190 | ~8 | ❌ Sin tests |
| `BaseRepository` | `base.py` | 132 | 5 | ❌ Sin tests |

---

## 3. Archivos y Funciones Afectados

### 3.1 Archivos Principales a Migrar

#### [database_manager.py](file:///Users/danielsanz/Library/Mobile%20Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/database_manager.py)

**Métodos Legacy que requieren migración:**

```python
# Métodos de creación de tablas (líneas 695-858)
create_tables()                          # 163 líneas de SQL directo

# Métodos de diagnóstico (líneas 959-1057)
verify_machine_assignments()             # SQL directo
diagnose_subfabricaciones_schema()       # SQL directo

# Métodos de grupos de preparación (líneas 868-891)
get_all_prep_steps()                     # SQL directo
get_group_details()                      # SQL directo

# Métodos de máquinas (líneas 1545-1559)
get_machine_usage_stats()                # SQL directo

# Métodos de importación (líneas 1568-1598)
import_from_old_db()                     # SQL directo

# Métodos de mantenimiento (líneas 1636-1647)
add_machine_maintenance()                # SQL directo

# Métodos de integridad (líneas 1842-1863)
_verify_database_integrity()             # SQL directo

# Métodos de prueba (líneas 1865-1911)
test_all_repositories()                  # Temporal, a eliminar
```

### 3.2 Modelos SQLAlchemy ([models.py](file:///Users/danielsanz/Library/Mobile%20Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/database/models.py))

**Modelos Core:**
- `Fabricacion` (líneas 54-75)
- `Preproceso` (líneas 77-104)
- `Producto` (líneas 106-127)
- `Trabajador` (líneas 129-153)
- `Maquina` (líneas 155-169)
- `Pila` (líneas 171-188)

**Modelos Auxiliares:**
- `Subfabricacion`, `ProcesoMecanico`, `Material`
- `TrabajoLog`, `IncidenciaLog`, `PasoTrazabilidad`
- `GrupoPreparacion`, `PreparacionPaso`
- `DiarioBitacora`, `EntradaDiario`
- `ProductIteration`, `MachineMaintenanc`
- `TrabajadorPilaAnotacion`, `Lote`

---

## 4. Verificación Manual del Funcionamiento

### 4.1 Funcionalidades a Verificar en la Aplicación

| Módulo | Funcionalidad | Cómo Verificar | Repositorio Afectado |
|--------|---------------|----------------|----------------------|
| Productos | CRUD completo | Menú → Productos → Añadir/Editar/Eliminar | ProductRepository |
| Productos | Búsqueda | Barra de búsqueda en lista productos | ProductRepository |
| Trabajadores | CRUD completo | Menú → Trabajadores → Gestionar | WorkerRepository |
| Trabajadores | Autenticación | Pantalla de login | WorkerRepository |
| Máquinas | CRUD completo | Menú → Máquinas → Gestionar | MachineRepository |
| Máquinas | Grupos preparación | Máquinas → Configurar pasos | MachineRepository |
| Pilas | Crear/Gestionar | Menú → Pilas → Nueva pila | PilaRepository |
| Tracking | Iniciar trabajo QR | Escanear QR → Iniciar trabajo | TrackingRepository |
| Tracking | Finalizar trabajo | Escanear QR → Finalizar | TrackingRepository |
| Materiales | Gestión componentes | Productos → Iteraciones → Materiales | MaterialRepository |
| Configuración | Horarios/Festivos | Configuración → Calendario | ConfigurationRepository |

### 4.2 Pruebas Manuales Críticas

> [!IMPORTANT]
> Estas pruebas deben ejecutarse **antes y después** de cada fase de migración.

#### Prueba 1: Flujo Completo de Producto
```
1. Iniciar aplicación
2. Ir a Gestión de Productos
3. Crear producto nuevo con:
   - Código: TEST-MIGRATION-001
   - Descripción: Producto de prueba migración
   - Departamento: Montaje
   - Añadir 2 subfabricaciones con máquina asignada
4. Guardar y verificar que aparece en la lista
5. Editar el producto, añadir tiempo óptimo
6. Buscar el producto por código
7. Eliminar el producto
8. Verificar que ya no aparece
```

#### Prueba 2: Flujo de Trabajador y Autenticación
```
1. Ir a Gestión de Trabajadores
2. Crear trabajador nuevo: "Operario Test"
3. Asignarle credenciales de acceso
4. Cerrar sesión
5. Iniciar sesión con las nuevas credenciales
6. Verificar que el trabajador puede ver sus tareas
```

#### Prueba 3: Flujo de Tracking QR
```
1. Iniciar sesión como trabajador
2. Crear/seleccionar una fabricación
3. Escanear código QR de unidad
4. Iniciar trabajo
5. Pausar trabajo
6. Reanudar trabajo
7. Registrar incidencia
8. Finalizar trabajo
9. Verificar tiempos registrados en historial
```

---

## 5. Suite de Tests a Implementar

### 5.1 Estructura de Tests Propuesta

```
tests/
├── conftest.py           # ✅ Existe (556 líneas)
├── __init__.py           # ✅ Existe
│
├── unit/                 # Tests unitarios
│   ├── __init__.py       # ✅ Existe
│   ├── test_base_repository.py        # ❌ Crear
│   ├── test_product_repository.py     # ✅ Mover desde db/
│   ├── test_worker_repository.py      # ❌ Crear
│   ├── test_machine_repository.py     # ❌ Crear
│   ├── test_pila_repository.py        # ❌ Crear
│   ├── test_tracking_repository.py    # ❌ Crear
│   ├── test_preproceso_repository.py  # ❌ Crear
│   ├── test_material_repository.py    # ❌ Crear
│   ├── test_iteration_repository.py   # ❌ Crear
│   ├── test_config_repository.py      # ❌ Crear
│   └── test_lote_repository.py        # ❌ Crear
│
├── integration/          # Tests de integración
│   ├── __init__.py       # ✅ Existe
│   ├── test_database_manager.py       # ❌ Crear
│   ├── test_sync_changes.py           # ❌ Crear
│   └── test_migrations.py             # ❌ Crear
│
├── e2e/                  # Tests End-to-End
│   ├── __init__.py       # ✅ Existe
│   ├── test_product_workflow.py       # ❌ Crear
│   ├── test_worker_workflow.py        # ❌ Crear
│   └── test_tracking_workflow.py      # ❌ Crear
│
├── setup/                # Tests de configuración
│   ├── __init__.py       # ❌ Crear
│   ├── test_database_setup.py         # ❌ Crear
│   └── test_migrations_setup.py       # ❌ Crear
│
└── load/                 # Tests de carga
    ├── __init__.py       # ❌ Crear
    ├── test_bulk_operations.py        # ❌ Crear
    └── test_concurrent_access.py      # ❌ Crear
```

### 5.2 Tests Unitarios por Repositorio

#### WorkerRepository Tests
```python
# tests/unit/test_worker_repository.py

@pytest.mark.unit
class TestWorkerRepository:
    # CRUD básico
    def test_get_all_workers_empty(self, repos): ...
    def test_get_all_workers_with_data(self, repos, session): ...
    def test_get_all_workers_include_inactive(self, repos, session): ...
    def test_add_worker_success(self, repos): ...
    def test_add_worker_duplicate_name(self, repos, session): ...
    def test_update_worker_success(self, repos, session): ...
    def test_delete_worker_success(self, repos, session): ...
    def test_get_worker_details_existing(self, repos, session): ...
    def test_get_worker_details_not_found(self, repos): ...
    def test_get_latest_workers(self, repos, session): ...
    
    # Autenticación
    def test_authenticate_user_success(self, repos, session): ...
    def test_authenticate_user_wrong_password(self, repos, session): ...
    def test_authenticate_user_not_found(self, repos): ...
    def test_update_user_credentials(self, repos, session): ...
    def test_update_user_password(self, repos, session): ...
    
    # Anotaciones
    def test_add_worker_annotation(self, repos, session): ...
    def test_get_worker_annotations_empty(self, repos, session): ...
    def test_get_worker_annotations_with_data(self, repos, session): ...
```

#### MachineRepository Tests
```python
# tests/unit/test_machine_repository.py

@pytest.mark.unit
class TestMachineRepository:
    # CRUD básico
    def test_get_all_machines_empty(self, repos): ...
    def test_get_all_machines_with_data(self, repos, session): ...
    def test_add_machine_success(self, repos): ...
    def test_add_machine_duplicate(self, repos, session): ...
    def test_update_machine_success(self, repos, session): ...
    def test_delete_machine_success(self, repos, session): ...
    def test_get_machine_details(self, repos, session): ...
    def test_get_machines_by_process_type(self, repos, session): ...
    
    # Grupos de preparación
    def test_add_prep_group(self, repos, session): ...
    def test_get_prep_groups_for_machine(self, repos, session): ...
    def test_update_prep_group(self, repos, session): ...
    def test_delete_prep_group(self, repos, session): ...
    
    # Pasos de preparación
    def test_add_prep_step(self, repos, session): ...
    def test_get_steps_for_group(self, repos, session): ...
    def test_update_prep_step(self, repos, session): ...
    def test_delete_prep_step(self, repos, session): ...
```

#### TrackingRepository Tests
```python
# tests/unit/test_tracking_repository.py

@pytest.mark.unit
class TestTrackingRepository:
    # TrabajoLog
    def test_obtener_o_crear_trabajo_log_nuevo(self, repos, session): ...
    def test_obtener_trabajo_existente(self, repos, session): ...
    def test_finalizar_trabajo_log(self, repos, session): ...
    def test_pausar_trabajo(self, repos, session): ...
    def test_reanudar_trabajo(self, repos, session): ...
    
    # PasoTrazabilidad
    def test_iniciar_nuevo_paso(self, repos, session): ...
    def test_finalizar_paso(self, repos, session): ...
    def test_get_pasos_por_trabajo(self, repos, session): ...
    def test_get_paso_activo_por_trabajador(self, repos, session): ...
    
    # Incidencias
    def test_registrar_incidencia(self, repos, session): ...
    def test_obtener_incidencias_por_trabajo(self, repos, session): ...
    def test_añadir_adjunto_incidencia(self, repos, session): ...
    
    # Fabricaciones
    def test_get_fabricaciones_por_trabajador(self, repos, session): ...
    def test_asignar_trabajador_fabricacion(self, repos, session): ...
    def test_actualizar_estado_asignacion(self, repos, session): ...
```

### 5.3 Tests de Integración

```python
# tests/integration/test_database_manager.py

@pytest.mark.integration
class TestDatabaseManagerIntegration:
    def test_initialization_creates_all_tables(self, temp_db_file): ...
    def test_repositories_share_connection(self, in_memory_db_manager): ...
    def test_transaction_rollback_on_error(self, in_memory_db_manager): ...
    def test_concurrent_session_access(self, in_memory_db_manager): ...
    
# tests/integration/test_migrations.py

@pytest.mark.integration
class TestMigrations:
    def test_migrate_from_v0_to_latest(self, temp_db_file): ...
    def test_migrate_idempotent(self, temp_db_file): ...
    def test_migrate_preserves_data(self, temp_db_file): ...
```

### 5.4 Tests E2E

```python
# tests/e2e/test_product_workflow.py

@pytest.mark.e2e
class TestProductWorkflow:
    def test_complete_product_lifecycle(self, in_memory_db_manager): ...
    def test_product_with_subfabricaciones(self, in_memory_db_manager): ...
    def test_search_and_filter_products(self, in_memory_db_manager): ...
```

### 5.5 Tests de Setup

```python
# tests/setup/test_database_setup.py

@pytest.mark.setup
class TestDatabaseSetup:
    def test_new_database_creation(self, temp_db_file): ...
    def test_default_admin_user_created(self, temp_db_file): ...
    def test_all_essential_tables_exist(self, temp_db_file): ...
    def test_foreign_keys_enabled(self, temp_db_file): ...
```

### 5.6 Tests de Carga

```python
# tests/load/test_bulk_operations.py

@pytest.mark.load
@pytest.mark.slow
class TestBulkOperations:
    def test_insert_1000_products(self, in_memory_db_manager): ...
    def test_query_10000_records(self, in_memory_db_manager): ...
    def test_concurrent_writes(self, temp_db_file): ...
    def test_memory_usage_large_dataset(self, in_memory_db_manager): ...
```

---

## 6. Modificaciones al Script de Tests

### 6.1 Actualización de [run_all_tests.py](file:///Users/danielsanz/Library/Mobile%20Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion/run_all_tests.py)

```python
# Añadir al TestConfig

class TestConfig:
    # ... configuración existente ...
    
    # NUEVA: Configuración de cobertura por módulo
    COVERAGE_BY_MODULE = {
        'database.repositories.product_repository': {
            'archivo': 'product_repository.py',
            'tests': 'tests/unit/test_product_repository.py',
            'min_coverage': 90,
        },
        'database.repositories.worker_repository': {
            'archivo': 'worker_repository.py',
            'tests': 'tests/unit/test_worker_repository.py',
            'min_coverage': 85,
        },
        # ... más módulos
    }
    
    # NUEVA: Matrices de bases de datos probadas
    DATABASE_TESTS = {
        'sqlite_memory': ':memory:',
        'sqlite_file': 'test_temp.db',
    }
```

### 6.2 Nuevo Informe de Cobertura Específica

El informe generado debe incluir:

```
═══════════════════════════════════════════════════════════════════════
INFORME DE COBERTURA - MIGRACIÓN SQLAlchemy Fase 1
═══════════════════════════════════════════════════════════════════════

📊 RESUMEN POR REPOSITORIO
───────────────────────────────────────────────────────────────────────
| Repositorio              | Líneas | Cubiertas | % Cob. | Estado  |
|--------------------------|--------|-----------|--------|---------|
| ProductRepository        | 310    | 287       | 92.6%  | ✅ OK   |
| WorkerRepository         | 391    | 0         | 0.0%   | ❌ FAIL |
| MachineRepository        | 715    | 0         | 0.0%   | ❌ FAIL |
| PilaRepository           | 1083   | 0         | 0.0%   | ❌ FAIL |
| TrackingRepository       | 1542   | 0         | 0.0%   | ❌ FAIL |
| ...                      |        |           |        |         |
───────────────────────────────────────────────────────────────────────

📊 RESUMEN POR TIPO DE TEST
───────────────────────────────────────────────────────────────────────
| Tipo        | Tests | Pasados | Fallidos | % Éxito |
|-------------|-------|---------|----------|---------|
| unit        | 15    | 15      | 0        | 100%    |
| integration | 0     | 0       | 0        | N/A     |
| e2e         | 0     | 0       | 0        | N/A     |
| setup       | 0     | 0       | 0        | N/A     |
| load        | 0     | 0       | 0        | N/A     |
───────────────────────────────────────────────────────────────────────

📊 BASES DE DATOS PROBADAS
───────────────────────────────────────────────────────────────────────
✅ SQLite en memoria (:memory:)
✅ SQLite en archivo (test_temp.db)
───────────────────────────────────────────────────────────────────────
```

---

## 7. Proceso de Migración

> [!CAUTION]
> **NO PROCEDER CON LA MIGRACIÓN** hasta que:
> 1. Todos los tests de repositorios pasen al 100%
> 2. La cobertura sea ≥ 85% en cada repositorio
> 3. Las pruebas manuales documenten el comportamiento esperado

### 7.1 Fase 1: Preparación (Estado Actual)
1. ✅ Analizar estado actual del código
2. ✅ Documentar arquitectura híbrida
3. ⏳ Crear suite completa de tests
4. ⏳ Ejecutar tests y alcanzar cobertura objetivo

### 7.2 Fase 2: Migración de Métodos Restantes
1. Migrar `create_tables()` a SQLAlchemy `Base.metadata.create_all()`
2. Migrar `get_all_prep_steps()` a MachineRepository
3. Migrar `get_group_details()` a MachineRepository
4. Migrar `get_machine_usage_stats()` a MachineRepository
5. Migrar `delete_product()` a ProductRepository
6. Migrar `add_machine_maintenance()` a MaintenanceRepository

### 7.3 Fase 3: Limpieza
1. Eliminar código SQLite legacy duplicado
2. Eliminar método `test_all_repositories()` temporal
3. Optimizar imports
4. Actualizar documentación

### 7.4 Fase 4: Verificación Final
1. Ejecutar suite completa de tests
2. Ejecutar pruebas manuales documentadas
3. Verificar rendimiento
4. Generar informe final

---

## 8. Comandos de Ejecución

### Ejecutar todos los tests con cobertura:
```bash
cd /Users/danielsanz/Library/Mobile\ Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion
python run_all_tests.py --all
```

### Ejecutar solo tests unitarios:
```bash
pytest tests/unit/ -v --cov=database.repositories --cov-report=html
```

### Ejecutar tests de un repositorio específico:
```bash
pytest tests/unit/test_worker_repository.py -v --cov=database.repositories.worker_repository
```

### Ejecutar tests de integración:
```bash
pytest tests/integration/ -v -m integration
```

### Generar informe de cobertura HTML:
```bash
pytest --cov=database --cov-report=html:test_reports/coverage
```

---

## 9. Criterios de Éxito

| Criterio | Objetivo | Actual |
|----------|----------|--------|
| Tests unitarios por repositorio | ≥ 10 por cada | 15 solo para ProductRepository |
| Cobertura por repositorio | ≥ 85% | ~8% (solo 1 de 13) |
| Tests de integración | ≥ 5 | 0 |
| Tests E2E | ≥ 3 | 0 |
| Tests de setup | ≥ 3 | 0 |
| Tests de carga | ≥ 2 | 0 |
| Todos los tests pasando | 100% | N/A |

---

## 10. Próximos Pasos Inmediatos

1. **Crear tests para WorkerRepository** - Prioridad Alta
2. **Crear tests para MachineRepository** - Prioridad Alta
3. **Crear tests para TrackingRepository** - Prioridad Alta
4. **Modificar run_all_tests.py** para informe detallado
5. **Ejecutar suite y documentar resultados**

---

> [!NOTE]
> Este documento debe actualizarse conforme avance la migración. Cada sección de tests completada debe marcarse como ✅ y documentar los resultados.
