---
name: Testing PyQt6 Headless
description: Guía completa para testear widgets PyQt6 en entorno headless (macOS, CI sin display). Cubre todos los problemas conocidos del proyecto Hipatia con QBrush, QPainter, QTabWidget, QShowEvent, isVisible y validación de tipos C++.
---

# Testing PyQt6 Headless

> Skill especializada. Léela cuando vayas a escribir o corregir tests de UI.
> Todos los problemas documentados aquí han ocurrido realmente en este proyecto.

---

## Configuración base (ya está en pytest.ini)

```ini
[pytest]
env =
    QT_QPA_PLATFORM=offscreen
```

Esto es lo que permite que los tests de UI corran sin pantalla. No lo cambies.

---

## Problema 1: QBrush, QColor, QPainter causan SIGABRT

**Por qué ocurre**: Estas clases requieren un contexto gráfico real. En headless, instanciarlas directamente mata el proceso con SIGABRT.

**Solución**: Parchear a nivel de módulo, justo donde se importan en el widget bajo prueba. Nunca usar `spec=QPainter` (causa `InvalidSpecError`).

```python
# ✅ CORRECTO — parchear en el módulo del widget
@patch('ui.widgets.gantt_widget.QPen')
@patch('ui.widgets.gantt_widget.QColor')
@patch('ui.widgets.gantt_widget.QPainter')
def test_paint_event(self, MockPainter, MockColor, MockPen, widget):
    widget.paintEvent(MagicMock())  # llamada directa

# ❌ INCORRECTO — spec en QPainter causa InvalidSpecError
@patch('ui.widgets.gantt_widget.QPainter', spec=QPainter)
```

Si el widget usa `QBrush` en un método que recibe un `QListWidgetItem`, también hay que parchear el método receptor:

```python
with patch("ui.dialogs.mi_dialog.QBrush", return_value=MagicMock()), \
     patch("ui.dialogs.mi_dialog.QColor", return_value=MagicMock()), \
     patch("PyQt6.QtWidgets.QListWidgetItem.setForeground"), \
     patch("PyQt6.QtWidgets.QListWidgetItem.setFont"):
    yield
```

---

## Problema 2: `paintEvent` vs `repaint()`

**Por qué ocurre**: `widget.repaint()` encola el evento en el event loop de Qt. Si `paintEvent` lanza una excepción, el event loop la traga silenciosamente y el test pasa.

**Solución**: Llamar `paintEvent` directamente.

```python
# ❌ INCORRECTO — las excepciones se tragan
widget.repaint()
widget.update()

# ✅ CORRECTO — las excepciones se propagan al test
widget.paintEvent(MagicMock())
```

---

## Problema 3: `isVisible()` siempre retorna `False` en headless

**Por qué ocurre**: `isVisible()` requiere que la ventana esté mapeada en el sistema de ventanas. En offscreen, nunca lo está.

**Solución**: Usar `isHidden()` que evalúa solo el estado interno del widget.

```python
# ❌ INCORRECTO — siempre False en headless, el assert siempre falla
assert widget.progress_bar.isVisible()

# ✅ CORRECTO
assert not widget.progress_bar.isHidden()

# ✅ TAMBIÉN CORRECTO para verificar que algo está oculto
assert widget.error_label.isHidden()
```

---

## Problema 4: `QTabWidget.insertTab()` requiere `QWidget` real

**Por qué ocurre**: `insertTab()` valida el tipo del widget a nivel de C++. Un `MagicMock()` no pasa la validación aunque tenga `spec=QWidget`.

**Solución**: Usar `QWidget()` real como `return_value` del mock, y añadir los métodos extra que necesites:

```python
# ❌ INCORRECTO — TypeError: arguments did not match any overloaded call
MockChartView.return_value = MagicMock()

# ✅ CORRECTO
mock_view = QWidget()
mock_view.setRenderHint = MagicMock()  # añadir métodos extra que el código llama
MockChartView.return_value = mock_view
```

---

## Problema 5: `QShowEvent` y `eventFilter` requieren objetos reales

**Por qué ocurre**: Los métodos que reciben eventos Qt validan el tipo a nivel de C++.

```python
# ❌ INCORRECTO — TypeError en C++
widget.showEvent(MagicMock())
effect.eventFilter(MagicMock(), MagicMock())

# ✅ CORRECTO
from PyQt6.QtGui import QShowEvent
from PyQt6.QtCore import QEvent

widget.showEvent(QShowEvent())
event = QEvent(QEvent.Type.Timer)
canvas = QWidget()
card = QWidget(canvas)  # parent real, no Mock
assert effect.eventFilter(card, event) is False
```

---

## Problema 6: Constructores `super().__init__(parent)` con Mock como parent

**Por qué ocurre**: El constructor de `QWidget` valida que `parent` sea `QWidget | None` a nivel de C++.

```python
# ❌ INCORRECTO — TypeError en C++
widget = MiWidget(parent=MagicMock())

# ✅ CORRECTO
parent = QWidget()
widget = MiWidget(parent=parent)
parent.deleteLater()  # limpieza
```

---

## Problema 7: Flags internos para cubrir ramas en `showEvent`

Si el widget tiene condiciones internas (como `_pending_signal_connection`), hay que establecerlas antes de llamar al evento para cubrir todas las ramas:

```python
# Cubrir rama "conexión pendiente"
widget._pending_signal_connection = True
widget.showEvent(QShowEvent())
assert mock_controller._connect_signals.called

# Cubrir rama "sin conexión pendiente"
widget._pending_signal_connection = False
widget.showEvent(QShowEvent())
assert not mock_controller._connect_signals.called
```

---

## Problema 8: `InvalidSpecError` con mocks de clases gráficas anidadas

Si pasas un mock con `spec` como argumento a otro mock con `spec` de clase gráfica (ej: `QBrush(QColor())`), PyQt6 lanza `InvalidSpecError`.

**Solución**: No usar `spec=` en mocks de clases gráficas que se pasan como argumentos a otras clases gráficas. Usar `MagicMock()` sin spec o `return_value=MagicMock()`.

```python
# ❌ INCORRECTO
mock_color = MagicMock(spec=QColor)
mock_brush = MagicMock(spec=QBrush)
mock_brush(mock_color)  # InvalidSpecError

# ✅ CORRECTO
with patch('ui.widgets.mi_widget.QColor', return_value=MagicMock()), \
     patch('ui.widgets.mi_widget.QBrush', return_value=MagicMock()):
    ...
```

---

## Plantilla completa para test de widget con renderizado custom

```python
"""Tests unitarios para GanttWidget."""
import pytest
from unittest.mock import MagicMock, patch, create_autospec
from PyQt6.QtWidgets import QWidget
from ui.widgets.gantt_widget import GanttWidget
from controllers.app_controller import AppController


@pytest.mark.unit
class TestGanttWidget:
    """Tests unitarios para GanttWidget en entorno headless."""

    @pytest.fixture
    def mock_controller(self):
        """Mock estricto del controlador."""
        return create_autospec(AppController, instance=True)

    @pytest.fixture
    def widget(self, qtbot, mock_controller):
        """GanttWidget real con gráficos parcheados."""
        with patch('ui.widgets.gantt_widget.QPainter'), \
             patch('ui.widgets.gantt_widget.QColor'), \
             patch('ui.widgets.gantt_widget.QPen'):
            w = GanttWidget(controller=mock_controller)
            qtbot.addWidget(w)
            return w

    def test_init_no_crash(self, widget):
        """Verifica que el widget se inicializa sin errores."""
        assert widget is not None
        assert not widget.isHidden()  # isHidden(), no isVisible()

    def test_paint_event_no_crash(self, widget):
        """Verifica que paintEvent no lanza excepciones."""
        with patch('ui.widgets.gantt_widget.QPainter'), \
             patch('ui.widgets.gantt_widget.QColor'), \
             patch('ui.widgets.gantt_widget.QPen'):
            widget.paintEvent(MagicMock())  # directo, no repaint()

    def test_show_event_connects_signals(self, widget, mock_controller):
        """Verifica que showEvent conecta las señales."""
        from PyQt6.QtGui import QShowEvent
        widget._pending_signal_connection = True
        widget.showEvent(QShowEvent())
        mock_controller.connect_gantt_signals.assert_called_once()

    def test_load_data_calls_controller(self, widget, mock_controller):
        """Verifica que cargar datos delega al controlador."""
        widget.load_data()
        mock_controller.get_gantt_data.assert_called_once()
```

---

## Checklist antes de escribir un test de UI

- [ ] ¿Estoy instanciando el widget real (no mockeándolo)?
- [ ] ¿He parcheado QPainter/QColor/QBrush a nivel del módulo del widget?
- [ ] ¿Uso `paintEvent(MagicMock())` en lugar de `repaint()`?
- [ ] ¿Uso `isHidden()` en lugar de `isVisible()`?
- [ ] ¿Los `QChartView` / widgets insertados en tabs son `QWidget()` reales?
- [ ] ¿Los eventos Qt (`QShowEvent`, `QEvent`) son objetos reales?
- [ ] ¿He verificado interacciones con `assert_called_*` en al menos un test?
- [ ] ¿He añadido `qtbot.addWidget(widget)` para limpieza automática?

---

## Problema 9: Segfault al ejecutar muchos tests Qt en el mismo proceso

**Por qué ocurre**: Al ejecutar 2000+ tests Qt en el mismo proceso, el runtime C++ de PyQt6
acumula objetos gráficos y el proceso muere con `zsh: abort` / `Fatal Python error: Aborted`.

**Síntoma**: La suite se ejecuta parcialmente y luego muere silenciosamente sin output de error.

**Solución**: Ejecutar cada archivo de test en un subproceso aislado.

```python
# Patrón usado en run_tests.py y run_tests_safe.py
env = os.environ.copy()
env["QT_QPA_PLATFORM"] = "offscreen"

result = subprocess.run(
    [sys.executable, "-m", "pytest", str(test_file), "--timeout=30", "-q"],
    capture_output=True, text=True, env=env, timeout=120
)
```

**Regla**: Nunca ejecutar `pytest tests/` completo en un solo proceso si hay widgets Qt.
Usar siempre `python3 run_tests_safe.py` o `python3 run_tests.py`.

---

## Problema 10: Importaciones locales dentro de funciones no se parchean con `patch()`

**Por qué ocurre**: Si el código bajo prueba hace `from modulo import Clase` dentro de una función,
el `patch("modulo.Clase")` no intercepta esa importación porque ya ocurrió antes.

**Ejemplo real** (`app.main()` importa `StartupScreen` localmente):
```python
# En app.py
def main():
    from ui.startup_screen import StartupScreen  # importación local
    startup = StartupScreen(db_manager)
```

**Solución**: Inyectar el mock directamente en `sys.modules` antes de llamar a la función:

```python
import sys

mock_module = MagicMock()
mock_module.StartupScreen.return_value = mock_startup_inst
original = sys.modules.get("ui.startup_screen")
sys.modules["ui.startup_screen"] = mock_module

try:
    main()  # ahora usa el mock
finally:
    if original is not None:
        sys.modules["ui.startup_screen"] = original
    else:
        sys.modules.pop("ui.startup_screen", None)
```
