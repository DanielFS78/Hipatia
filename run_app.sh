#!/bin/bash
# =============================================================================
# IMPORTANTE: Este script es necesario para ejecutar la aplicación en macOS
# cuando el proyecto está en una ruta con espacios (ej: iCloud Drive, Dropbox)
#
# Qt6 tiene un bug donde no puede cargar plugins desde rutas con espacios.
# Este script configura las variables de entorno ANTES de iniciar Python.
# =============================================================================

# Obtener el directorio donde está este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activar el entorno virtual
source "$SCRIPT_DIR/.venv/bin/activate"

# Encontrar el directorio site-packages
SITE_PACKAGES="$SCRIPT_DIR/.venv/lib/python3.13/site-packages"
QT6_DIR="$SITE_PACKAGES/PyQt6/Qt6"

# Verificar si la ruta contiene espacios
if [[ "$SITE_PACKAGES" == *" "* ]]; then
    echo "Detectada ruta con espacios, configurando workaround para Qt6..."
    
    # Crear copia de PyQt6 en /tmp si no existe
    TMP_PYQT="/tmp/pyqt6_venv"
    if [ ! -d "$TMP_PYQT/PyQt6" ]; then
        echo "Copiando PyQt6 a $TMP_PYQT (esto puede tomar unos segundos)..."
        mkdir -p "$TMP_PYQT"
        cp -R "$SITE_PACKAGES/PyQt6" "$TMP_PYQT/"
        # Remover atributos de quarantine
        xattr -r -d com.apple.quarantine "$TMP_PYQT/PyQt6" 2>/dev/null
        echo "Copia completada."
    fi
    
    QT6_DIR="$TMP_PYQT/PyQt6/Qt6"
    
    # Añadir la copia al PYTHONPATH
    export PYTHONPATH="$TMP_PYQT:$PYTHONPATH"
fi

# Configurar variables de entorno de Qt (ANTES de importar QtWidgets)
export QT_PLUGIN_PATH="$QT6_DIR/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT6_DIR/plugins/platforms"
export DYLD_LIBRARY_PATH="$QT6_DIR/lib:$DYLD_LIBRARY_PATH"
export DYLD_FRAMEWORK_PATH="$QT6_DIR/lib:$DYLD_FRAMEWORK_PATH"

# Debug (opcional, comentar para producción)
# echo "QT_PLUGIN_PATH: $QT_PLUGIN_PATH"
# echo "QT_QPA_PLATFORM_PLUGIN_PATH: $QT_QPA_PLATFORM_PLUGIN_PATH"

# Ejecutar la aplicación Python
python "$SCRIPT_DIR/app.py" "$@"
