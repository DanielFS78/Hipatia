# Fase 3.5: Tests para MainWindow (Reporte de Ejecución)

> **Fecha:** 27 de Diciembre de 2025
> **Estado:** Completado ✅
> **Responsable:** Antigravity Agent

---

## 1. Resumen Ejecutivo

Se ha completado la **Fase 3.5** del Plan de Refactorización. Esta fase tenía como objetivo asegurar la estabilidad de la clase `MainView` (anteriormente referida como `MainWindow` en planes previos) antes de proceder a su refactorización.

Se han implementado **tests unitarios** con mocks aislados y **tests E2E** (end-to-end) de flujo de navegación utilizando una base de datos en memoria para validar la integración real con `AppController` y `AppModel`.

| Métrica | Resultado |
|---------|-----------|
| **Tests Creados** | 7 (5 Unitarios, 2 E2E) |
| **Estado** | 7 Pasando (100%) |
| **Tiempo de Ejecución** | ~0.7s |
| **Cobertura en `app.py`** | 69% (Enfocado en MainView lógica) |

---

## 2. Archivos Creados

### 2.1 Tests Unitarios (`tests/unit/test_main_window.py`)
Objetivo: Validar la inicialización y lógica interna de `MainView` aislada de dependencias externas.
- **Fixture:** `main_view` mocks de todos los widgets (`app.HomeWidget`, `app.DashboardWidget`, etc.) y `AppController`.
- **Cobertura:**
    - Inicialización correcta de título y geometría.
    - Estructura de navegación (existencia de páginas y botones).
    - Lógica de `switch_page`.
    - Delegación de eventos de clic en botones.
    - Lógica de selección de menú (Planificación).

### 2.2 Tests E2E (`tests/e2e/test_main_window_flows.py`)
Objetivo: Validar flujos de usuario reales y la integración `View <-> Controller <-> Model`.
- **Fixture:** `app_stack` crea instancias **REALES** de `MainView`, `AppController` y `AppModel` (usando `in_memory_db_manager`).
- **Mocks:** Se utilizaron mocks inteligentes para los widgets pesados (`GestionDatosWidget`, etc.) para evitar dependencias de hardware (cámaras) o UI compleja, pero manteniendo la estructura necesaria para que el controlador funcione (e.g., tabs mockeadas).
- **Cobertura:**
    - Navegación real actualiza el estado de la vista.
    - Verificación de la integridad de la conexión Controlador-Vista.

---

## 3. Resolucíon de Problemas Encontrados

Durante la implementación se resolvieron los siguientes obstáculos:

1.  **Bloqueo por Diálogos Modales:**
    - *Problema:* `MainView.closeEvent` lanza un diálogo de confirmación que bloqueaba la finalización de los tests.
    - *Solución:* Se mockeó `view.show_confirmation_dialog` en los fixtures para retornar `True` automáticamente.

2.  **Conflicto con `pytest-qt`:**
    - *Problema:* Una fixture manual `qtbot` en `conftest.py` entraba en conflicto con el plugin `pytest-qt`, causando errores de `AttributeError: 'QApplication' object has no attribute 'node'`.
    - *Solución:* Se eliminó la fixture manual redundante en `conftest.py` para usar la oficial del plugin.

3.  **Dependencias de `GestionDatosWidget`:**
    - *Problema:* El controlador intenta acceder a pestañas específicas (`productos_tab`, `trabajadores_tab`) al inicializarse.
    - *Solución:* Se creó un `MockGestionDatosWidget` específico en los tests E2E que simula estos atributos, permitiendo que `AppController` se inicialice sin errores.

---

## 4. Próximos Pasos (Fase 3.6)

Con los tests de `MainView` pasando y estables, se puede proceder con seguridad a la **Fase 3.6: Refactorización de MainWindow**.

**Plan para Fase 3.6:**
1.  Extraer `MainView` de `app.py` a `ui/main_window.py`.
2.  Mantener `app.py` solo como punto de entrada (setup y bootstrap).
3.  Verificar que los imports en `controllers/app_controller.py` y `tests/` se actualicen correctamente.
