---
name: strict_testing
description: Guidelines and strict testing standards for the Hipatia project. Follow these rules to ensure high test quality and compliance with the dashboard.
---

# Hipatia Strict Testing Standards

When writing, updating, or refactoring tests for the Hipatia project, you **MUST** strictly adhere to the following guidelines. These rules están sincronizadas con `scripts/test_quality_analyzer.py` y se reflejan en el score real del dashboard.

---

## SCORING REAL (test_quality_analyzer.py)

El analizador detecta patrones reales en el código, no solo palabras clave.

| Criterio | Puntos |
|---|---|
| Tiene `@pytest.mark.*` | +25 |
| Usa mocks estrictos (`create_autospec`, `spec=`, `autospec=True`) | +20 |
| Verifica interacciones (`assert_called_with`, `assert_called_once_with`, etc.) | +15 |
| Valida DTOs con `isinstance(..., XxxDTO)` | +15 |
| Todos los `@patch` usan `autospec=True` | +15 |
| Tiene docstrings | +10 |
| **PENALIZACIÓN**: -5 por cada `MagicMock()` / `Mock()` suelto (sin spec) | hasta -30 |
| **PENALIZACIÓN**: -3 por cada `@patch` sin `autospec=True` | hasta -20 |
| **PENALIZACIÓN**: -5 por cada test sin ningún `assert` | hasta -20 |
| **PENALIZACIÓN**: -10 si el archivo es de ctrl/servicio y no tiene ningún `assert_called*` | -10 |
| **PENALIZACIÓN**: -3 por cada `assert_called_once()` sin argumentos | hasta -15 |
| **PENALIZACIÓN**: -8 si mockea la sesión de BD (antipatrón en repositorios) | -8 |

- **Actualizado**: score ≥ 80
- **En Progreso**: score ≥ 50
- **Legacy / Pendiente**: score < 50

> Ver skill `testing_antipatrones` para el catálogo completo de falsos positivos y cómo corregirlos.

---

## 1. Mocks Estrictos (Strict Mocks) — OBLIGATORIO

Nunca usar `MagicMock()` o `Mock()` sin spec para clases complejas (Widgets, Controllers, Repositories, Services). Los mocks sueltos ocultan errores de integración y **penalizan el score**.

```python
# ❌ INCORRECTO — mock suelto, penaliza -5 pts
mock_widget = MagicMock()
mock_service = Mock()

# ✅ CORRECTO — spec limita los atributos al contrato real
mock_widget = MagicMock(spec=ReportesWidget)

# ✅ MEJOR — create_autospec también valida firmas de métodos
from unittest.mock import create_autospec
mock_service = create_autospec(BackupService, instance=True)
```

---

## 2. Patches con autospec=True — OBLIGATORIO

Todo `@patch` debe incluir `autospec=True`. Sin él, el mock acepta cualquier argumento y oculta llamadas incorrectas. **Cada patch sin autospec penaliza -3 pts**.

```python
# ❌ INCORRECTO — penaliza -3 pts
@patch("core.services.backup_service.BackupService")
def test_something(self, MockBackup): ...

# ✅ CORRECTO
@patch("core.services.backup_service.BackupService", autospec=True)
def test_something(self, MockBackup): ...

# ✅ CORRECTO con context manager
with patch("os.makedirs", autospec=True) as mock_makedirs:
    ...
```

**Excepción válida**: usar `new_callable=` (ej: `new_callable=PropertyMock`) también es aceptado por el analizador.

---

## 3. Verificación de Interacciones — OBLIGATORIO en tests de controladores y servicios

No basta con que el código no lance excepción. Hay que verificar que los colaboradores fueron llamados correctamente.

```python
# ❌ INCORRECTO — no verifica que el servicio fue usado
def test_run_backup(self, controller):
    controller.run_backup()
    assert controller.status == "ok"

# ✅ CORRECTO
def test_run_backup(self, controller, mock_backup_service):
    controller.run_backup()
    mock_backup_service.create_backup.assert_called_once_with(
        destination=ANY, compress=True
    )
```

Métodos aceptados por el analizador:
- `assert_called_once_with(...)`
- `assert_called_with(...)`
- `assert_any_call(...)`
- `assert_called_once()`
- `assert_not_called()`
- `.call_args_list`
- `.call_count`

---

## 4. Validación de DTOs con isinstance — OBLIGATORIO donde aplique

```python
# ❌ INCORRECTO — no verifica el tipo real
def test_get_worker(self, repos):
    result = repos["worker"].get_worker(1)
    assert result is not None

# ✅ CORRECTO
from core.dtos import WorkerDTO

def test_get_worker(self, repos):
    result = repos["worker"].get_worker(1)
    assert isinstance(result, WorkerDTO)
    assert result.id == 1
```

El analizador detecta el patrón `isinstance(..., XxxDTO)` con regex. Asegúrate de que el nombre de la clase termine en `DTO`.

---

## 5. Pytest Markers — OBLIGATORIO

Cada archivo de test **DEBE** tener al menos un marker. Sin marker el archivo pierde 25 pts base.

- `@pytest.mark.unit` — tests rápidos sin I/O real
- `@pytest.mark.integration` — tests con BD real (SQLite en memoria)
- `@pytest.mark.e2e` — flujos completos de usuario
- `@pytest.mark.setup` — infraestructura y configuración

---

## 6. Docstrings — OBLIGATORIO

Módulo, clase y función deben tener docstring. Aportan +10 pts y son obligatorios por el estándar Google Style definido en `estandar_documentacion`.

```python
@pytest.mark.unit
class TestWorkerRepository:
    """Tests unitarios para WorkerRepository."""

    def test_add_worker_success(self, repos):
        """Verifica que se añade un trabajador y retorna WorkerDTO válido."""
        ...
```

---

## 6.1 Asserts triviales (`assert True`) — SOLO como último recurso

`assert True` existe únicamente para evitar el antipatrón “test sin asserts”, pero **no valida comportamiento**. En Hipatia se permite **solo** en un caso muy concreto:

- **Caso permitido (test de humo real)**: el objetivo del test es verificar que un método/constructor **no lanza excepción** y **no hay un observable mejor** (retorno, estado, interacción, UI). En ese caso:
  - Preferir antes `assert widget is not None`, `assert result is True/False`, `assert not widget.isHidden()`, `assert mock_x.call_count == N`, etc.
  - Si aun así no existe un observable razonable, entonces se permite `assert True` con **justificación explícita** en el comentario.

Formato obligatorio cuando se use:

```python
assert True  # smoke_test: no hay observable mejor sin acoplar el test al UI/headless
```

Regla práctica:
- En **Servicios/Controladores**, `assert True` debería ser **casi inexistente**: siempre suele haber interacción (`assert_called_*`) o estado retornado que validar.

---

## 7. Repositorios — usar BD real en memoria

No mockear respuestas de base de datos en tests de repositorio. Usar la fixture `repos` del conftest que inyecta SQLite en memoria con foreign keys activadas.

```python
@pytest.mark.integration
class TestWorkerRepository:
    """Tests de integración para WorkerRepository."""

    def test_add_and_retrieve(self, repos, session):
        """Verifica persistencia real con SQLAlchemy."""
        repos["worker"].add_worker("Ana", "", 2)
        workers = repos["worker"].get_all_workers()
        assert isinstance(workers[0], WorkerDTO)
```

---

## 8. UI y headless — lecciones aprendidas

### 8.1 QBrush, QColor, QPainter en headless
Parchear a nivel de módulo. **Nunca** usar `spec=QPainter` (provoca `InvalidSpecError`).

```python
@patch('ui.widgets.gantt_widget.QPen')
@patch('ui.widgets.gantt_widget.QColor')
@patch('ui.widgets.gantt_widget.QPainter')
def test_paintEvent(self, MockPainter, MockColor, MockPen, widget):
    widget.paintEvent(MagicMock())  # llamada directa, NO widget.repaint()
```

### 8.2 isVisible() siempre False en headless
```python
# ❌ siempre False sin ventana padre mapeada
assert widget.progress_bar.isVisible()
# ✅
assert not widget.progress_bar.isHidden()
```

### 8.3 QTabWidget.insertTab() requiere QWidget real
```python
mock_view = QWidget()
mock_view.setRenderHint = MagicMock()
MockChartView.return_value = mock_view
```

### 8.4 QShowEvent y eventFilter requieren objetos reales
```python
from PyQt6.QtGui import QShowEvent
widget.showEvent(QShowEvent())  # no MagicMock()
```

### 8.5 Validación de tipos C++ en constructores y eventFilter
```python
canvas = QWidget()
card = QWidget(canvas)  # requiere QWidget real, no Mock
event = QEvent(QEvent.Type.Timer)
assert effect.eventFilter(card, event) is False
```

---

## 9. Parcheo de imports locales

Si una clase importa dentro de `__init__()` o un método (no a nivel de módulo), parchear donde **vive** la clase, no donde se usa.

```python
# ❌ AttributeError — DIContainer no está en el namespace de app_controller
with patch("controllers.app_controller.DIContainer"):
    ...

# ✅ parchear en el módulo fuente
with patch("core.di_container.DIContainer"):
    ...
```

Regla rápida: `from X import Y` a nivel de módulo → `patch("modulo_bajo_prueba.Y")`. Import local dentro de método → `patch("X.Y")`.

---

## 10. Fixtures — evitar pérdida de referencias tras reinicialización

```python
# Guardar referencia ANTES de la acción que reinicializa
old_db = controller.model.db
controller.on_import_databases()
old_db.close.assert_called_once()  # verificar sobre la referencia original
```

---

## 11. Fixtures con autouse y conflictos de nombre

Dar nombres únicos a fixtures `autouse=True` de clase para evitar colisiones con fixtures del conftest.

```python
@pytest.fixture(autouse=True)
def setup_schedule_ctrl(self, controller):  # nombre único, no "setup_schedule"
    """Configura mock de schedule_controller para esta clase."""
    self.mock_sc = MagicMock()
    controller.schedule_controller = self.mock_sc
```

---

## 12. InvalidSpecError al reinicializar objetos mockeados

Si el código llama a `self.model.__init__(arg)` y `model` es un `MagicMock`, lanzará `InvalidSpecError`. Usar clase `Dummy` concreta en su lugar.

```python
# ❌ fallará si el controller hace self.model.__init__(db)
@pytest.fixture
def mock_model():
    return MagicMock()

# ✅
class DummyModel:
    def __init__(self, db_manager=None):
        self.db = MagicMock()
        self.app = MagicMock()

@pytest.fixture
def mock_model():
    return DummyModel()
```
