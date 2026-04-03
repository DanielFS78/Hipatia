---
name: Testing — Antipatrones y Falsos Positivos
description: Catálogo de antipatrones concretos que hacen que los tests pasen aunque el código esté roto. Cada antipatrón tiene el patrón problemático, por qué engaña, y la corrección obligatoria. Léela antes de escribir o revisar cualquier test.
---

# Testing — Antipatrones y Falsos Positivos

> Esta skill documenta los errores reales que se han encontrado en este proyecto.
> Un test que pasa no significa que el código funcione. Estos patrones son la razón.

---

## ANTIPATRÓN 1: MagicMock() sin spec en clases del proyecto

**Por qué es un falso positivo**: `MagicMock()` acepta cualquier atributo y cualquier llamada. Si el código llama a `service.metodo_que_no_existe()`, el mock devuelve otro mock en lugar de lanzar `AttributeError`. El test pasa. El bug queda oculto.

```python
# ❌ FALSO POSITIVO — si BackupService no tiene create_backup(), el test pasa igual
mock_service = MagicMock()
controller.backup_service = mock_service
controller.run_backup()
mock_service.create_backup.assert_called_once()  # pasa aunque create_backup no exista

# ✅ CORRECTO — lanza AttributeError si create_backup no existe en BackupService
from unittest.mock import create_autospec
mock_service = create_autospec(BackupService, instance=True)
```

**Regla**: `MagicMock()` sin spec está PROHIBIDO para cualquier clase definida en el proyecto (Services, Repositories, Controllers, Views, Models, DTOs). Solo se permite para módulos externos (cv2, pyzbar, openpyxl) o funciones sueltas del stdlib.

---

## ANTIPATRÓN 2: @patch sin autospec=True

**Por qué es un falso positivo**: Un `@patch` sin `autospec=True` reemplaza la clase con un `MagicMock` sin spec. El código puede llamar al mock con argumentos incorrectos y el test pasa.

```python
# ❌ FALSO POSITIVO — si el código llama BackupService(arg_incorrecto), pasa igual
@patch("controllers.backup_controller.BackupService")
def test_init(self, MockBackup):
    controller = BackupController(db, view)
    MockBackup.assert_called_once()  # pasa aunque los args sean incorrectos

# ✅ CORRECTO — valida firma del constructor
@patch("controllers.backup_controller.BackupService", autospec=True)
def test_init(self, MockBackup):
    controller = BackupController(db, view)
    MockBackup.assert_called_once_with(db)  # falla si los args son incorrectos
```

**Excepción válida**: `new_callable=PropertyMock`, `new_callable=mock_open`, `new=sentinel.X`.

---

## ANTIPATRÓN 3: Test que solo verifica el retorno, no la interacción

**Por qué es un falso positivo**: Si el servicio devuelve el valor correcto pero lo hace de forma incorrecta (llamando al repositorio equivocado, con los args incorrectos, o sin llamarlo), el test pasa.

```python
# ❌ FALSO POSITIVO — no verifica que el repositorio fue llamado
def test_get_worker(self, service, mock_db):
    mock_db.worker_repo.get_worker.return_value = WorkerDTO(id=1, nombre="Ana")
    result = service.get_worker(1)
    assert isinstance(result, WorkerDTO)  # pasa aunque el servicio use el repo incorrecto

# ✅ CORRECTO — verifica retorno Y que el repositorio correcto fue llamado con los args correctos
def test_get_worker(self, service, mock_db):
    mock_db.worker_repo.get_worker.return_value = WorkerDTO(id=1, nombre="Ana")
    result = service.get_worker(1)
    assert isinstance(result, WorkerDTO)
    mock_db.worker_repo.get_worker.assert_called_once_with(1)  # ← OBLIGATORIO
```

**Regla**: Todo test de servicio o controlador DEBE tener al menos un `assert_called_*` además del assert de retorno.

---

## ANTIPATRÓN 4: Verificar solo que "no lanza excepción"

**Por qué es un falso positivo**: Si el método no hace nada (o hace algo incorrecto silenciosamente), el test pasa.

```python
# ❌ FALSO POSITIVO — pasa aunque el método esté vacío
def test_create_backup(self, controller, mock_service):
    controller.create_backup()  # no hay assert

# ❌ TAMBIÉN FALSO POSITIVO — solo verifica que no explota
def test_create_backup(self, controller, mock_service):
    try:
        controller.create_backup()
    except Exception:
        pytest.fail("No debería lanzar excepción")

# ✅ CORRECTO
def test_create_backup(self, controller, mock_service):
    controller.create_backup()
    mock_service.create_backup.assert_called_once()
    mock_service.create_backup.assert_called_once_with(destination=ANY, compress=True)
```

---

## ANTIPATRÓN 4B: `assert True` para “hacer feliz” al analizador

**Por qué es un falso positivo**: `assert True` no valida nada. Si el test solo contiene `assert True`,
el código bajo prueba puede estar roto y el test seguirá pasando.

Este patrón suele aparecer cuando se intenta “arreglar” `tests_without_assert` sin definir un
observable real (retorno, estado o interacción).

```python
# ❌ FALSO POSITIVO — no verifica nada
def test_connect_signals(self, widget):
    widget.connect_signals()
    assert True

# ✅ CORRECTO — verificar al menos un observable real
def test_connect_signals(self, widget, mock_controller):
    widget.connect_signals()
    assert widget is not None
    assert mock_controller.on_data_changed.call_count >= 1
```

**Regla**: `assert True` solo se permite como **test de humo** y debe ir justificado con
`# smoke_test: ...`. En servicios/controladores debe evitarse casi siempre.

---

## ANTIPATRÓN 5: Mock de retorno que coincide con el valor por defecto

**Por qué es un falso positivo**: Si el mock devuelve `True` por defecto y el código también devuelve `True` por defecto (sin llamar al servicio), el test pasa.

```python
# ❌ FALSO POSITIVO — MagicMock() devuelve MagicMock() que es truthy
mock_service = MagicMock()
# mock_service.create_backup() devuelve MagicMock(), que es truthy
result = controller.create_backup()
assert result  # pasa aunque el servicio no haya sido llamado

# ✅ CORRECTO — configurar el retorno explícitamente Y verificar la llamada
mock_service = create_autospec(BackupService, instance=True)
mock_service.create_backup.return_value = True
result = controller.create_backup()
assert result is True
mock_service.create_backup.assert_called_once()
```

---

## ANTIPATRÓN 6: assert_called_once() sin verificar argumentos

**Por qué es un falso positivo**: El método fue llamado, pero con los argumentos incorrectos.

```python
# ❌ INCOMPLETO — verifica que fue llamado pero no con qué args
mock_service.add_worker.assert_called_once()

# ✅ CORRECTO — verifica args exactos
mock_service.add_worker.assert_called_once_with("Ana García", tipo=2, notas="")

# ✅ TAMBIÉN CORRECTO cuando algunos args son variables
from unittest.mock import ANY
mock_service.add_worker.assert_called_once_with("Ana García", tipo=ANY, notas=ANY)
```

**Regla**: Usar `assert_called_once_with(...)` en lugar de `assert_called_once()` siempre que los argumentos sean conocidos o parcialmente conocidos.

---

## ANTIPATRÓN 7: Fixture que devuelve MagicMock anidado

**Por qué es un falso positivo**: Los atributos anidados de un `MagicMock` son también `MagicMock` sin spec. El código puede acceder a `mock.model.worker_service.metodo_inexistente()` y el test pasa.

```python
# ❌ FALSO POSITIVO — todos los atributos anidados son MagicMock sin spec
@pytest.fixture
def mock_app():
    app = MagicMock()
    app.model = MagicMock()
    app.model.worker_service = MagicMock()
    return app

# ✅ CORRECTO — cada nivel tiene spec
@pytest.fixture
def mock_app():
    from unittest.mock import create_autospec
    app = create_autospec(AppController, instance=True)
    app.model = create_autospec(AppModel, instance=True)
    app.model.worker_service = create_autospec(WorkerService, instance=True)
    return app
```

---

## ANTIPATRÓN 8: Test de repositorio con mock de sesión

**Por qué es un falso positivo**: Si mockeas la sesión de SQLAlchemy, el repositorio puede ejecutar queries incorrectas (columnas inexistentes, joins incorrectos) y el test pasa porque el mock devuelve lo que le dices.

```python
# ❌ FALSO POSITIVO — el repositorio puede tener SQL incorrecto y el test pasa
def test_get_worker(self):
    mock_session = MagicMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = WorkerDTO(id=1)
    repo = WorkerRepository(mock_session)
    result = repo.get_worker(1)
    assert isinstance(result, WorkerDTO)  # pasa aunque el SQL sea incorrecto

# ✅ CORRECTO — usar BD real en memoria (fixture repos del conftest)
def test_get_worker(self, repos):
    repos["worker"].add_worker("Ana", "", 2)
    result = repos["worker"].get_worker(1)
    assert isinstance(result, WorkerDTO)
    assert result.nombre_completo == "Ana"
```

**Regla absoluta**: Los tests de repositorio NUNCA mockean la sesión de BD. Siempre usan la fixture `repos` del conftest.

---

## ANTIPATRÓN 9: Parchear en el módulo incorrecto

**Por qué es un falso positivo**: Si parcheas `unittest.mock.MagicMock` en lugar del módulo donde se usa, el código real sigue ejecutándose con la clase original.

```python
# ❌ INCORRECTO — parchea en el módulo fuente, no donde se usa
@patch("core.services.backup_service.BackupService")
def test_controller(self, MockBackup):
    # Si backup_controller importa BackupService a nivel de módulo,
    # el import ya ocurrió antes del patch → el mock no tiene efecto
    ...

# ✅ CORRECTO — parchear donde el nombre vive en el momento de ejecución
@patch("controllers.backup_controller.BackupService", autospec=True)
def test_controller(self, MockBackup):
    ...
```

**Regla**: Si el módulo bajo prueba tiene `from X import Y` a nivel de módulo → parchear `modulo_bajo_prueba.Y`. Si el import es local dentro de un método → parchear `X.Y`.

---

## ANTIPATRÓN 10: Test E2E con mocks de DTOs

**Por qué es un falso positivo**: Los tests E2E deben probar el flujo completo. Si mockeas los DTOs, estás probando que los mocks funcionan, no que el sistema funciona.

```python
# ❌ FALSO POSITIVO en E2E — los DTOs son mocks, no objetos reales
controller = MagicMock()
controller.model = MagicMock()
machines = [MagicMock() for _ in range(3)]  # DTOs falsos
controller.model.get_all_machines.return_value = machines

# ✅ CORRECTO en E2E — usar BD real y DTOs reales
def test_flujo_completo(self, repos, session):
    repos["machine"].add_machine("CNC-01", "Mecanizado", "CNC", True)
    machines = repos["machine"].get_all_machines()
    assert len(machines) == 1
    assert isinstance(machines[0], MachineDTO)
```

---

## ANTIPATRÓN 11: `MagicMock(spec=object)` — el spec que bloquea todo

**Por qué es un error**: `spec=object` limita el mock a los atributos de `object` (básicamente nada útil). Cualquier acceso a un atributo real como `get_setting`, `engine`, `config_repo` lanza `AttributeError`. Parece "estricto" pero en realidad rompe los tests.

```python
# ❌ INCORRECTO — spec=object bloquea TODOS los atributos del proyecto
model = MagicMock(spec=object)
model.db = MagicMock(spec=object)
model.db.config_repo.get_setting.side_effect = ...  # AttributeError: Mock object has no attribute 'get_setting'

# ✅ CORRECTO — usar la clase real como spec, o MagicMock() sin spec si la clase no es importable
from database.repositories.configuration_repository import ConfigurationRepository
mock_cfg = create_autospec(ConfigurationRepository, instance=True)
mock_cfg.get_setting.side_effect = lambda k, d=None: "08:00" if k == "work_start_time" else d

# ✅ TAMBIÉN CORRECTO para objetos con muchos atributos dinámicos
model = MagicMock()  # sin spec — permite acceso libre a atributos
model.db = MagicMock()
```

**Regla**: `spec=object` nunca es útil. Si quieres un mock estricto, usa `create_autospec(ClaseReal, instance=True)`. Si no puedes importar la clase, usa `MagicMock()` sin spec.

---

## ANTIPATRÓN 12: Capturar la clase real DESPUÉS del patch

**Por qué falla**: Si haces `patch("app.configparser.ConfigParser")` y luego dentro del bloque intentas `MagicMock(spec=configparser.ConfigParser)`, en ese momento `configparser.ConfigParser` ya es el mock — y `create_autospec` / `MagicMock(spec=...)` sobre un Mock lanza `InvalidSpecError: Cannot spec a Mock object`.

```python
# ❌ INCORRECTO — configparser.ConfigParser ya es un Mock dentro del with
with patch("app.configparser.ConfigParser") as m_conf_cls:
    mock_conf = MagicMock(spec=configparser.ConfigParser)  # InvalidSpecError

# ✅ CORRECTO — capturar la clase real ANTES del patch, a nivel de módulo
import configparser
_REAL_CONFIG_PARSER = configparser.ConfigParser  # capturar aquí, fuera de cualquier patch

# ... más tarde, dentro del test:
with patch("app.configparser.ConfigParser"):
    mock_conf = MagicMock(spec=_REAL_CONFIG_PARSER)  # usa la clase real, no el mock
```

**Regla**: Si necesitas el spec de una clase que vas a parchear, captúrala en una variable a nivel de módulo del test, antes de cualquier `patch`.

---

## ANTIPATRÓN 13: `sys.exit()` mockeado sin `side_effect` no para la ejecución

**Por qué es un falso positivo**: Si parcheas `sys.exit` con un `MagicMock()` normal, las llamadas a `sys.exit(0)` o `sys.exit(1)` dentro del código no lanzan `SystemExit` — el código sigue ejecutándose. Las líneas posteriores al `sys.exit()` se ejecutan igualmente, lo que puede causar errores inesperados o que el test pase por razones incorrectas.

```python
# ❌ INCORRECTO — sys.exit() no para la ejecución, el código continúa
with patch("app.sys.exit") as m_exit:
    main()  # si main() llama sys.exit(0), el código sigue ejecutándose
    m_exit.assert_called_with(0)  # puede pasar aunque el flujo sea incorrecto

# ✅ CORRECTO — side_effect hace que sys.exit() realmente pare la ejecución
with patch("app.sys.exit") as m_exit:
    m_exit.side_effect = SystemExit(0)
    with pytest.raises(SystemExit):
        main()
```

**Cuándo NO usar side_effect**: Si el test necesita verificar que `sys.exit()` fue llamado pero el código tiene más lógica después que también quieres probar, omite el `side_effect` y verifica con `assert_called_with`. Pero en ese caso, asegúrate de que el código posterior no falle por falta de contexto.

---

## ANTIPATRÓN 14: Parchear imports locales dentro de funciones

**Por qué falla**: Si el código importa una clase dentro de una función o método (no a nivel de módulo), el nombre no existe en el namespace del módulo hasta que se ejecuta esa función. `patch("modulo.Clase")` lanza `AttributeError: module has no attribute 'Clase'`.

```python
# En app.py:
def main():
    ...
    elif not saved_mode:
        from ui.dialogs.connection_dialog import ConnectionDialog  # import LOCAL
        dialog = ConnectionDialog()

# ❌ INCORRECTO — ConnectionDialog no está en el namespace de app
with patch("app.ConnectionDialog") as m_dialog:  # AttributeError

# ✅ CORRECTO — parchear en el módulo fuente donde vive la clase
with patch("ui.dialogs.connection_dialog.ConnectionDialog") as m_dialog:
    ...
```

**Regla de diagnóstico**: Si `patch("modulo.Nombre")` lanza `AttributeError: module has no attribute 'Nombre'`, el import es local. Busca `from X.Y import Nombre` dentro de funciones/métodos y parchea `X.Y.Nombre` en su lugar.

---

## Checklist de revisión antes de hacer commit

Antes de marcar un test como "listo", verifica:

- [ ] ¿Todos los mocks de clases del proyecto usan `create_autospec` o `MagicMock(spec=ClaseReal)`?
- [ ] ¿Ningún mock usa `spec=object`?
- [ ] ¿Las clases que se van a parchear están capturadas en variables antes del patch si se usan como spec?
- [ ] ¿Todos los `@patch` tienen `autospec=True` (o `new_callable=` como excepción válida)?
- [ ] ¿Cada test de servicio/controlador tiene al menos un `assert_called_once_with(...)`?
- [ ] ¿Los tests de repositorio usan la fixture `repos` (BD real), no mocks de sesión?
- [ ] ¿Los tests E2E usan DTOs reales, no `MagicMock()`?
- [ ] ¿Los `assert_called_once()` verifican también los argumentos con `assert_called_once_with(...)`?
- [ ] ¿`sys.exit` mockeado tiene `side_effect = SystemExit(...)` si el código no debe continuar?
- [ ] ¿Los imports locales dentro de funciones se parchean en su módulo fuente, no en el módulo bajo prueba?

---

## Cómo detectar estos antipatrones en el código existente

```bash
# Buscar MagicMock() sueltos (sin spec)
grep -rn "MagicMock()" tests/ --include="*.py"

# Buscar spec=object (siempre incorrecto)
grep -rn "spec=object" tests/ --include="*.py"

# Buscar @patch sin autospec
grep -rn "@patch(" tests/ --include="*.py" | grep -v "autospec=True" | grep -v "new_callable" | grep -v "new="

# Buscar tests sin assert_called en archivos de controladores
grep -L "assert_called" tests/unit/test_*controller*.py tests/controllers/**/*.py 2>/dev/null

# Buscar tests de repositorio con mock de sesión
grep -rn "MagicMock.*session\|session.*MagicMock" tests/ --include="*.py"

# Buscar sys.exit mockeado sin side_effect
grep -rn "patch.*sys.exit" tests/ --include="*.py" | grep -v "side_effect"
```
