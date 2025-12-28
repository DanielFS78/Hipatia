# Guía de Creación de Tests para Repositorios

> **Guía práctica para implementar una suite de tests completa en proyectos Python con SQLAlchemy y DTOs.**

Esta guía establece los estándares y patrones para crear tests en el proyecto, asegurando cobertura completa y consistencia entre repositorios.

---

## Índice

1. [Estructura de Directorios](#estructura-de-directorios)
2. [Tests Unitarios](#tests-unitarios-pytest-mark-unit)
3. [Tests de Integración](#tests-de-integración-pytest-mark-integration)
4. [Tests End-to-End (E2E)](#tests-end-to-end-e2e-pytest-mark-e2e)
5. [Tests de Setup](#tests-de-setup-pytest-mark-setup)
6. [Checklist de Cobertura](#checklist-de-cobertura-para-nuevos-repositorios)
7. [Patrones y Buenas Prácticas](#patrones-y-buenas-prácticas)

---

## Estructura de Directorios

```
tests/
├── conftest.py           # Fixtures compartidas globales
├── unit/                 # Tests unitarios (rápidos, aislados)
│   ├── test_worker_repository.py
│   ├── test_product_repository.py
│   └── test_machine_repository.py
├── integration/          # Tests de integración entre componentes
│   ├── test_worker_integration.py
│   └── test_pila_integration.py
├── e2e/                  # Tests end-to-end (flujos completos)
│   ├── test_worker_workflow.py
│   └── test_product_workflow.py
└── setup/                # Tests de configuración/esquema
    ├── test_worker_setup.py
    └── test_product_setup.py
```

---

## Tests Unitarios (`@pytest.mark.unit`)

### ¿Qué son?
Tests rápidos y aislados que prueban **un único método** del repositorio. Utilizan base de datos en memoria y no dependen de servicios externos.

### ¿Qué deben cubrir?

| Categoría | Ejemplo de Test |
|-----------|-----------------|
| **Happy Path** | Operación exitosa con datos válidos |
| **Empty State** | Comportamiento con BD vacía |
| **Not Found** | Entidad que no existe (ID/código inválido) |
| **Edge Cases** | Valores límite, caracteres especiales |
| **Tipos de Datos** | Verificar que los DTOs tienen tipos correctos |

### Estructura Recomendada

```python
# tests/unit/test_{entidad}_repository.py

import pytest
from database.models import {Entidad}
from core.dtos import {Entidad}DTO

@pytest.mark.unit
class Test{Entidad}RepositoryGetMethods:
    """Tests para métodos de obtención (GET)."""
    
    def test_get_all_{entidades}_empty(self, repos):
        """BD vacía debe devolver lista vacía."""
        pass
    
    def test_get_all_{entidades}_with_data(self, repos, session):
        """Con datos debe devolver DTOs correctamente."""
        pass

@pytest.mark.unit
class Test{Entidad}RepositoryCRUD:
    """Tests para operaciones CRUD."""
    
    def test_add_{entidad}_success(self, repos):
        pass
    
    def test_update_{entidad}_success(self, repos, session):
        pass
    
    def test_update_{entidad}_not_found(self, repos):
        pass
    
    def test_delete_{entidad}_success(self, repos, session):
        pass
    
    def test_delete_{entidad}_not_found(self, repos):
        pass

@pytest.mark.unit
class Test{Entidad}RepositoryEdgeCases:
    """Tests para casos límite."""
    pass
```

### Patrón AAA (Arrange-Act-Assert)

```python
def test_get_product_details_simple(self, repos, session):
    """Ejemplo de patrón AAA."""
    product_repo = repos["product"]
    
    # 1. ARRANGE: Preparar datos de prueba
    p = Producto(
        codigo="TEST-001",
        descripcion="Producto de prueba",
        departamento="Montaje",
        tipo_trabajador=1,
        tiene_subfabricaciones=False
    )
    session.add(p)
    session.commit()
    
    # 2. ACT: Ejecutar la acción a probar
    producto, subfabs, procesos = product_repo.get_product_details("TEST-001")
    
    # 3. ASSERT: Verificar resultados usando DTOs
    assert producto is not None
    assert isinstance(producto, ProductDTO)  # ← Verificar tipo DTO
    assert producto.codigo == "TEST-001"     # ← Acceso por atributo, no índice
    assert producto.descripcion == "Producto de prueba"
```

### Verificación de DTOs

> [!IMPORTANT]
> **Siempre verificar que los métodos devuelven DTOs, no tuplas ni diccionarios.**

```python
# ✅ CORRECTO: Acceso por atributo a DTO
assert workers[0].nombre_completo == "Ana García"
assert isinstance(workers[0], WorkerDTO)

# ❌ INCORRECTO: Acceso por índice (tupla)
assert workers[0][1] == "Ana García"  # NO USAR
```

---

## Tests de Integración (`@pytest.mark.integration`)

### ¿Qué son?
Tests que verifican la **interacción entre múltiples componentes** (repositorios, modelos, relaciones de BD).

### ¿Cuándo usarlos?

- Operaciones que afectan múltiples tablas
- Validar relaciones/foreign keys en acción
- Verificar cascadas de eliminación
- Transacciones con múltiples pasos

### Estructura Recomendada

```python
# tests/integration/test_{entidad}_integration.py

import pytest
from database.models import {Entidad}, {EntidadRelacionada}

@pytest.mark.integration
class Test{Entidad}Integration:
    """Tests de integración para {Entidad}."""
    
    def test_{entidad}_with_{relacionada}_creation(self, repos, session):
        """Verifica creación con entidades relacionadas."""
        pass
    
    def test_{entidad}_cascade_delete(self, repos, session):
        """Verifica que eliminación en cascada funciona."""
        pass
    
    def test_multiple_repositories_interaction(self, repos, session):
        """Verifica que varios repos trabajan juntos correctamente."""
        pass
```

### Ejemplo Práctico

```python
@pytest.mark.integration
def test_product_with_subfabricaciones_cascade(self, repos, session):
    """Eliminar producto debe eliminar sus subfabricaciones."""
    product_repo = repos["product"]
    
    # Arrange: Crear producto con subfabricaciones
    data = {
        "codigo": "CASCADE-001",
        "descripcion": "Test Cascada",
        "departamento": "Test",
        "tipo_trabajador": 1,
        "tiene_subfabricaciones": True
    }
    subfabs = [
        {"descripcion": "Sub 1", "tiempo": 10.0, "tipo_trabajador": 1}
    ]
    product_repo.add_product(data, subfabs)
    
    # Act: Eliminar producto
    result = product_repo.delete_product("CASCADE-001")
    
    # Assert: Subfabricaciones también eliminadas
    assert result == True
    from sqlalchemy import select
    from database.models import Subfabricacion
    remaining = session.execute(
        select(Subfabricacion).where(Subfabricacion.producto_codigo == "CASCADE-001")
    ).scalars().all()
    assert len(remaining) == 0
```

---

## Tests End-to-End (E2E) (`@pytest.mark.e2e`)

### ¿Qué son?
Tests que simulan **flujos completos de usuario**, desde la creación hasta la eliminación de una entidad, pasando por todas las operaciones intermedias.

### ¿Qué deben cubrir?

| Fase del Flujo | Operaciones |
|----------------|-------------|
| **Creación** | Añadir entidad con todos sus componentes |
| **Búsqueda** | Verificar que aparece en resultados |
| **Lectura** | Obtener detalles completos |
| **Actualización** | Modificar campos y subentidades |
| **Verificación** | Confirmar que cambios persistieron |
| **Eliminación** | Borrar y confirmar que no existe |

### Estructura Recomendada

```python
# tests/e2e/test_{entidad}_workflow.py

import pytest
from core.dtos import {Entidad}DTO

@pytest.mark.e2e
class Test{Entidad}Workflow:
    """Tests E2E simulando flujos reales de {Entidad}."""
    
    def test_full_{entidad}_lifecycle(self, repos, session):
        """
        Escenario: Usuario gestiona el ciclo de vida completo.
        
        1. Crear {entidad} con componentes
        2. Buscar y verificar existencia
        3. Verificar detalles iniciales
        4. Actualizar {entidad}
        5. Verificar actualizaciones
        6. Eliminar {entidad}
        """
        pass
```

### Ejemplo Práctico

```python
@pytest.mark.e2e
def test_full_product_lifecycle(self, repos, session):
    """Ciclo de vida completo de un producto."""
    product_repo = repos["product"]
    
    # 1. CREAR
    print("\nStep 1: Crear producto")
    prod_data = {
        "codigo": "LIFECYCLE-001",
        "descripcion": "Producto E2E",
        "departamento": "Montaje",
        "tipo_trabajador": 2,
        "tiene_subfabricaciones": True
    }
    subfabs = [
        {"descripcion": "Paso 1", "tiempo": 15.0, "tipo_trabajador": 1, "maquina_id": None}
    ]
    success = product_repo.add_product(prod_data, subfabs)
    assert success is True
    
    # 2. BUSCAR
    print("Step 2: Buscar producto")
    results = product_repo.search_products("LIFECYCLE")
    assert len(results) == 1
    assert isinstance(results[0], ProductDTO)  # ← DTOs, no tuplas
    
    # 3. VERIFICAR DETALLES
    print("Step 3: Verificar detalles")
    product, subfabricaciones, _ = product_repo.get_product_details("LIFECYCLE-001")
    assert product.descripcion == "Producto E2E"
    assert len(subfabricaciones) == 1
    
    # 4. ACTUALIZAR
    print("Step 4: Actualizar producto")
    updated_data = prod_data.copy()
    updated_data["descripcion"] = "Producto E2E - V2"
    success = product_repo.update_product("LIFECYCLE-001", updated_data, [])
    assert success is True
    
    # 5. VERIFICAR ACTUALIZACIONES
    print("Step 5: Verificar actualizaciones")
    product_v2, _, _ = product_repo.get_product_details("LIFECYCLE-001")
    assert product_v2.descripcion == "Producto E2E - V2"
    
    # 6. ELIMINAR
    print("Step 6: Eliminar producto")
    success = product_repo.delete_product("LIFECYCLE-001")
    assert success is True
    
    # Verificar eliminación
    deleted, _, _ = product_repo.get_product_details("LIFECYCLE-001")
    assert deleted is None
```

---

## Tests de Setup (`@pytest.mark.setup`)

### ¿Qué son?
Tests que verifican que el **esquema de base de datos** está correctamente configurado: tablas, columnas, tipos, claves primarias y foráneas.

### ¿Qué deben cubrir?

| Verificación | Descripción |
|--------------|-------------|
| **Tablas existen** | La tabla principal y relacionadas están creadas |
| **Columnas correctas** | Todas las columnas esperadas existen |
| **Clave primaria** | PK está definida correctamente |
| **Claves foráneas** | FKs hacia tablas relacionadas existen |
| **Índices** | (Opcional) Índices de performance existen |

### Estructura Recomendada

```python
# tests/setup/test_{entidad}_setup.py

import pytest
from sqlalchemy import inspect
from database.models import Base, {Entidad}

@pytest.mark.setup
class Test{Entidad}DatabaseSetup:
    """Tests de configuración de esquema para {Entidad}."""
    
    def test_{tabla}_table_exists(self, session):
        """Verifica que la tabla principal existe."""
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        assert "{tabla}" in tables
    
    def test_{tabla}_table_columns(self, session):
        """Verifica columnas de la tabla."""
        inspector = inspect(session.bind)
        columns = {c['name']: c for c in inspector.get_columns("{tabla}")}
        
        expected_columns = ['id', 'nombre', ...]  # Listar columnas esperadas
        
        for col_name in expected_columns:
            assert col_name in columns, f"Falta columna {col_name}"
    
    def test_{tabla}_primary_key(self, session):
        """Verifica clave primaria."""
        inspector = inspect(session.bind)
        pk = inspector.get_pk_constraint("{tabla}")
        assert '{pk_column}' in pk['constrained_columns']
    
    def test_{tabla_relacionada}_foreign_key(self, session):
        """Verifica FK hacia tabla relacionada."""
        inspector = inspect(session.bind)
        fks = inspector.get_foreign_keys("{tabla_relacionada}")
        fk_tables = [fk['referred_table'] for fk in fks]
        assert "{tabla}" in fk_tables
```

### Ejemplo Práctico

```python
@pytest.mark.setup
def test_productos_table_exists(self, session):
    """Verifica que la tabla 'productos' existe en la BD."""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "productos" in tables

@pytest.mark.setup
def test_subfabricaciones_foreign_key(self, session):
    """Verifica que subfabricaciones tiene FK hacia productos."""
    inspector = inspect(session.bind)
    fks = inspector.get_foreign_keys("subfabricaciones")
    fk_tables = [fk['referred_table'] for fk in fks]
    
    assert "productos" in fk_tables
```

---

## Checklist de Cobertura para Nuevos Repositorios

Utiliza este checklist al crear tests para un nuevo repositorio:

### Tests Unitarios

- [ ] **GET vacío**: `get_all_*()` devuelve `[]` con BD vacía
- [ ] **GET con datos**: Devuelve DTOs correctamente formateados
- [ ] **GET filtrado**: Filtros opcionales funcionan (ej: `include_inactive`)
- [ ] **SEARCH vacío/corto**: Consulta vacía devuelve todo, muy corta devuelve `[]`
- [ ] **SEARCH match**: Búsqueda encuentra por múltiples campos
- [ ] **GET details existente**: Devuelve DTO con todos los campos
- [ ] **GET details no existe**: Devuelve `None` o tupla con valores vacíos
- [ ] **ADD success**: Crear entidad funciona
- [ ] **ADD con relaciones**: Crear con subentidades funciona
- [ ] **ADD duplicado**: Comportamiento correcto (error o actualización)
- [ ] **UPDATE success**: Modificar datos funciona
- [ ] **UPDATE no existe**: Devuelve `False`
- [ ] **DELETE success**: Eliminar funciona
- [ ] **DELETE no existe**: Devuelve `False`
- [ ] **Edge cases**: Caracteres especiales, valores límite

### Tests de Integración

- [ ] **Creación con relaciones**: Entidad + subentidades se crean juntas
- [ ] **Cascada eliminación**: Eliminar padre elimina hijos
- [ ] **Multi-repositorio**: Operaciones que usan varios repos funcionan

### Tests E2E

- [ ] **Ciclo de vida completo**: Create → Read → Update → Delete

### Tests de Setup

- [ ] **Tabla existe**: Tabla principal creada
- [ ] **Columnas correctas**: Todas las esperadas existen
- [ ] **PK correcta**: Clave primaria definida
- [ ] **FKs correctas**: Claves foráneas hacia tablas relacionadas

---

## Patrones y Buenas Prácticas

### 1. Usar Fixtures de `conftest.py`

```python
# La fixture `repos` proporciona todos los repositorios
def test_example(self, repos, session):
    product_repo = repos["product"]
    worker_repo = repos["worker"]
```

### 2. Capturar IDs Antes de Operaciones

```python
# ✅ CORRECTO: Capturar ID antes de usar en otra operación
worker = Trabajador(nombre_completo="Test")
session.add(worker)
session.commit()
worker_id = worker.id  # Capturar aquí

# Luego usar worker_id en otras operaciones
details = worker_repo.get_worker_details(worker_id)
```

### 3. Verificar Tipos de Retorno

```python
# Siempre verificar que es el DTO correcto
assert isinstance(result, ProductDTO)
assert isinstance(results[0], WorkerDTO)
```

### 4. Documentar Tests con Docstrings

```python
def test_add_product_with_invalid_maquina_id(self, repos):
    """
    Prueba que add_product() maneja maquina_id inválido gracefully.
    
    Cuando maquina_id tiene un valor no convertible a int,
    debe loggearse un warning y asignarse como None.
    """
```

### 5. Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/ -v --tb=short -m unit

# Tests de integración
pytest tests/integration/ -v --tb=short -m integration

# Tests E2E
pytest tests/e2e/ -v --tb=short -m e2e

# Tests de setup
pytest tests/setup/ -v --tb=short -m setup

# Todos los tests
pytest tests/ -v --tb=short

# Con cobertura
pytest tests/ -v --cov=database/repositories --cov-report=html
```

---

## Resumen

| Tipo | Marcador | Propósito | Velocidad |
|------|----------|-----------|-----------|
| **Unit** | `@pytest.mark.unit` | Un método, aislado | ⚡ Rápido |
| **Integration** | `@pytest.mark.integration` | Interacción componentes | 🔄 Medio |
| **E2E** | `@pytest.mark.e2e` | Flujos completos | 🐢 Lento |
| **Setup** | `@pytest.mark.setup` | Esquema BD | ⚡ Rápido |

> [!TIP]
> **Regla de oro**: Ejecuta tests unitarios frecuentemente durante desarrollo, E2E antes de commits importantes.
