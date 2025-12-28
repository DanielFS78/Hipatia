# Corrección: Gestión de Componentes en Preprocesos

**Fecha:** 2025-12-28  
**Versión:** Fase 3

---

## 📋 Resumen del Problema

Los botones "Añadir Componente", "Editar Componente" y "Eliminar Componente" en la pestaña "🔩 Componentes" del diálogo de Preprocesos **no funcionaban**. Al hacer clic en ellos, no ocurría nada.

---

## 🔍 Diagnóstico

### Síntoma Observado
El log mostraba:
```
PreprocesoDialog.__init__ called. Controller arg: None
_on_add_material clicked. Controller: None
```

El parámetro `controller` llegaba como `None` al diálogo, impidiendo que los botones ejecutaran las acciones del controlador.

### Causa Raíz Identificada

**Código duplicado en `AppController`**: Existían métodos `show_add_preproceso_dialog` y `show_edit_preproceso_dialog` **duplicados** en dos lugares:

| Archivo | Líneas | ¿Pasa controller? |
|---------|--------|-------------------|
| `controllers/app_controller.py` | 3342-3374 | ❌ **NO** |
| `controllers/product_controller.py` | 399-430 | ✅ SÍ |

El sistema estaba llamando a los métodos de `AppController` (que **no pasaban** el controlador), en lugar de los de `ProductController` (que sí lo hacían).

### Por qué existía este código duplicado

Durante la refactorización de Fase 2, se movieron responsabilidades de `AppController` a sub-controladores (`ProductController`, `WorkerController`, `PilaController`). Sin embargo, los métodos de preprocesos en `AppController` **no fueron eliminados**, creando duplicación.

---

## ✅ Solución Aplicada

### 1. Corrección en `AppController` (líneas 3347, 3364)

Se añadió `controller=self.product_controller` a las llamadas de `PreprocesoDialog`:

```python
# ANTES (incorrecto)
dialog = PreprocesoDialog(all_materials=all_materials, parent=self.view)

# DESPUÉS (correcto)
dialog = PreprocesoDialog(all_materials=all_materials, controller=self.product_controller, parent=self.view)
```

### 2. Método faltante en `MaterialRepository`

Se añadió el método `delete_material()` que no existía:

```python
def delete_material(self, material_id: int) -> bool:
    """Elimina un material del sistema."""
    def _operation(session):
        material = session.query(Material).filter_by(id=material_id).first()
        if not material:
            return False
        session.delete(material)
        session.flush()
        return True
    return self.safe_execute(_operation) or False
```

---

## 📁 Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `controllers/app_controller.py` | Añadido `controller=self.product_controller` en líneas 3347, 3364 |
| `database/repositories/material_repository.py` | Añadido método `delete_material()` |
| `ui/dialogs/prep_dialogs.py` | UI de botones ya existía correctamente |

---

## ✔️ Verificación

Tras los cambios, el log muestra correctamente:
```
PreprocesoDialog.__init__ called. Controller arg: <ProductController object at 0x...>
_on_add_material clicked. Controller: <ProductController object at 0x...>
MaterialRepository: Material '1010' añadido con ID 21
```

Los tres botones funcionan:
- ✅ **Añadir Componente**: Crea nuevos materiales en el sistema
- ✅ **Editar Componente**: Modifica código y descripción de materiales existentes
- ✅ **Eliminar Componente**: Elimina materiales del sistema (con confirmación)

---

## 📝 Lecciones Aprendidas

1. **Evitar código duplicado**: Los métodos en `AppController` deberían haberse eliminado cuando se delegaron a `ProductController`.

2. **Verificar toda la cadena de llamadas**: El problema no estaba en el diálogo ni en el controlador V2, sino en un método legacy que seguía siendo invocado.

3. **Usar prints de depuración estratégicos**: El `print(f"DEBUG...")` fue clave para identificar que el código esperado no se ejecutaba.
