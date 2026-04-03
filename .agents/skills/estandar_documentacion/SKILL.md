---
name: Estandar de Documentacion
description: Reglas obligatorias para docstrings y para la generación automática de documentación técnica de Hipatia, incluyendo diagramas Mermaid de arquitectura, ERD, árbol de carpetas y flujos.
---

# Estandar de Documentacion

> Regla de Oro: cada vez que se modifique o cree un archivo `.py`, es obligatorio implementar o actualizar sus docstrings. Sin docstring, el archivo no aparece en la documentación generada.

---

## 1. Estructura de docstrings (Google Style)

### Módulo (al inicio del archivo, antes de los imports)

```python
"""
Nombre del Módulo: backup_controller
Descripcion: Gestiona las operaciones de copia de seguridad, restauracion
             e importacion de la base de datos y logs del sistema.
"""
import os
```

### Clase

```python
class BackupController:
    """
    Controlador encargado de la gestion de copias de seguridad.

    Centraliza la logica para crear backups estructurados por fecha,
    importar datos desde paquetes ZIP y exportar la BD actual.
    """
```

### Metodo / Funcion

```python
def create_automatic_backup(self) -> bool:
    """
    Realiza una copia de seguridad automatica completa.

    Args:
        destination: Ruta de destino del backup.
        compress: Si True, comprime el resultado en ZIP.

    Returns:
        True si el proceso se completo con exito, False en caso contrario.
    """
```

---

## 2. Reglas de estilo

- Primera linea: resumen conciso que termina en punto.
- Idioma: español para descripciones, inglés/español para términos técnicos según el contexto del archivo.
- Si cambias la lógica de una función, actualiza su docstring. La documentación que miente es peor que no tener documentación.
- Matemáticas y Heurísticas: Si una clase contiene algoritmos complejos o heurísticas (ej. optimizadores o calculadoras de tiempos), el docstring DEBE explicar el algoritmo, las fórmulas matemáticas aplicadas o la estrategia (ej. iteración secuencial de recursos). No te limites a decir "Qué hace", explica "Cómo lo calcula".
- Reglas de Negocio: Si una clase modela una regla lógica abstracta (ej. condiciones de reasignación), especifica cuáles son esas condiciones reales aplicadas a la planta de producción.
- Diccionario de Datos: Si atributos en los modelos SQLAlchemy representan enums, flags o niveles predefinidos (como integers para tipos de rol), mapea explicitamente el significado de cada número en el docstring de la clase.
- Rendimiento Visual (UI): En widgets intensivos o con animaciones repetitivas (efectos luminosos en Canvas), documenta cómo gestionan los repintados sin bloquear el hilo principal (`QTimer` de PyQt6, `eventFilter`, llamadas directas a hardware, etc.).
- Nomenclatura: `PascalCase` para clases, `snake_case` para funciones y variables, `SCREAMING_SNAKE_CASE` para constantes.

---

## 3. Generar la documentacion

```bash
python3 scripts/generate_daniel_doc.py
```

Genera `Documentacion Daniel.md` y `Documentacion Daniel.pdf` automáticamente. El script:

1. Extrae docstrings de todos los archivos en `controllers/`, `core/`, `database/`, `features/`, `ui/`
2. Genera diagramas Mermaid automáticos (ver sección 4)
3. Construye tablas de modelos, tecnologías y capas
4. Convierte a PDF con tabla de contenidos automática
5. Inserta al inicio un `Índice de Código (completo y verificable)` que:
   - lista carpetas/subcarpetas y archivos `.py` (incluye los omitidos)
   - lista clases detectadas por AST (aunque luego no aparezcan en el cuerpo si no hay docstrings relevantes)
   - muestra número de página exacto como `pNNNN` (dónde empieza el bloque del archivo en el PDF)
   - etiqueta el estado de tipado mypy como `Mypy Sí/Parcial` con una razón breve derivada de `mypy.ini`

No hay pasos manuales. Ejecutar el script es suficiente.

---

## 4. Diagramas generados automaticamente

El script genera los siguientes diagramas Mermaid en cada ejecucion:

### ERD (Modelo de Base de Datos)
Extraido de `database/models/`. Muestra todas las entidades y sus relaciones:
- `Producto` → `Subfabricacion`, `ProcesoMecanico`, `ProductIteration`, `Material`
- `Fabricacion` → `Preproceso` (M-M), `Trabajador` (M-M), `TrabajoLog`
- `Maquina` → `GrupoPreparacion` → `PreparacionPaso`
- `Pila` → `PasoPila`, `DiarioBitacora`
- `Lote` → `Producto` (M-M), `Fabricacion` (M-M)

Si añades un modelo nuevo, actualiza la constante `MERMAID_ERD` en el script.

### Arquitectura por capas
Diagrama `graph TD` que muestra la jerarquía UI → Controllers → Services → Database con el DIContainer.

### Arbol de carpetas
Generado dinámicamente desde el sistema de archivos real. Muestra las carpetas principales y sus subcarpetas de primer nivel.

### Flujo de Fabricacion y QR
Diagrama `sequenceDiagram` que muestra el flujo completo: crear OF → generar etiquetas QR → escanear inicio → registrar TrabajoLog.

### Flujo del Motor de Simulacion
Diagrama `graph LR` que muestra: Pila → SimulationEngine → Motor de Eventos → TimelineTask → ResultsCompiler → GanttWidget.

---

## 5. Cuando actualizar los diagramas del script

Los diagramas de arquitectura y flujos son constantes en el script (`MERMAID_ERD`, `MERMAID_ARQUITECTURA`, etc.). Actualízalos manualmente cuando:

- Añadas un modelo SQLAlchemy nuevo → actualizar `MERMAID_ERD`
- Añadas un controller nuevo → actualizar `MERMAID_ARQUITECTURA`
- Cambies el flujo de fabricación o simulación → actualizar los diagramas de flujo correspondientes

El árbol de carpetas (`_build_folder_tree_mermaid`) se genera solo desde el filesystem, no necesita actualización manual.

---

## 6. Cómo hacer la documentación más visual y amigable

El script genera Markdown con diagramas Mermaid. Para mejorar la legibilidad:

### Dividir el ERD en sub-diagramas por dominio

El ERD completo con 11 entidades es difícil de leer. Divide en sub-diagramas añadiendo constantes al script:

```python
MERMAID_ERD_FABRICACION = '''```mermaid
erDiagram
    Fabricacion { int id PK; string codigo; string descripcion }
    Preproceso { int id PK; string nombre; float tiempo }
    Trabajador { int id PK; string nombre_completo; string role }
    Fabricacion }o--o{ Preproceso : "vincula"
    Fabricacion }o--o{ Trabajador : "asignados"
```'''

MERMAID_ERD_PRODUCTOS = '''```mermaid
erDiagram
    Producto { string codigo PK; string descripcion; float tiempo_optimo }
    Subfabricacion { int id PK; string producto_codigo FK; float tiempo }
    Material { int id PK; string codigo_componente }
    Producto ||--o{ Subfabricacion : "tiene"
    Producto }o--o{ Material : "requiere"
```'''
```

Luego en `generate_markdown()`, escribe cada sub-diagrama con su título:
```python
md.write("### Dominio de Fabricación\n\n")
md.write(MERMAID_ERD_FABRICACION + "\n\n")
md.write("### Dominio de Productos\n\n")
md.write(MERMAID_ERD_PRODUCTOS + "\n\n")
```

### Añadir tabla de conexiones entre capas

Después del diagrama de arquitectura, añade una tabla que explique las conexiones clave:

```python
md.write("| Componente | Depende de | Tipo |\n")
md.write("|---|---|---|\n")
md.write("| BackupController | BackupService | Inyección de dependencia |\n")
md.write("| BackupService | DatabaseManager | Acceso a datos |\n")
md.write("| AppModel | Todos los Services | Fachada |\n")
```

### Añadir sección de "Cómo añadir X"

Para que la documentación sea útil para nuevos desarrolladores, añade una sección de guías rápidas:

```python
md.write("## Guías Rápidas\n\n")
md.write("### Cómo añadir un nuevo modelo\n\n")
md.write("1. Crear el modelo en `database/models/`\n")
md.write("2. Crear el repositorio en `database/repositories/`\n")
md.write("3. Añadir el repositorio al `DatabaseManager`\n")
md.write("4. Crear el servicio en `core/services/`\n")
md.write("5. Registrar en `DIContainer`\n")
md.write("6. Actualizar `MERMAID_ERD` en este script\n\n")
```

---

## 7. Checklist antes de hacer commit

- [ ] El archivo tiene docstring de módulo antes de los imports
- [ ] Todas las clases nuevas o modificadas tienen docstring
- [ ] Todos los métodos públicos tienen docstring con Args/Returns si la firma es compleja
- [ ] Si se añadio un modelo SQLAlchemy, se actualizo `MERMAID_ERD` en el script
- [ ] Si se añadio un controller, se actualizo `MERMAID_ARQUITECTURA` en el script
- [ ] Se ejecuto `python3 scripts/generate_daniel_doc.py` y genero sin errores
