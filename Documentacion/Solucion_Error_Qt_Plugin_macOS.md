# Solución: Error de Qt Platform Plugin "cocoa" en macOS

> **Fecha:** 26 de Diciembre de 2025  
> **Problema:** La aplicación no se ejecutaba en macOS  
> **Estado:** ✅ Resuelto

---

## 1. Descripción del Error

Al ejecutar la aplicación con `python app.py`, aparecía el siguiente error:

```
qt.qpa.plugin: Could not find the Qt platform plugin "cocoa" in "/tmp/pyqt6_cache/plugins/platforms"
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
zsh: abort      python app.py
```

La aplicación se abortaba inmediatamente después de mostrar el mensaje de logging, sin llegar a mostrar la interfaz gráfica.

---

## 2. Causa Raíz

### 2.1 El Bug de Qt6 con Espacios en Rutas

Qt6 tiene un **bug conocido en macOS** donde no puede cargar plugins de plataforma desde rutas que contienen espacios. 

El proyecto está ubicado en:
```
/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/...
                                 ↑
                            "Mobile Documents" contiene espacio
```

Esta ruta es de iCloud Drive, que usa "Mobile Documents" como directorio base.

### 2.2 Por Qué el Fix Anterior No Funcionaba

Existía un fix en `app.py` que intentaba:
1. Copiar el directorio Qt6 a `/tmp/pyqt6_cache`
2. Establecer `QT_PLUGIN_PATH` apuntando a la copia

**El problema:** Establecer variables de entorno con `os.environ[]` en Python **no afecta a las bibliotecas nativas** que ya fueron cargadas. Cuando Python importa PyQt6, los bindings `.abi3.so` ya tienen las rutas de frameworks hardcodeadas:

```
$ otool -L QtWidgets.abi3.so
@rpath/QtWidgets.framework/Versions/A/QtWidgets
@rpath/QtGui.framework/Versions/A/QtGui
@rpath/QtCore.framework/Versions/A/QtCore
```

Estas rutas `@rpath` se resuelven relativamente a la ubicación del `.abi3.so`, que sigue estando en la ruta con espacios.

### 2.3 Prueba Clave

Usando `ctypes.CDLL()` directamente para cargar `libqcocoa.dylib` funcionaba correctamente:

```python
lib = ctypes.CDLL("/tmp/pyqt6_cache/plugins/platforms/libqcocoa.dylib")
# → SUCCESS
```

Esto demostró que el archivo en sí no estaba corrupto, sino que Qt tenía problemas internos al resolver las dependencias.

---

## 3. Proceso de Debugging

### 3.1 Diagnóstico Inicial
```bash
export QT_DEBUG_PLUGINS=1
python app.py
```

Esto reveló que Qt encontraba el directorio pero no podía cargar el plugin.

### 3.2 Análisis de Dependencias
```bash
# Ver qué frameworks necesita libqcocoa.dylib
otool -L /path/to/libqcocoa.dylib

# Ver el rpath configurado
otool -l /path/to/libqcocoa.dylib | grep -A2 "LC_RPATH"
```

Resultado: `@loader_path/../../lib` - correcto estructuralmente.

### 3.3 Análisis de Carga de Bibliotecas
```bash
export DYLD_PRINT_LIBRARIES=1
python -c "from PyQt6.QtWidgets import QApplication"
```

Esto reveló que **macOS cargaba Qt desde la ruta original con espacios**, ignorando la copia en `/tmp`.

### 3.4 Prueba de Carga Directa
Verificar que el dylib se puede cargar manualmente:

```python
import ctypes
lib = ctypes.CDLL("/tmp/pyqt6_venv/PyQt6/Qt6/plugins/platforms/libqcocoa.dylib")
# → SUCCESS - El archivo funciona
```

### 3.5 Conclusión
Las variables de entorno deben establecerse **ANTES** de iniciar Python, no durante la ejecución.

---

## 4. Solución Implementada

### 4.1 Script Wrapper: `run_app.sh`

Se creó un script bash que:
1. Detecta si la ruta contiene espacios
2. Copia PyQt6 completo a `/tmp/pyqt6_venv` (sin espacios)
3. Establece las variables de entorno **antes** de ejecutar Python
4. Ejecuta la aplicación

```bash
#!/bin/bash
# run_app.sh - Ejecutar la aplicación correctamente en macOS

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/.venv/bin/activate"

SITE_PACKAGES="$SCRIPT_DIR/.venv/lib/python3.13/site-packages"
QT6_DIR="$SITE_PACKAGES/PyQt6/Qt6"

# Si hay espacios en la ruta, usar workaround
if [[ "$SITE_PACKAGES" == *" "* ]]; then
    TMP_PYQT="/tmp/pyqt6_venv"
    if [ ! -d "$TMP_PYQT/PyQt6" ]; then
        mkdir -p "$TMP_PYQT"
        cp -R "$SITE_PACKAGES/PyQt6" "$TMP_PYQT/"
        xattr -r -d com.apple.quarantine "$TMP_PYQT/PyQt6" 2>/dev/null
    fi
    QT6_DIR="$TMP_PYQT/PyQt6/Qt6"
    export PYTHONPATH="$TMP_PYQT:$PYTHONPATH"
fi

export QT_PLUGIN_PATH="$QT6_DIR/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT6_DIR/plugins/platforms"
export DYLD_LIBRARY_PATH="$QT6_DIR/lib:$DYLD_LIBRARY_PATH"
export DYLD_FRAMEWORK_PATH="$QT6_DIR/lib:$DYLD_FRAMEWORK_PATH"

python "$SCRIPT_DIR/app.py" "$@"
```

### 4.2 Simplificación de app.py

El código de fix en `app.py` se simplificó para solo actuar si las variables no están configuradas:

```python
if sys.platform == "darwin":
    existing_qt_path = os.environ.get("QT_PLUGIN_PATH", "")
    if existing_qt_path and " " not in existing_qt_path and os.path.exists(existing_qt_path):
        pass  # Ya configurado por run_app.sh
    else:
        # Usar copia en /tmp si existe
        tmp_pyqt = "/tmp/pyqt6_venv"
        if os.path.exists(os.path.join(tmp_pyqt, "PyQt6", "Qt6", "plugins")):
            # ... configurar paths
```

---

## 5. Cómo Ejecutar la Aplicación Ahora

```bash
# En lugar de:
python app.py    # ❌ Falla

# Usar:
./run_app.sh     # ✅ Funciona
```

---

## 6. Por Qué los Tests No Detectaron Este Problema

| Tests | Aplicación Real |
|-------|-----------------|
| Usan `pytest-qt` con backend offscreen | Necesita backend `cocoa` (GUI real) |
| No cargan plugins de plataforma reales | Requiere cargar `libqcocoa.dylib` |
| Se ejecutan sin espacios en `/tmp` | Se ejecuta desde iCloud con espacios |
| Solo verifican lógica de negocio | Depende del stack completo de Qt |

### Tipos de Problemas que los Unit Tests NO Detectan:

1. **Problemas de entorno de ejecución**: Rutas, permisos, variables de entorno
2. **Bugs de bibliotecas externas**: El bug de Qt con espacios es externo al código
3. **Problemas de inicialización**: Orden de imports, configuración temprana
4. **Incompatibilidades de sistema operativo**: Comportamiento específico de macOS

### Recomendación: Tests de Smoke

Para detectar este tipo de problemas, añadir un test de integración que verifique que la aplicación puede iniciarse:

```python
def test_application_can_start():
    """Verifica que la aplicación Qt puede inicializarse."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    assert app is not None
```

---

## 7. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `run_app.sh` | **[NUEVO]** Script wrapper para ejecutar la aplicación |
| `app.py` | Simplificado el fix de Qt para no sobrescribir variables |

---

## 8. Referencias

- [Bug de Qt con espacios en paths](https://bugreports.qt.io/) - Reportes relacionados
- [Documentación de DYLD en macOS](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/)
- [PyQt6 Platform Plugins](https://www.riverbankcomputing.com/static/Docs/PyQt6/installation.html)
