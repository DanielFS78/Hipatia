#!/bin/bash
# =============================================================================
# Helper script to run tests with the correct environment (Qt workaround for macOS)
# =============================================================================

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtualenv
source "$SCRIPT_DIR/.venv/bin/activate"

# Reuse Qt environment setup from run_app.sh if needed
# (Copying logic here to ensure tests run in same env as app)
SITE_PACKAGES="$SCRIPT_DIR/.venv/lib/python3.13/site-packages"
QT6_DIR="$SITE_PACKAGES/PyQt6/Qt6"

if [[ "$SITE_PACKAGES" == *" "* ]]; then
    # Create copy of PyQt6 in /tmp if it doesn't exist
    TMP_PYQT="/tmp/pyqt6_venv"
    if [ ! -d "$TMP_PYQT/PyQt6" ]; then
        echo "Configuring PyQt6 workaround for tests..."
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

echo "Running tests with pytest..."
# Pass arguments to pytest (e.g., ./run_tests.sh -v tests/unit)
python -m pytest "$@"
