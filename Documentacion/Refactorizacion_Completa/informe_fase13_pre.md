# Informe Pre-Fase: Fase 13 - Escalado Dinámico y UI Responsante

**Fecha:** 2026-03-10
**Fase:** Fase 13 (Nueva fase añadida)

## 1. Análisis del Problema
Los operarios que usan portátiles con resoluciones menores a 1080p (por ejemplo, 1366x768) experimentan recortes en la interfaz inferior de la aplicación. Controles importantes quedan fuera de los márgenes de visualización y Qt no reflowea el contenido adecuadamente con tamaños absolutos.

## 2. Solución a Implementar (Propuesta Aprobada)
Implementar un "Factor de Escala Dinámico" global en la arquitectura gráfica.

### Componentes de la Solución:
1. **El Motor ("UIScaler"):** Una clase en utilidades gráficas que leerá la resolución activa del SO y devolverá un multiplicador (0.6 a 1.2).
2. **Generador de Estilos:** Una función que tomará este multiplicador para reescribir `font-size`, `padding`, `margin` al vuelo e inyectarlo en el `QApplication` o en la instancia base.
3. **Control Manual ("El Botón"):** Un botón persistente tipo "Auto Ajustar" (refresco forzado) en las ventanas principales (`MainView`). Llama a repintar e iterar por todas las sub-páginas (`adjustSize()`).
4. **Navegación Consciente:** El `NavigationController` detectará si se ha hecho switch a una página "densa" (ej: Simulación) y pre-escalará o reajustará la geometría preventivamente.

## 3. Estrategia de Archivos
* Archivos nuevos: `core/utils/ui_scaler.py` (y sus test asociados).
* Archivos modificados: 
  - `ui/main_window.py`
  - `controllers/navigation_controller.py`
  - `tests/unit/test_main_window.py`
  - `tests/unit/test_navigation_controller_comprehensive.py`

## 4. Metodología Obligatoria
- **Flujo MCP:** Ciclo completo documentado.
- **TDD / Test-First:** Construir lógica vacía, escribir test, pasar test.
- **Calidad Absoluta:** 100% Code Coverage (`pytest-cov`), Sin descensos. Tipado estricto `mypy`. En las clases nuevas, todo el docstring en español bajo la convención Google.

---
**Firma de Autorización del Plan:** Sistema Antigravity / Usuario (pendiente de Aprobación en la sesión).
