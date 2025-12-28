# Limpieza y Actualización del Proyecto - Diciembre 2025

## Resumen Ejecutivo

Este documento describe el proceso de limpieza y modernización del proyecto "Sistema de Cálculo de Tiempos de Fabricación", que originalmente fue desarrollado en Windows y posteriormente migrado a macOS.

---

## 1. Análisis Inicial del Proyecto

### 1.1 Metodología de Análisis

Para identificar exhaustivamente todas las tecnologías utilizadas en el proyecto, se realizó:

1. **Exploración de estructura de directorios** - Listado de todos los archivos y carpetas del proyecto
2. **Análisis de archivos de configuración** - Revisión de los 3 archivos `requirements*.txt` existentes
3. **Búsqueda de imports en código fuente** - Grep en todos los archivos `.py` para identificar librerías importadas
4. **Revisión del archivo principal `app.py`** - Análisis de los primeros 800 líneas donde se concentran los imports
5. **Análisis de archivos de build** - Revisión de `fabricacion.spec` y `compilar_nuevo.ps1`

### 1.2 Tecnologías Identificadas

| Categoría | Librerías | Uso |
|-----------|-----------|-----|
| **UI Framework** | PyQt6, PyQt6-Charts | Interfaz gráfica de usuario |
| **Base de Datos** | SQLAlchemy, sqlite3 | ORM y persistencia |
| **Procesamiento de Datos** | pandas, openpyxl | Análisis y manejo de Excel |
| **Imágenes/QR** | Pillow, opencv-python, qrcode | Cámaras, procesamiento de imagen, códigos QR |
| **Documentos** | python-docx, reportlab, jinja2, weasyprint | Generación de Word, PDF, plantillas |
| **Utilidades** | requests, concurrent-log-handler, graphviz | HTTP, logging, visualizaciones |
| **Testing** | pytest, pytest-qt, pytest-cov, pytest-mock | Framework de testing |
| **Calidad** | pylint, bandit, flake8, coverage | Análisis estático de código |

### 1.3 Archivos Windows Identificados

| Archivo | Tipo | Propósito |
|---------|------|-----------|
| `compilar_nuevo.ps1` | PowerShell | Script de compilación automatizado para Windows |
| `fabricacion.spec` | PyInstaller | Configuración para generar el .exe de Windows |
| `file_version_info.txt` | Metadatos | Información de versión embebida en el .exe |
| `build/` | Directorio | Archivos intermedios de compilación PyInstaller |
| `dist/` | Directorio | Ejecutable Windows compilado y sus dependencias |

### 1.4 Estado de los Requirements

Se encontraron **3 archivos de requirements redundantes**:

1. **`requirements.txt`** (25 líneas) - Dependencias principales mezcladas con testing
2. **`requirements_new.txt`** (58 líneas) - Plan para migración a PostgreSQL (nunca implementado)
3. **`requirements-test.txt`** (19 líneas) - Dependencias específicas de testing

**Problema identificado:** Duplicación, inconsistencia de versiones y dependencias no utilizadas (PostgreSQL).

---

## 2. Decisiones de Diseño

### 2.1 Eliminación de Archivos Windows

**Decisión:** Eliminar todos los archivos específicos de Windows.

**Justificación:**
- El proyecto ahora se desarrolla exclusivamente en macOS
- Los archivos .exe generados son específicos de Windows y no funcionan en Mac
- El script PowerShell no es ejecutable en macOS
- El archivo .spec contiene rutas y configuraciones específicas de Windows
- Las carpetas `build/` y `dist/` ocupaban ~1083 archivos innecesarios

**Riesgo considerado:** Si en el futuro se necesita volver a compilar para Windows, se deberá recrear el archivo `.spec`. Sin embargo, esto es preferible a mantener archivos desactualizados que pueden causar confusión.

### 2.2 Consolidación de Requirements

**Decisión:** Unificar todo en un único `requirements.txt`.

**Justificación:**
- Simplifica el mantenimiento del proyecto
- Evita inconsistencias entre archivos
- El archivo `requirements_new.txt` contenía dependencias de PostgreSQL (psycopg2, alembic, pydantic) que **nunca se implementaron** - el proyecto sigue usando SQLite
- Las dependencias de testing deben estar junto a las de producción para facilitar la configuración del entorno de desarrollo

### 2.3 Estrategia de Versionado

**Decisión:** Usar versiones mínimas (`>=`) en lugar de versiones exactas (`==`).

**Justificación:**
- Permite actualizaciones automáticas de seguridad
- Reduce conflictos de dependencias
- Las versiones especificadas son las últimas estables verificadas
- El proyecto no tiene requisitos de reproducibilidad exacta que justifiquen fijar versiones

---

## 3. Proceso de Ejecución

### 3.1 Fase 1: Limpieza de Archivos Windows

```bash
# Eliminar archivos individuales
rm -f compilar_nuevo.ps1 fabricacion.spec file_version_info.txt

# Eliminar carpetas de build
rm -rf build/ dist/
```

**Resultado:** ~1083 archivos eliminados, proyecto significativamente más limpio.

### 3.2 Fase 2: Investigación de Versiones

Se consultaron las páginas oficiales de PyPI para cada librería:

| Librería | Versión Anterior | Versión Nueva |
|----------|------------------|---------------|
| PyQt6 | >=6.4.0 | >=6.10.1 |
| PyQt6-Charts | >=6.4.0 | >=6.10.0 |
| pandas | >=1.5.0 | >=2.2.3 |
| SQLAlchemy | >=2.0.0 | >=2.0.45 |
| opencv-python | >=4.8.0 | >=4.12.0.88 |
| Pillow | >=9.0.0 | >=12.0.0 |
| pytest | >=7.4.0 | >=8.4.2 |
| reportlab | (no especificado) | >=4.4.7 |

**Nota:** Durante la instalación se detectó que PyQt6-Charts 6.10.1 no existe; la versión máxima disponible es 6.10.0. Se corrigió automáticamente.

### 3.3 Fase 3: Creación del Requirements Unificado

Se creó un nuevo `requirements.txt` organizado por categorías:

1. Framework UI Principal
2. Base de Datos y ORM
3. Procesamiento de Datos
4. Procesamiento de Imágenes y QR
5. Generación de Documentos
6. Utilidades
7. Testing y Cobertura
8. Análisis de Código

### 3.4 Fase 4: Instalación y Verificación

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias actualizadas
pip install -r requirements.txt --upgrade

# Verificar imports
python -c "from PyQt6.QtWidgets import QApplication; ..."
```

**Resultado de verificación:**
```
✅ Todos los imports principales funcionan correctamente
  - PyQt6: OK
  - PyQt6-Charts: OK
  - pandas: 2.3.3
  - SQLAlchemy: 2.0.45
  - opencv: 4.12.0
  - Pillow: OK
  - qrcode: OK
  - python-docx: OK
  - reportlab: OK
  - pytest: OK
```

---

## 4. Problemas Encontrados y Soluciones

### 4.1 PyQt6-Charts Versión Inexistente

**Problema:** Se especificó PyQt6-Charts>=6.10.1, pero la versión máxima en PyPI es 6.10.0.

**Causa:** Las búsquedas web indicaron que PyQt6 estaba en 6.10.1, se asumió erróneamente que Charts tendría la misma versión.

**Solución:** Corregir a >=6.10.0

### 4.2 WeasyPrint Requiere Dependencias de Sistema

**Problema:** WeasyPrint falla al importar porque necesita `libgobject-2.0` (parte de GTK/Pango).

**Causa:** WeasyPrint usa bibliotecas C del sistema para renderizar HTML a PDF.

**Solución:** El usuario debe instalar las dependencias del sistema:
```bash
brew install pango
```

---

## 5. Estado Final del Proyecto

### Archivos Eliminados
- `compilar_nuevo.ps1`
- `fabricacion.spec`
- `file_version_info.txt`
- `build/` (carpeta completa)
- `dist/` (carpeta completa)
- `requirements_new.txt`
- `requirements-test.txt`

### Archivo Modificado
- `requirements.txt` - Ahora contiene 22 librerías con versiones actualizadas

### Acción Pendiente del Usuario
```bash
brew install pango
```

---

## 6. Recomendaciones Futuras

1. **Mantener actualizado el requirements.txt** - Revisar versiones periódicamente
2. **Considerar usar `pip-tools`** - Para gestión más robusta de dependencias
3. **Documentar dependencias de sistema** - Como pango para weasyprint
4. **Crear Makefile o script bash** - Para automatizar tareas comunes en Mac (equivalente al antiguo .ps1)

---

*Documento generado el 25 de diciembre de 2025*
