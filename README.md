# Proyecto Hipatia

[![CI](https://github.com/DanielFS78/Hipatia/actions/workflows/ci.yml/badge.svg)](https://github.com/DanielFS78/Hipatia/actions/workflows/ci.yml)

Sistema de gestión de producción industrial con simulador de flujos, trazabilidad de lotes,
gestión de máquinas y trabajadores, y generación de informes. Desarrollado en Python con PyQt6.

---

## Estado del proyecto y métricas

<!-- HIPATIA_METRICS_BEGIN -->

> **Regeneración:** `python scripts/update_readme_metrics.py`  
> **Datos:** `test_reports/compliance_data.json` vía `python scripts/test_quality_analyzer.py`; `coverage.json` vía `pytest tests --cov=. --cov-report=json` (archivo en `.gitignore`).

| Métrica | Valor |
|---------|-------|
| Fecha de referencia | 2026-04-08 |
| Python usado al generar | 3.13.5 |
| Casos de test recogidos (pytest) | 2716 |
| Archivos `test_*.py` (sin copias `* N.py`) | 226 |
| Cobertura global (`pytest tests --cov=.`) | 86.1% |
| Score calidad medio (absoluto → techo medio) | 75.3 → 77.2 |
| Entradas en analizador de calidad | 238 |
| Entradas marcadas «en techo» | 238 / 238 |
| …de ellas, archivos `test_*.py` en techo | 226 |

<!-- HIPATIA_METRICS_END -->



**Plan de mejora de calidad:** `.agents/skills/plan_mejora_calidad/SKILL.md`

---

## Documentación

| Recurso | Descripción |
|---------|-------------|
| `Documentacion/MAPA_NAVEGACION_CODIGO.md` | **Primera lectura** para orientarse en capas, carpetas (vivo vs histórico) y flujos sin abrir la doc masiva |
| `PLAN_ACCION_TECNICO.md` | Estado actual y roadmap de fases |
| `.agents/skills/plan_mejora_calidad/SKILL.md` | Plan operativo detallado (fuente de verdad) |
| `.agents/skills/backlog_tests/SKILL.md` | Backlog priorizado de archivos a mejorar |
| `Documentacion/Mejora_Calidad/` | Informes históricos por fase |
| `Documentacion/Analisis_Inicial/` | Análisis inicial del proyecto (referencial) |
| `Documentacion Daniel.md` | Documentación técnica generada automáticamente |
| `Documentacion/Despliegue_Windows.md` | Empaquetado PyInstaller, rutas de datos y checklist de fábrica |

---

## Arranque rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python app.py

# Ejecutar tests con métricas de calidad
python run_tests.py

# Regenerar documentación técnica
python scripts/generate_daniel_doc.py

# Actualizar tabla de métricas del README (tras analyzer y/o cobertura)
python scripts/update_readme_metrics.py

# Validar que no existan archivos omitidos en documentación
python scripts/check_documentation_omissions.py
```

---

## Stack tecnológico

- **Python 3.11+** (tipado con mypy usando `python_version = 3.12`; **CI en GitHub:** 3.11 y 3.12)
- **PyQt6** (interfaz de usuario)
- PostgreSQL + SQLAlchemy (persistencia)
- pytest + coverage (testing)
- Ver `Documentacion/Analisis_Inicial/ANALISIS_TECNOLOGIAS.md` para análisis completo

### Integración continua

- Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
  - **tests:** `pytest` en **Python 3.11 y 3.12**, `QT_QPA_PLATFORM=offscreen`.
  - **mypy:** Python 3.12, `mypy app.py core controllers database features ui` (alineado con `mypy.ini`).
  - **coverage-report:** Python 3.12, suite completa con `--cov-report=json`; el artefacto **`coverage-json`** contiene `coverage.json` (descarga desde la pestaña *Actions* → run → *Artifacts*; útil para alinear métricas sin commitear el archivo).
- Si el badge anterior no carga (fork u otro remoto), ignóralo o ajusta la URL del repositorio.

---

## Onboarding e instalación (entorno local)

1. Crear y activar entorno virtual (`python3.12 -m venv .venv` o **3.11+**).
2. Instalar dependencias (`pip install -r requirements.txt`).
3. Inicializar configuración (`cp .env.example .env` y ajustar rutas/credenciales).
4. Verificar acceso a base de datos y recursos (`python scripts/verify_qr_optimization.py` y `python tests/utils/check_db.py`).
5. Arrancar aplicación (`python app.py`).

## Despliegue (Windows objetivo de producción)

- **EXE en GitHub Actions (automático):** cada push a la rama `main` ejecuta [Build Windows EXE](https://github.com/DanielFS78/Hipatia/actions/workflows/build-windows.yml) y publica el artefacto **Hipatia-windows-onedir** (carpeta `dist/Hipatia` con `Hipatia.exe`). También puedes lanzarlo a mano con «Run workflow».
- Empaquetado local en Windows: `build_windows.bat` (o `pyinstaller hipatia.spec`).
- Validación de plataforma: seguir checklist en `.agents/skills/preparacion_windows/SKILL.md`.
- Recursos críticos en despliegue:
  - Base de datos/configuración en `config/` y `database/`.
  - Logs de ejecución y auditoría en carpeta de datos de la aplicación.
  - Plugins Qt/cámara y rutas de OpenCV según entorno Windows.

## Seguridad y arquitectura (resumen operativo)

- **RBAC**: el acceso funcional se controla con permisos/roles (`core/security/access_control.py`).
- **Fase 12C DTO-first**: la UI no intercambia diccionarios crudos con dominio; usar DTOs de `core/dtos.py`.
- **Sincronización offline**: flujo USB/local gestionado por `core/sync_service.py` (comparación y aplicación controlada de cambios).
