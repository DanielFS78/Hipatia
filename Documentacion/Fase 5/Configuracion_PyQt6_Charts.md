# Configuración de PyQt6-Charts - Documentación

**Fecha:** 30 de Diciembre de 2025  
**Objetivo:** Instalar, configurar y documentar PyQt6-Charts para el módulo de Reportes

---

## 1. Estado Inicial

**Verificación de instalación:**
```bash
pip3 show PyQt6-Charts
# Resultado: NOT_INSTALLED
```

---

## 2. Investigación

### Fuentes Consultadas
| Fuente | URL |
|--------|-----|
| PyPI (versiones) | https://pypi.org/project/PyQt6-Charts/ |
| Riverbank Computing | https://www.riverbankcomputing.com/software/pyqtchart/ |
| Qt Documentation | https://doc.qt.io/qt-6/qtcharts-index.html |
| Qt Charts Overview | https://doc.qt.io/qt-6/qtcharts-overview.html |

### Versión Identificada
- **Última versión estable:** 6.10.0
- **Fecha de lanzamiento:** 22 de Octubre de 2025
- **Desarrollador:** Riverbank Computing (PyQt) + The Qt Company (Qt)

### Nota de Deprecación
> Qt Charts ha sido **deprecado desde Qt 6.10**. Se recomienda usar Qt Graphs para nuevos proyectos. Sin embargo, Qt Charts sigue siendo funcional y es la opción establecida para proyectos existentes.

---

## 3. Instalación

### Comando ejecutado
```bash
pip3 install PyQt6-Charts==6.10.0
```

### Resultado
```
Successfully installed PyQt6-Charts-6.10.0 PyQt6-Charts-Qt6-6.10.1
```

### Verificación post-instalación
```bash
pip3 show PyQt6-Charts | grep -E "Version|Location"
# Version: 6.10.0
# Location: /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages
```

---

## 4. Documentación Guardada

### Ubicación
```
Documentacion/PyQt6-Charts/
└── Qt_Charts_Reference.md
```

### Contenido del archivo de referencia
- Componentes principales (QChart, QChartView)
- Tipos de series (Line, Bar, Pie, Scatter, Area)
- Tipos de ejes (Value, BarCategory, DateTime, Logarithmic)
- Ejemplos de código para cada tipo de gráfica
- Temas disponibles
- Opciones de interacción (zoom, scroll, eventos)
- Buenas prácticas de implementación

---

## 5. Verificación de Funcionamiento

### Test de importación
```python
from PyQt6.QtCharts import (
    QChart, QChartView, 
    QLineSeries, QBarSeries, QPieSeries,
    QValueAxis, QBarCategoryAxis
)
print('✓ PyQt6-Charts 6.10.0 imports working correctly')
```

**Resultado:** ✅ Todas las importaciones funcionan correctamente

---

## 6. Clases Principales Disponibles

### Series
| Clase | Propósito |
|-------|-----------|
| `QLineSeries` | Gráficas de línea |
| `QSplineSeries` | Líneas suavizadas |
| `QBarSeries` | Gráficas de barras |
| `QBarSet` | Conjunto de datos para barras |
| `QPieSeries` | Gráficas circulares (pastel) |
| `QScatterSeries` | Gráficas de dispersión |
| `QAreaSeries` | Gráficas de área |

### Ejes
| Clase | Propósito |
|-------|-----------|
| `QValueAxis` | Valores numéricos |
| `QBarCategoryAxis` | Etiquetas categóricas |
| `QDateTimeAxis` | Fechas y horas |
| `QLogValueAxis` | Escala logarítmica |

### Contenedores
| Clase | Propósito |
|-------|-----------|
| `QChart` | Contenedor de series y ejes |
| `QChartView` | Widget para mostrar QChart |

---

## 7. Recomendaciones del Desarrollador

1. **Usar QChartView** para integrar gráficas en widgets PyQt
2. **Habilitar antialiasing** para bordes suaves: `setRenderHint(QPainter.RenderHint.Antialiasing)`
3. **Configurar ejes explícitamente** en lugar de usar `createDefaultAxes()`
4. **Usar animaciones moderadamente** (`QChart.AnimationOption.SeriesAnimations`)
5. **Manejar importación condicional** para entornos sin Charts instalado

---

## 8. Actualización del Proyecto

### Cambios en charts_container.py
Las gráficas ahora funcionarán correctamente con PyQt6-Charts instalado:
- Evolución temporal → `QLineSeries`
- Tiempos por trabajador → `QBarSeries`
- Incidencias → `QPieSeries`

### Requirements.txt (si aplica)
```
PyQt6>=6.10.0
PyQt6-Charts>=6.10.0
```

---

## 9. Próximos Pasos

- [x] Instalar PyQt6-Charts 6.10.0
- [x] Descargar documentación oficial
- [x] Guardar referencia en proyecto
- [ ] Probar manualmente las gráficas con datos reales
- [ ] Considerar migración a Qt Graphs en futuras versiones
