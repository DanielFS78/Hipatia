# Objetivo: Refactorización a Objetos Fuertemente Tipados y Generación de Tests E2E

Actúa como un Arquitecto de Software Senior en Python/PyQt. Mi proyecto actual usa tuplas crudas `(id, nombre, ...)` para mover datos entre la Base de Datos y la UI, lo cual ha causado errores de índices silenciosos.

Quiero migrar a una arquitectura basada en **Data Classes** (DTOs) y generar una suite de tests E2E que garantice el funcionamiento de los flujos críticos.

realiza las siguientes tareas paso a paso:

## FASE 1: Definición de Contratos de Datos (DTOs)
1. Analiza el archivo `database/models.py` para entender las entidades (Máquinas, Trabajadores, etc.).
2. Crea un nuevo archivo `database/schemas.py` o `core/dtos.py`.
3. Genera `dataclasses` (o modelos Pydantic) para cada entidad que se usa en la UI.
   - Ejemplo: `class MachineDTO`: debe tener `id: int`, `nombre: str`, `departamento: str`, `tipo_proceso: str`, `activa: bool`.
   - Asegúrate de que los tipos sean explícitos.

## FASE 2: Refactorización de Repositorios
1. Modifica `database/repositories/machine_repository.py` (y otros relevantes).
2. En lugar de devolver tuplas con `_convert_list_to_tuples`, modifica el código para que instancie y devuelva los objetos DTO creados en la Fase 1.
3. *Importante*: Esto romperá la UI temporalmente. No la arregles todavía, concéntrate en la capa de datos.

## FASE 3: Generación de Tests E2E (La Garantía)
Crea una nueva carpeta `tests/e2e_flows/`. Genera tests usando `pytest` que simulen el flujo completo usando los nuevos Objetos.
Estuctura de los tests:
1. **Setup**: Iniciar base de datos de prueba limpia.
2. **Action**: Llamar a los métodos del controlador/repositorio para Crear/Editar (ej: `repo.add_machine(...)`).
3. **Verification**:
   - Recuperar el objeto resultante.
   - **ASERCIONES POR ATRIBUTO**: `assert machine_obj.nombre == "Torno"` (Prohibido usar índices numéricos como `machine[1]`).
   - Verificar integridad de tipos: `assert isinstance(machine_obj.activa, bool)`.

## FASE 4: Adaptación de la UI (Reparación)
1. Ve a `ui/widgets.py` y `app.py`.
2. Actualiza los métodos `populate_list`, `show_details`, etc.
3. Reemplaza los accesos por índice (`item[2]`) por accesos por atributo (`item.departamento`).

## Resultado Esperado
Quiero que el sistema sea resistente a cambios de orden en las columnas de la base de datos. Entrégame el código de los DTOs, el Repositorio refactorizado y un ejemplo sólido de Test E2E.
