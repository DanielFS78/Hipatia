---
name: Troubleshooting y Prevención de Congelamientos UI (PyQt6 en macOS)
description: Guía crítica para evitar y solucionar bloqueos totales (UI freezes) causados por el motor de diseño de PyQt6 en macOS Apple Silicon. Detalla bucles infinitos por WordWrap, Stretch en pestañas ocultas y necesidad de QScrollArea.
---

# Prevención de Congelamientos UI (PyQt6 en macOS M1/M2/M3)

Este documento contiene las reglas obligatorias e histórico de soluciones para los **bloqueos totales de interfaz (Infinite Layout Loops)** que plagan el desarrollo de este proyecto en macOS.

Cuando la aplicación "se congela", "cambia de resolución repentinamente" o "los clics del ratón no responden" al cambiar de pestaña, la causa principal suele ser una cascada de redimensionamientos en el hilo principal (`resizeEvent`). 

Sigue estrictamente estas 3 reglas de diseño al crear o modificar componentes de UI en este proyecto:

## 1. Prohibido usar `setWordWrap(True)` en contenedores dinámicos
**El Problema:** 
Si un `QLabel` con auto-desbordamiento se inserta en un Layout que cambia de tamaño (por ejemplo, dentro de una página controlada por un Sidebar o un contenedor dinámico), macOS entra en un bucle ciego: 
1. El texto baja a una segunda línea, pidiendo más alto. 
2. La ventana crece en alto y compensa ensanchándose. 
3. Al ensancharse, el texto cabe en una sola línea, pidiendo menos alto. 
4. La ventana se encoje y el ciclo se repite miles de veces por segundo, bloqueando e inutilizando la app.

**Regla de Oro:**
- **NUNCA** uses `setWordWrap(True)` en etiquetas informativas o contenedores dentro de `MachinesWidget`, `SettingsWidget` o componentes similares apilados en el `QStackedWidget` principal, a menos que su padre tenga un tamaño métrico fijo estricto (ej. un ancho estático `setFixedWidth`).

## 2. Prohibido usar `Stretch` en widgets ocultos
**El Problema:**
Usar `QHeaderView.ResizeMode.Stretch` en una tabla (`QTableWidget` o `QTreeView`) que se instancia en modo "Hidden" (por ejemplo, en pestañas en segundo plano de un `QTabWidget` o vistas que aún no se muestran) causa colisiones drásticas en macOS. Tratar de calcular un 100% de estiramiento sobre un frame con ancho temporal de `0px` o de estado colapsado puede llevar a desbordamientos del layout.

**Regla de Oro:**
- En vez de `ResizeMode.Stretch` en tablas anidadas o no visibles inicialmente (como en `WorkerActivityPanel`), asigna siempre una dimensión en píxeles fijos utilizando `setColumnWidth(indice, ancho)` o `ResizeToContents`.

## 3. Interfaces muy altas obligan el uso de `QScrollArea`
**El Problema a Erradicar:**
Si un widget tiene múltiples filas, frames y calendarios apilados (ej: `SettingsWidget`) su exigencia de "ancho/alto mínimo" excederá el tamaño natural de la ventana del usuario. Esto fuerza que la clase `QMainWindow` dispare el redimensionamiento obligatorio a macOS para agrandar toda la ventana sí o sí.
Al agrandar la ventana artificialmente, nuestro escalador global de accesibilidad (`UIScaler`) detecta el cambio de tamaño y puede decidir **agrandar las fuentes**. El texto voluminoso obliga al widget a exigir más espacio, forzando a repintar y atrapar a la UI en un ciclo letal de parpadeos y congelamiento.

**Regla de Oro:**
- Cualquier pantalla de navegación que crezca en vertical más allá de lo normal **debe ser encapsulada en un `QScrollArea`**.
- La receta de sintaxis estructural para aislar la ventana de desastres es:
```python
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setFrameShape(QFrame.Shape.NoFrame)
content_widget = QWidget()
scroll_area.setWidget(content_widget)

main_layout = QVBoxLayout(content_widget) # Los sub-elementos van aquí
self.layout().addWidget(scroll_area) # Y el scroll va a la ventana
```

### Contexto del Incidente
Estas directivas han mitigado y solucionado los episodios críticos y repetitivos de congelamientos en las vistas de `MachinesWidget`, `Historial de Trabajador` y `Configuración` (marzo de 2026). Jamás subestimes la influencia de un WordWrap o un QTabWidget en este ecosistema.
