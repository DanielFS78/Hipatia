#!/bin/bash

# Script para descargar e instalar Python 3.14.2 (Última versión estable a Diciembre 2025)
# Este script descarga el instalador oficial de macOS (universal 2 installer) y lo ejecuta.

PYTHON_VERSION="3.14.2"
DOWNLOAD_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
OUTPUT_FILE="python-${PYTHON_VERSION}-macos11.pkg"

echo "================================================="
echo "  Descargando Python ${PYTHON_VERSION} para macOS"
echo "================================================="

if [ -f "$OUTPUT_FILE" ]; then
    echo "El archivo $OUTPUT_FILE ya existe. Saltando descarga."
else
    echo "Descargando desde: $DOWNLOAD_URL"
    curl -O "$DOWNLOAD_URL"
    
    if [ $? -eq 0 ]; then
        echo "✅ Descarga completada exitosamente."
    else
        echo "❌ Error en la descarga."
        exit 1
    fi
fi

echo ""
echo "================================================="
echo "  Instalando Python ${PYTHON_VERSION}..."
echo "================================================="
echo "Nota: Se requerirá su contraseña de administrador para la instalación."
echo ""

# Ejecutar el instalador
sudo installer -pkg "$OUTPUT_FILE" -target /

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Instalación completada exitosamente."
    echo "Verificando versión..."
    python3.14 --version
else
    echo ""
    echo "❌ Error durante la instalación."
    exit 1
fi

echo ""
echo "================================================="
echo "  Configuración Post-Instalación Sugerida"
echo "================================================="
echo "1. Actualizar certificados SSL:"
echo "   /Applications/Python\ 3.14/Install\ Certificates.command"
echo ""
echo "2. Verificar pip:"
echo "   python3.14 -m pip --version"
echo ""
echo "3. (Opcional) Crear un nuevo entorno virtual para el proyecto:"
echo "   python3.14 -m venv .venv_new"
echo "   source .venv_new/bin/activate"
echo "   pip install -r requirements.txt"
