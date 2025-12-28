# Eliminación de MaintenanceRepository (Código Muerto)

> **Fecha:** 26 de Diciembre de 2025  
> **Tipo:** Limpieza de código / Refactorización

---

## 1. Contexto

Durante el análisis de la suite de tests y la estructura del proyecto, se identificó que el archivo `maintenance_repository.py` contenía **código muerto** que nunca se ejecutaba correctamente.

---

## 2. Problema Identificado

El `MaintenanceRepository` tenía una referencia circular que causaría un error en tiempo de ejecución si se intentara usar:

```python
# maintenance_repository.py (ANTES)
class MaintenanceRepository(BaseRepository):
    def add_maintenance_record(self, machine_id, maintenance_date, notes=""):
        # ❌ ERROR: self.maintenance_repo NO EXISTE en esta clase
        return self.maintenance_repo.add_maintenance_record(machine_id, maintenance_date, notes)
    
    def get_maintenance_history(self, machine_id):
        # ❌ ERROR: self.maintenance_repo NO EXISTE en esta clase
        return self.maintenance_repo.get_maintenance_history(machine_id)
```

### ¿Por qué era código muerto?

1. La clase delegaba a `self.maintenance_repo`, un atributo que **nunca se definió**
2. Si alguien intentara usar estos métodos, obtendría un `AttributeError`
3. La funcionalidad **ya estaba correctamente implementada** en `MachineRepository`

---

## 3. Funcionalidad Correcta (MachineRepository)

El `MachineRepository` ya contenía los métodos de mantenimiento funcionando correctamente con DTOs:

```python
# machine_repository.py
class MachineRepository(BaseRepository):
    def add_machine_maintenance(self, machine_id: int, maintenance_date: date, notes: str) -> bool:
        """Añade un registro de mantenimiento para una máquina."""
        # Implementación completa y funcional
        ...
    
    def get_machine_maintenance_history(self, machine_id: int) -> List[MachineMaintenanceDTO]:
        """Obtiene el historial de mantenimientos, devolviendo DTOs."""
        # Implementación completa y funcional
        ...
```

---

## 4. Cambios Realizados

| Archivo | Acción | Razón |
|---------|--------|-------|
| `database/repositories/maintenance_repository.py` | 🗑️ **Eliminado** | Código muerto con referencia circular |
| `database/repositories/__init__.py` | ✏️ Modificado | Removido import y export de `MaintenanceRepository` |
| `database/database_manager.py` | ✏️ Modificado | Removida importación e instanciación |
| `tests/conftest.py` | ✏️ Modificado | Añadido filtro para warnings de sqlite3 |

### Detalle de cambios en database_manager.py

```diff
- from .repositories import (..., MaintenanceRepository, ...)
+ from .repositories import (...) # Sin MaintenanceRepository

- self.maintenance_repo = MaintenanceRepository(self.SessionLocal)
+ # MaintenanceRepository eliminado - funcionalidad en MachineRepository
```

---

## 5. Verificación

Se ejecutó la suite completa de tests después de los cambios:

```bash
python3 -m pytest tests/ -v --tb=short
```

### Resultado:
```
============================= 303 passed in 1.92s ==============================
```

- ✅ **303 tests pasando**
- ✅ **0 errores**
- ✅ **0 warnings** (se añadió filtro para DeprecationWarning de sqlite3)

---

## 6. Lecciones Aprendidas

1. **Código de delegación vacío**: Cuando se migra funcionalidad entre clases, hay que eliminar las clases wrapper vacías que solo delegaban
2. **Tests ayudan pero no detectan todo**: El código muerto compilaba correctamente, pero habría fallado en runtime
3. **Principio YAGNI**: No mantener código "por si acaso" - si la funcionalidad ya existe en otro lugar, eliminar el duplicado

---

## 7. Impacto

**Ningún impacto negativo**. La funcionalidad de mantenimiento de máquinas sigue disponible a través de:

```python
# Uso correcto desde DatabaseManager
db_manager.machine_repo.add_machine_maintenance(machine_id, date, notes)
db_manager.machine_repo.get_machine_maintenance_history(machine_id)
```

---

> **Nota:** Este documento forma parte del registro de mantenimiento del proyecto y debe consultarse junto con `migracion_y_testing_repositorios.md` para entender el contexto completo de las migraciones de repositorios.
