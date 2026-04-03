---
name: Testing por Capa
description: Qué testear y cómo en cada capa de Hipatia — Repositorios, Servicios, Controladores y UI/Widgets. Incluye plantillas de test listas para usar y los errores más comunes por capa.
---

# Testing por Capa

> Skill especializada. Léela junto con `strict_testing` (reglas generales) y `testing_fixtures_y_mocks` (cómo construir mocks).

---

## Mapa de capas y estrategia

| Capa | Marker | BD | Mocks | Verificar |
|---|---|---|---|---|
| Repositorios | `@pytest.mark.integration` | SQLite real (fixture `repos`) | Ninguno | DTOs con `isinstance`, persistencia real |
| Servicios | `@pytest.mark.unit` | Mock de `DatabaseManager` | `create_autospec(DatabaseManager)` | Interacciones con `assert_called_*` + retorno |
| Controladores | `@pytest.mark.unit` | Mock de `AppController` | `create_autospec(AppController)` | Interacciones con `assert_called_*` |
| UI / Widgets | `@pytest.mark.unit` | No aplica | Servicios mockeados, widget real | Estado de widgets, señales conectadas |
| E2E | `@pytest.mark.e2e` | SQLite real | Mínimos | Flujo completo de usuario |

---

## Capa 1: Repositorios

### Reglas
- Usar siempre la fixture `repos` del conftest (SQLite en memoria, foreign keys ON)
- No mockear nada de la BD — el punto es probar la interacción real con SQLAlchemy
- Verificar que el retorno es un DTO con `isinstance`
- Verificar el contenido del DTO, no solo que no sea `None`

### Plantilla

```python
# tests/unit/test_worker_repository.py
"""Tests de integración para WorkerRepository."""
import pytest
from database.models import Trabajador
from core.dtos import WorkerDTO


@pytest.mark.integration
class TestWorkerRepository:
    """Tests de integración para WorkerRepository usando BD en memoria."""

    def test_add_and_get_worker(self, repos, session):
        """Verifica que se persiste un trabajador y se recupera como WorkerDTO."""
        # Arrange
        worker_repo = repos["worker"]

        # Act
        worker_repo.add_worker("Ana García", "Notas", 2)
        workers = worker_repo.get_all_workers()

        # Assert
        assert len(workers) == 1
        assert isinstance(workers[0], WorkerDTO)   # ← obligatorio
        assert workers[0].nombre_completo == "Ana García"
        assert workers[0].tipo_trabajador == 2

    def test_get_nonexistent_worker_returns_none(self, repos):
        """Verifica que buscar un ID inexistente retorna None."""
        result = repos["worker"].get_worker(9999)
        assert result is None
```

### Errores comunes en esta capa
- Usar `MagicMock()` para simular la sesión → invalida el test completamente
- No verificar el tipo del retorno → el repositorio puede devolver un dict y el test pasa
- No probar el caso `None` / lista vacía → las ramas de error quedan sin cubrir

---

## Capa 2: Servicios

### Reglas
- Mockear `DatabaseManager` con `create_autospec`
- Verificar que el servicio llama al repositorio correcto con los argumentos correctos
- Verificar el valor de retorno
- No probar lógica de BD aquí — eso es responsabilidad de los tests de repositorio

### Plantilla

```python
# tests/unit/test_preparation_service.py
"""Tests unitarios para PreparationService."""
import pytest
from unittest.mock import create_autospec
from core.services.preparation_service import PreparationService
from database.database_manager import DatabaseManager
from core.dtos import PreparationGroupDTO


@pytest.mark.unit
class TestPreparationService:
    """Tests unitarios para PreparationService."""

    @pytest.fixture
    def mock_db(self):
        """Mock estricto de DatabaseManager."""
        db = create_autospec(DatabaseManager, instance=True)
        db.machine_repo = create_autospec(db.machine_repo.__class__, instance=True)
        return db

    @pytest.fixture
    def service(self, mock_db):
        """PreparationService con dependencias mockeadas."""
        return PreparationService(mock_db)

    def test_get_groups_for_machine_calls_repo(self, service, mock_db):
        """Verifica que delega correctamente al repositorio."""
        expected = [PreparationGroupDTO(id=1, nombre="G1", descripcion="D1")]
        mock_db.machine_repo.get_groups_for_machine.return_value = expected

        result = service.get_groups_for_machine(machine_id=1)

        # Verificar retorno
        assert result == expected
        assert isinstance(result[0], PreparationGroupDTO)
        # Verificar interacción — OBLIGATORIO en tests de servicio
        mock_db.machine_repo.get_groups_for_machine.assert_called_once_with(1)

    def test_add_group_returns_new_id(self, service, mock_db):
        """Verifica que retorna el ID del nuevo grupo."""
        mock_db.machine_repo.add_prep_group.return_value = 42

        result = service.add_prep_group(machine_id=1, nombre="G1", descripcion="D1")

        assert result == 42
        mock_db.machine_repo.add_prep_group.assert_called_once_with(1, "G1", "D1", None)
```

### Errores comunes en esta capa
- No llamar a `assert_called_once_with` → el test verifica el retorno pero no que el servicio haga algo
- Usar `MagicMock()` para `mock_db` → el servicio puede llamar a un método inexistente y el test pasa
- Testear lógica de BD en lugar de lógica de negocio

---

## Capa 3: Controladores

### Reglas
- Mockear `AppController` con `create_autospec` (o `DummyModel` si hay reinicialización)
- Verificar que el controlador llama al servicio/modelo correcto con los argumentos correctos
- Verificar que la vista recibe los mensajes correctos
- No testear lógica de negocio aquí — eso es responsabilidad de los tests de servicio

### Plantilla

```python
# tests/unit/test_backup_controller.py
"""Tests unitarios para BackupController."""
import pytest
from unittest.mock import create_autospec, patch
from controllers.backup_controller import BackupController
from controllers.app_controller import AppController
from core.services.backup_service import BackupService


@pytest.mark.unit
class TestBackupController:
    """Tests unitarios para BackupController."""

    @pytest.fixture
    def mock_app(self):
        """Mock estricto de AppController."""
        app = create_autospec(AppController, instance=True)
        app.model = create_autospec(app.model.__class__, instance=True)
        app.view = create_autospec(app.view.__class__, instance=True)
        return app

    @pytest.fixture
    def mock_backup_service(self):
        """Mock estricto de BackupService."""
        return create_autospec(BackupService, instance=True)

    @pytest.fixture
    def controller(self, mock_app, mock_backup_service):
        """BackupController con dependencias mockeadas."""
        return BackupController(
            db=mock_app.model.db,
            view=mock_app.view,
            logger=create_autospec(object),
            backup_service=mock_backup_service,
        )

    def test_create_backup_calls_service(self, controller, mock_backup_service):
        """Verifica que create_automatic_backup delega al servicio."""
        mock_backup_service.create_backup.return_value = True

        result = controller.create_automatic_backup()

        assert result is True
        mock_backup_service.create_backup.assert_called_once()  # ← OBLIGATORIO

    def test_create_backup_shows_error_on_failure(self, controller, mock_backup_service, mock_app):
        """Verifica que se muestra error cuando el servicio falla."""
        mock_backup_service.create_backup.side_effect = Exception("Disco lleno")

        result = controller.create_automatic_backup()

        assert result is False
        mock_app.view.show_message.assert_called_once()  # ← verificar que la UI recibe el error
```

### Errores comunes en esta capa
- No verificar que la vista recibe mensajes de error → el controlador puede fallar silenciosamente
- Usar `MagicMock()` para el servicio → el controlador puede llamar a métodos inexistentes
- Testear lógica de negocio del servicio en lugar de la delegación del controlador

---

## Capa 4: UI / Widgets

### Reglas
- Instanciar el widget real (no mockearlo) — esto captura errores de `__init__`
- Mockear solo las dependencias externas (servicios, controladores)
- Usar `qtbot.addWidget()` para registro y limpieza
- Llamar `paintEvent` directamente, nunca `repaint()` (el event loop traga excepciones)
- Usar `isHidden()` en lugar de `isVisible()` en entorno headless
- Para `QTabWidget.insertTab()`, usar `QWidget()` real como `return_value`
- Evitar `assert True`: preferir `assert widget is not None`, asserts de estado interno y/o asserts de interacciones

### Plantilla

```python
# tests/unit/ui/test_dashboard_widget.py
"""Tests unitarios para DashboardWidget."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QWidget, QApplication
from ui.widgets.dashboard_widget import DashboardWidget
from controllers.app_controller import AppController


@pytest.mark.unit
class TestDashboardWidget:
    """Tests unitarios para DashboardWidget en entorno headless."""

    @pytest.fixture
    def mock_controller(self):
        """Mock estricto del controlador."""
        return create_autospec(AppController, instance=True)

    @pytest.fixture
    def widget(self, qtbot, mock_controller):
        """DashboardWidget real con controlador mockeado."""
        # Parchear clases gráficas que causan SIGABRT en headless
        with patch('ui.widgets.dashboard_widget.QChart') as MockChart, \
             patch('ui.widgets.dashboard_widget.QChartView') as MockChartView, \
             patch('ui.widgets.dashboard_widget.QPainter'):
            # QChartView debe devolver QWidget real para insertTab
            mock_view = QWidget()
            mock_view.setRenderHint = MagicMock()
            MockChartView.return_value = mock_view

            w = DashboardWidget(controller=mock_controller)
            qtbot.addWidget(w)
            return w

    def test_init_creates_widget(self, widget):
        """Verifica que el widget se inicializa sin errores."""
        assert widget is not None
        assert not widget.isHidden()  # ← isHidden(), no isVisible()

    def test_paint_event_does_not_crash(self, widget):
        """Verifica que paintEvent no lanza excepciones."""
        with patch('ui.widgets.dashboard_widget.QPainter'):
            widget.paintEvent(MagicMock())  # ← llamada directa, no repaint()

    def test_update_data_calls_controller(self, widget, mock_controller):
        """Verifica que actualizar datos delega al controlador."""
        widget.refresh_data()
        mock_controller.get_dashboard_data.assert_called_once()  # ← OBLIGATORIO
```

### Errores comunes en esta capa
- Mockear el widget en lugar de instanciarlo → los errores de `__init__` quedan ocultos
- Usar `widget.repaint()` en lugar de `widget.paintEvent(MagicMock())` → las excepciones se tragan
- Usar `isVisible()` → siempre `False` en headless, el test siempre falla o siempre pasa
- Pasar `MagicMock()` a `insertTab()` → `TypeError` de C++

---

## Capa 5: Tests E2E

### Reglas
- Usar BD real (fixture `repos` o `temp_db_file`)
- Simular el flujo completo del usuario, no solo una función
- Verificar el estado final en la BD, no solo el retorno de la función
- Usar `@pytest.mark.e2e`

### Plantilla

```python
@pytest.mark.e2e
class TestFlujoCreacionProducto:
    """Tests E2E para el flujo completo de creación de producto."""

    def test_crear_producto_con_subfabricaciones_persiste(self, repos, session):
        """Verifica que crear un producto con subfabricaciones persiste todo correctamente."""
        from sqlalchemy import select
        from database.models import Producto

        # Act — flujo completo
        repos["product"].create_product("PROD-001", "Producto Test", 10.0)
        repos["product"].add_subfabricacion("PROD-001", "SUB-001", 2)

        # Assert — verificar en BD directamente
        stmt = select(Producto).where(Producto.codigo == "PROD-001")
        prod = session.execute(stmt).scalar_one_or_none()
        assert prod is not None
        assert len(prod.subfabricaciones) == 1
```
