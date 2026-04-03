---
name: Fase Monolitos Finales — Autopilot
description: Bucle autónomo continuo para fragmentar los 75 archivos pesados. Ejecuta refactorización extrema con tests 100%, 0 errores Mypy y documentación, basando todas sus decisiones en la calidad del código, sin consultar al usuario.
---

# [ARCHIVO — no usar como backlog activo] Fase Monolitos Finales — Autopilot

> **Modo Autónomo Extremo**: Tienes TOTAL LIBRERTAD Y AUTORIDAD para tomar cualquier decisión arquitectónica o de refactorización necesaria. Tu única regla de oro es maximizar la **calidad**, **estabilidad** y **escalabilidad** del software. **NO PREGUNTES al usuario**. Toma la decisión, documéntala internamente si es necesario, y sigue adelante.

## 🎯 Objetivo de la Skill
Transformar por completo el repositorio leyendo el documento `documentacion/Monolitos_finales.md`. Desmantelar los 75 archivos especificados, dividiéndolos en módulos cohesivos e inyectables con tests perfectos y cero errores Mypy.

---

## 🔁 El Bucle de Trabajo (Loop)

Esta skill es un bucle perpetuo. Cuando acabe con un archivo, pasará automáticamente al siguiente de la lista, sin detenerse hasta que la lista entera esté completada o el proceso sea interrumpido por el usuario.

### Paso 1: Selección y Verificación Inicial
1. Abre y lee el documento `documentacion/Monolitos_finales.md`.
2. Identifica el **primer archivo** de la lista que aún no haya sido refactorizado (puedes verificarlo creando un checklist interno de tracking en la carpeta `documentacion/` o marcándolos con check en el propio markdown si lo prefieres, pero decide tú el sistema, por ejemplo, borrar el archivo de ese listado o tacharlo `~~archivo~~`).
3. Ejecuta los tests correspondientes al archivo original para asegurar que la "baseline" está en verde antes de empezar a tocar código (`python3 run_tests.py` o ejecutar pytest directo al módulo respectivo).

### Paso 2: Refactorización Estructural (El Corte)
1. **Analiza** internamente cómo vas a dividir el archivo apoyándote en la sugerencia que te proporciona `Monolitos_finales.md`.
2. **Contrato UI/DTO (Fase 12C)**: Rediseña los contratos internos. **PROHIBIDO** pasar diccionarios a los nuevos componentes o al Presenter. Define o usa DTOs existentes en `core/dtos.py`.
3. Toma decisiones basadas **SIEMPRE** en SRP (Single Responsibility Principle) e Inyección de Dependencias.
4. Genera los nuevos archivos `.py` extrayendo clases, renderers, presenters, repositorios o calculadoras específicas.
5. Sustituye la lógica monolítica en el archivo original actuando como Façade, o destrúyelo y ajusta las importaciones globales si es lo mejor para el proyecto.

### Paso 3: Tipado Estricto absoluto (Mypy)
1. Pasa Mypy sobre los nuevos archivos explícitamente (`mypy --strict ruta/del/nuevo/archivo.py`).
2. **Cero errores tolerados**. No introduzcas ningún `type: ignore` por tu cuenta para tapar parches. Arregla el diseño si los tipos chocan.
3. **Erradicación de Diccionarios**: Elimina cualquier acceso del tipo `obj["key"]` o `obj.get("key")` en la UI. Sustitúyelo por atributos de DTO (`obj.key`). Si el DTO no tiene el campo, añádelo a `core/dtos.py` con su tipo correcto.

### Paso 4: Pruebas (TDD Inverso) al 100% de Calidad
1. Lee tu skill interna `strict_testing` y `testing_por_capa`.
2. Genera los archivos `test_xxx.py` de todo lo modificado.
3. Pasa `pytest --cov=ruta/donde/modificaste tests/` y NO PASES al siguiente paso hasta tener **100% de cobertura de líneas** y ningún solo skipped o warning.
4. **Mocks Estrictos**: Usa siempre `create_autospec` y `autospec=True`. Nunca instancies `MagicMock()` sin spec. Valida outputs con asserts y delegaciones con `assert_called_once_with`.
5. Si falla un test, arréglalo automáticamente analizando el log de error o refactorizando de nuevo el código.

### Paso 5: Documentación y Finalización del Ciclo
1. Añade docstrings (Google Style) en todos los módulos, nuevas clases y métodos creados. Documentación 100% en español.
2. Ejecuta el recopilador: `python3 scripts/generate_daniel_doc.py`.
3. Certifica que todo en el pipeline sigue estable (`python3 run_tests_safe.py` o similar a nivel proyecto general).
4. Edita el registro/`Monolitos_finales.md` para marcar este monolito como **SUPERADO**.

### Paso 6: Siguiente Iteración
Inmediatamente tras certificar el éxito del paso 5, selecciona el siguiente archivo en la secuencia y **repite desde el Paso 1**. No uses `notify_user` excepto si la tarea general se da enteramente por concluida, o si existe un impedimento crítico inevitable que requiera intervención manual (muy infrecuente).

---

## 🛡️ Límites y Responsabilidades

- **Tolerancia a fallos**: Si romper un ciclo de dependencia rompe docenas de módulos, repara esos docenas de módulos. Si es inasumible, extrae una interfaz (Protocol) y rompe la dependencia.
- **Autoridad sobre arquitectura**: Eres el máximo responsable de la calidad del código, haz lo que sea necesario sin esperar confirmación para cumplir al 100% la limpieza del código.
- **Asuncion**: Todo lo generado debe coincidir perfectamente con el código legacy pero de una forma inmensamente más limpia. No añadas "features" o funcionalidades de producto que alteren el propósito del código actual, solamente límpialo y sepáralo.
