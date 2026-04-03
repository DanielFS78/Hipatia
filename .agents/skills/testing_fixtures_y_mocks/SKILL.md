---
name: Testing — Fixtures y Mocks
description: Reglas estrictas para construir fixtures y mocks correctos en Hipatia. Cubre create_autospec, autospec=True, DummyModel, SessionKeepAliveProxy y todos los patrones que han causado falsos positivos en el proyecto.
---

# Testing — Fixtures y Mocks

> Skill especializada. Léela junto con `strict_testing` (reglas generales) y `testing_por_capa` (qué testear en cada capa).

---

## REGLA ABSOLUTA: nunca `MagicMock()` sin spec para clases del proyecto

Un `MagicMock()` sin spec acepta cualquier atributo y cualquier llamada. Si el código bajo prueba llama a un método que no existe, el test pasa igualmente. Eso es exactamente lo que ha estado pasando en este proyecto.

```python
# ❌ PROHIBIDO para clases del proyecto
mock_service = MagicMock()
mock_db = MagicMock()
mock_view = MagicMock()

# ✅ OBLIGATORIO
from unittest.mock import create_autospec
mock_service = create_autospec(BackupService, instance=True)
mock_db = create_autospec(DatabaseManager, instance=True)
mock_view = create_autospec(MainView, instance=True)
```

`create_autospec(Clase, instance=True)` es más estricto que `MagicMock(spec=Clase)` porque también valida las firmas de los métodos (número y nombre de argumentos).

---

## Cuándo usar cada patrón

| Situación | Patrón correcto |
|---|---|
| Mockear una clase del proyecto (Service, Repo, Controller, View) | `create_autospec(Clase, instance=True)` |
| Mockear una clase de PyQt6 que no se pasa a C++ | `MagicMock(spec=QWidget)` |
| Mockear una clase de PyQt6 que SÍ se pasa a C++ (insertTab, setForeground) | Objeto real `QWidget()` |
| Mockear un módulo externo (cv2, pyzbar) | `MagicMock()` sin spec (son módulos, no clases del proyecto) |
| Mockear una función suelta (os.makedirs, shutil.copy) | `@patch("modulo.funcion", autospec=True)` |
| El código llama a `self.model.__init__(arg)` | Clase `Dummy` concreta (ver abajo) |

---

## Fixtures de controladores — patrón correcto

El patrón más común en este proyecto es un controlador que recibe `app` (AppController), `model` y `view`. Así se hace correctamente:

```python
# ❌ INCORRECTO — lo que hay ahora en muchos tests
@pytest.fixture
def mock_app() -> MagicMock:
    app = MagicMock()              # loose mock
    app.model = MagicMock()        # loose mock anidado
    app.view = MagicMock()         # loose mock anidado
    return app

# ✅ CORRECTO
from unittest.mock import create_autospec
from controllers.app_controller import AppController
from core.app_model import AppModel
from ui.main_window import MainView

@pytest.fixture
def mock_app() -> AppController:
    """Mock estricto de AppController."""
    app = create_autospec(AppController, instance=True)
    app.model = create_autospec(AppModel, instance=True)
    app.view = create_autospec(MainView, instance=True)
    return app
```

Si `AppController` tiene imports locales en `__init__` que impiden instanciarlo, usa `create_autospec` igualmente — no necesita instanciar la clase real, solo lee su firma.

---

## Cuando el código llama a `__init__` del mock — usar DummyModel

Si el controlador bajo prueba ejecuta `self.model.__init__(db)` internamente (reinicialización), `MagicMock` lanza `InvalidSpecError`. La solución es una clase `Dummy` concreta:

```python
# ❌ Fallará con InvalidSpecError
@pytest.fixture
def mock_model():
    return MagicMock()

# ✅ Clase Dummy concreta
class DummyAppModel:
    """Sustituto concreto de AppModel para tests que reinicializan el modelo."""
    def __init__(self, db_manager=None):
        self.db = MagicMock()
        self.worker_service = MagicMock()
        self.product_service = MagicMock()
        self.fabricacion_service = MagicMock()
        # Añadir solo los atributos que el test realmente necesita

@pytest.fixture
def mock_model() -> DummyAppModel:
    """Modelo dummy para tests con reinicialización."""
    return DummyAppModel()
```

---

## Guardar referencias antes de reinicialización

Si el test parchea un atributo y luego el código reinicializa el objeto que lo contiene, la referencia al mock original se pierde:

```python
# ❌ Fallará — mock_db es el nuevo objeto tras __init__
controller.on_import_databases()
controller.model.db.close.assert_called_once()  # comprueba el nuevo mock, no el original

# ✅ Guardar referencia ANTES de la acción
old_db = controller.model.db
controller.on_import_databases()
old_db.close.assert_called_once()
```

---

## Patches — siempre `autospec=True`

```python
# ❌ PROHIBIDO — acepta cualquier argumento
@patch("os.makedirs")
@patch("core.services.backup_service.BackupService")

# ✅ OBLIGATORIO
@patch("os.makedirs", autospec=True)
@patch("core.services.backup_service.BackupService", autospec=True)
```

**Excepción válida**: `new_callable=PropertyMock` para propiedades, o `new=MagicMock()` cuando necesitas controlar el objeto exacto que se inyecta.

---

## Dónde parchear — la regla del namespace

La regla es parchear donde el nombre **vive en el momento de la ejecución**, no donde está definido.

```python
# Si el módulo bajo prueba tiene a nivel de módulo:
# from core.services.backup_service import BackupService
# → parchear en el módulo bajo prueba:
@patch("controllers.backup_controller.BackupService", autospec=True)

# Si el import es LOCAL dentro de __init__ o un método:
# def __init__(self): from core.di_container import DIContainer
# → parchear en el módulo fuente:
@patch("core.di_container.DIContainer", autospec=True)
```

Verificación rápida: si `patch("mi_modulo.Clase")` lanza `AttributeError`, el import es local → parchear en el módulo fuente.

---

## Fixtures de base de datos — usar las del conftest

No crear fixtures de BD propias en archivos de test. Usar las del `conftest.py`:

```python
# ✅ Fixtures disponibles en conftest.py
def test_algo(self, repos, session):
    # repos["worker"]  → WorkerRepository con BD en memoria
    # repos["machine"] → MachineRepository con BD en memoria
    # session          → SQLAlchemy Session activa
    ...
```

Si necesitas una BD temporal en archivo (para tests de persistencia de fichero):
```python
def test_algo(self, temp_db_file):
    # temp_db_file → ruta a archivo .db temporal, se limpia automáticamente
    ...
```

---

## Fixtures de UI — usar `qtbot` y objetos reales donde sea posible

```python
@pytest.fixture
def dialog(qtbot, mock_backup_service):
    """Instancia real del diálogo con dependencias mockeadas."""
    with patch.object(BackupRestoreDialog, 'load_backups'):  # evitar I/O en __init__
        d = BackupRestoreDialog(backup_service=mock_backup_service)
        qtbot.addWidget(d)
        return d
```

Regla: instanciar el widget real siempre que sea posible. Solo mockear sus dependencias (servicios, repos), no el widget en sí. Esto captura errores de `__init__` que los mocks ocultan.

---

## Tests de humo y `assert True`

Evitar `assert True` como sustituto de asserts reales. Antes de usarlo, intentar siempre:
- `assert widget is not None`
- `assert not widget.isHidden()` (headless) en vez de `isVisible()`
- `assert mock_colaborador.call_count == N` / `assert_called_once_with(...)`
- `assert result is ...` cuando exista retorno

`assert True` solo se permite cuando no existe un observable razonable sin acoplar el test (por ejemplo, UI headless con side effects difíciles de observar). Debe llevar comentario:

```python
assert True  # smoke_test: sin observable mejor (verificación de no-excepción)
```

---

## Fixtures con `autouse` — nombres únicos

Si una clase de test define un fixture `autouse=True`, dale un nombre que no colisione con fixtures del conftest:

```python
# ❌ Puede colisionar con fixture global "controller"
@pytest.fixture(autouse=True)
def setup(self, controller):
    self.ctrl = controller

# ✅ Nombre único de clase
@pytest.fixture(autouse=True)
def setup_worker_ctrl(self, controller):
    """Configura estado específico para esta clase de tests."""
    self.ctrl = controller
    self.ctrl.some_state = True
```

---

## Capturar clases reales antes del patch — patrón obligatorio

Si necesitas usar una clase como `spec` en un mock, pero esa misma clase va a ser parcheada en el test, captúrala a nivel de módulo antes de cualquier `patch`. En el momento en que el `patch` está activo, la clase ya es un Mock y `MagicMock(spec=esa_clase)` lanza `InvalidSpecError`.

```python
# A nivel de módulo del archivo de test — ANTES de cualquier fixture o test
import configparser
_REAL_CONFIG_PARSER = configparser.ConfigParser  # capturar aquí

# Dentro del fixture o test:
with patch("app.configparser.ConfigParser"):
    # ❌ INCORRECTO — en este punto configparser.ConfigParser ya es un Mock
    mock_conf = MagicMock(spec=configparser.ConfigParser)  # InvalidSpecError

    # ✅ CORRECTO — usa la referencia capturada antes del patch
    mock_conf = MagicMock(spec=_REAL_CONFIG_PARSER)
```

Aplica a cualquier clase que se parchee y también se use como spec: `DatabaseManager`, `ScheduleConfig`, `AppController`, etc.

---

## `spec=object` — nunca es útil, siempre rompe

`MagicMock(spec=object)` limita el mock a los atributos de `object` (solo `__class__`, `__doc__`, etc.). Cualquier acceso a atributos reales del proyecto lanza `AttributeError`. No aporta ninguna restricción útil.

```python
# ❌ SIEMPRE INCORRECTO
model = MagicMock(spec=object)
model.db.config_repo.get_setting(...)  # AttributeError

# ✅ Si tienes la clase, úsala como spec
from core.app_model import AppModel
model = create_autospec(AppModel, instance=True)

# ✅ Si no puedes importar la clase (dependencias circulares, etc.)
model = MagicMock()  # sin spec — permite acceso libre
```

---

## `sys.exit` mockeado — siempre con `side_effect`

Cuando el código bajo prueba llama a `sys.exit()`, si está mockeado sin `side_effect`, la ejecución continúa. Las líneas posteriores al `sys.exit()` se ejecutan igualmente, causando errores inesperados o falsos positivos.

```python
# ❌ INCORRECTO — el código continúa después del sys.exit() mockeado
with patch("app.sys.exit") as m_exit:
    main()  # si main() llama sys.exit(1), el código sigue ejecutándose

# ✅ CORRECTO — side_effect hace que sys.exit() realmente detenga la ejecución
with patch("app.sys.exit") as m_exit:
    m_exit.side_effect = SystemExit(1)
    with pytest.raises(SystemExit):
        main()
```

Si el test necesita verificar múltiples llamadas a `sys.exit()` con distintos códigos, configura `side_effect` como lista:

```python
m_exit.side_effect = [None, SystemExit(0)]  # primera llamada pasa, segunda para
```
