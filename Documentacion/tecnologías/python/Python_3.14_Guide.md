# Guía Técnica: Python 3.14.2
> **Versión**: 3.14.2 (Lanzamiento Estable: Diciembre 2025)
> **Estado**: Recomendado para nuevos desarrollos y migraciones.

---

## 1. Introducción y Estado Actual
Python 3.14 representa un hito importante en la evolución del lenguaje, introduciendo cambios fundamentales en el modelo de ejecución (Free-Threaded CPython) y mejoras significativas en la experiencia del desarrollador. Esta versión es LTS (Long Term Support) y recibirá actualizaciones de seguridad hasta Octubre de 2030.

## 2. Nuevas Características Críticas

### 2.1 Free-Threaded CPython (No-GIL) 🚀
Quizás el cambio más grande en la historia de Python. Python 3.14 permite ejecutar código en modo "free-threaded", eliminando el Global Interpreter Lock (GIL).
- **Impacto**: Permite paralelismo real en tareas ligadas a CPU (CPU-bound) sin necesidad de usar `multiprocessing`.
- **Uso**: Requiere binarios específicos o configuración al compilar (`--disable-gil`).
- **Recomendación**: Evaluar para procesos de cálculo intensivo (como el cálculo de tiempos de fabricación).

### 2.2 Compilador JIT (Experimental) ⚡️
Se introduce un compilador Just-In-Time experimental.
- **Funcionamiento**: Traduce bytecode a código máquina en tiempo de ejecución para optimizar "puntos calientes" del código.
- **Estado**: Desactivado por defecto. Activar para pruebas de rendimiento.

### 2.3 Mejoras en el REPL y Errores 🛠️
- **REPL Mejorado**: Edición multilínea, historial persistente, coloreado de sintaxis por defecto.
- **Mensajes de Error**: Tracebacks más claros y sugerencias automáticas para errores tipográficos (e.g., sugerir `NameError` correcciones).

### 2.4 Mejoras en Tipado Estático (Type Hints) 📝
- **PEP 696**: Valores por defecto para parámetros de tipo (Type Parameters Defaults).
- **PEP 742**: `TypeIs` para estrechamiento de tipos (Type Narrowing) más preciso.
- **`TypedDict` Read-only**: Mejoras para definir diccionarios inmutables tipados.

## 3. Guía de Uso y Buenas Prácticas (Python 3.14)

### 3.1 Estilo y Calidad de Código
1.  **Tipado Estricto**: Aprovechar las mejoras de tipado. Usar `mypy` o `pyright` en modo estricto.
    ```python
    # Antes
    def process_items(items: list) -> None: ...
    
    # Ahora (Mejor práctica 3.14)
    def process_items[T](items: list[T]) -> None: ...  # Uso de genéricos nativos y sintaxis nueva
    ```
2.  **Manejo de Excepciones**: Usar `ExceptionGroup` (introducido en 3.11, madurado aquí) para manejar múltiples errores en tareas asíncronas o concurrentes.

### 3.2 Manejo de Fechas (Crítico para este proyecto)
Python 3.14 refuerza el uso de zonas horarias conscientes (timezone-aware).
- **Deprecado/Desaconsejado**: `datetime.utcnow()` y `datetime.utcfromtimestamp()`.
- **Correcto**:
    ```python
    from datetime import datetime, timezone
    
    # CORRECTO
    now = datetime.now(timezone.utc)
    
    # INCORRECTO (Generará warnings o errores)
    now = datetime.now(datetime.UTC) # Asegurarse de usar la importación correcta o timezone.utc
    ```

### 3.3 Rendimiento
- **Inmutabilidad**: Usar el nuevo `copy.replace()` para objetos inmutables (`dataclasses`, `namedtuples`) es más eficiente que crear copias manuales.
- **Slots**: Usar `__slots__` en clases con muchas instancias sigue siendo vital para reducir huella de memoria.

## 4. Estrategia de Migración para `Calcular_tiempos_fabricacion`

### 4.1 Actualización de Modelos
El proyecto actual usa `datetime.now(datetime.UTC)` lo cual es válido en 3.11+, pero hemos detectado issues en los tests. La forma más robusta y compatible hacia atrás (si se usara 3.10) y futuro es:
```python
from datetime import datetime, timezone
default=lambda: datetime.now(timezone.utc)
```

### 4.2 Tests
- Aprovechar `unittest.mock` que ha recibido mejoras de rendimiento.
- Asegurar que los tests asíncronos (si los hay) manejen correctamente la cancelación de tareas, ya que 3.14 es más estricto con el cleanup de corrutinas.

## 5. Terminología Clave Actualizada
- **Free-threading**: Ejecución sin bloqueo global (GIL).
- **JIT (Just-In-Time)**: Compilación dinámica durante ejecución.
- **Type Narrowing**: Reducción del conjunto de tipos posibles de una variable basada en checks de flujo de control.
- **TaskGroups**: (Desde 3.11) La forma recomendada de gestionar tareas asíncronas concurrentes, reemplazando a `gather` en muchos casos.

---
*Documento generado por Antigravity - 25/12/2025*
