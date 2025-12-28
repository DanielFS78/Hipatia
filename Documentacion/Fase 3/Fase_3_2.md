# Fase 3.2: Refactorización y Desacoplamiento de AppModel

## 1. Contexto
Siguiendo el Plan de Refactorización de la Fase 3, se ha procedido a extraer la lógica de negocio (`AppModel`) del archivo monolítico `app.py` a su propio módulo dedicado `core/app_model.py`.

## 2. Cambios Realizados

### Refactorización Estructural
- **Extracción de Clase:** La clase `AppModel` (aprox. 800 líneas) fue movida de `app.py` a `core/app_model.py`.
- **Actualización de Dependencias:** `app.py` ahora importa `AppModel` desde el núcleo en lugar de definirla internamente.
  ```python
  from core.app_model import AppModel
  ```

### Resolución de Incidencias Técnicas
Durante la refactorización y ejecución, se identificó un error crítico que provocaba el cierre de la aplicación al acceder al Dashboard:

**Problema:**
```
AttributeError: 'DatabaseManager' object has no attribute 'get_problematic_components_stats'
```

**Causa:**
El método `get_problematic_components_stats` fue migrado previamente al `MaterialRepository` (siguiendo los principios de Fase 2), pero `AppModel` seguía intentando acceder a él a través de la clase legacy `DatabaseManager` (`self.db`), la cual ya no exponía ese método proxy.

**Afectación:**
Este error impedía la carga de estadísticas en el Dashboard principal.

**Solución Implementada:**
1.  **Inyección de Repositorio:** Se añadió `self.material_repo` a la inicialización de `AppModel` para tener acceso directo al repositorio de materiales.
2.  **Redirección de Llamada:** Se actualizó el método en `AppModel` para consumir directamente el repositorio:
    ```python
    # Antes (Incorrecto)
    return self.db.get_problematic_components_stats()
    
    # Ahora (Corregido)
    return self.material_repo.get_problematic_components_stats()
    ```

## 3. Estado Actual
- **AppModel:** Desacoplado exitosamente en `core/`.
- **Dashboard:** Funcionalidad restaurada y validada.
- **Tests:** Se requiere la creación de nuevos tests unitarios específicos para `core/app_model.py` (ver Fase 3.1) para asegurar que la cobertura se mantenga alta tras el movimiento de código.

## 4. Próximos Pasos (Fase 3.3)
Continuar con la refactorización creando tests para `AppController` y preparando su extracción, siguiendo el diagrama de flujo general de la Fase 3.
