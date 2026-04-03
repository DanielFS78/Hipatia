# Proyecto Hipatia

Sistema de gestión de producción industrial con simulador de flujos, trazabilidad de lotes,
gestión de máquinas y trabajadores, y generación de informes. Desarrollado en Python con PyQt6.

---

## Estado del Proyecto (2026-03-15)

| Métrica | Valor |
|---------|-------|
| Score de calidad de tests | 38.0 / 100 (optimizado: 41.4) |
| Cobertura global | 97.3% |
| Tests ejecutándose | 201 archivos, 0 fallos |
| Archivos en techo de calidad | 66 / 201 |

**Fase activa:** Fase 2 — Eliminación de Antipatrones de Testing (Grupo B)

---

## Documentación

| Recurso | Descripción |
|---------|-------------|
| `PLAN_ACCION_TECNICO.md` | Estado actual y roadmap de fases |
| `.agents/skills/plan_mejora_calidad/SKILL.md` | Plan operativo detallado (fuente de verdad) |
| `.agents/skills/backlog_tests/SKILL.md` | Backlog priorizado de archivos a mejorar |
| `Documentacion/Mejora_Calidad/` | Informes históricos por fase |
| `Documentacion/Analisis_Inicial/` | Análisis inicial del proyecto (referencial) |
| `Documentacion Daniel.md` | Documentación técnica generada automáticamente |

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

# Validar que no existan archivos omitidos en documentación
python scripts/check_documentation_omissions.py
```

---

## Stack tecnológico

- Python 3.11 + PyQt6 (interfaz de usuario)
- PostgreSQL + SQLAlchemy (persistencia)
- pytest + coverage (testing)
- Ver `Documentacion/Analisis_Inicial/ANALISIS_TECNOLOGIAS.md` para análisis completo

---

## Onboarding e instalación (entorno local)

1. Crear y activar entorno virtual (`python3 -m venv .venv`).
2. Instalar dependencias (`pip install -r requirements.txt`).
3. Inicializar configuración (`cp .env.example .env` y ajustar rutas/credenciales).
4. Verificar acceso a base de datos y recursos (`python scripts/verify_qr_optimization.py` y `python tests/utils/check_db.py`).
5. Arrancar aplicación (`python app.py`).

## Despliegue (Windows objetivo de producción)

- Empaquetado ejecutable: `python build_executable.py`.
- Validación de plataforma: seguir checklist en `.agents/skills/preparacion_windows/SKILL.md`.
- Recursos críticos en despliegue:
  - Base de datos/configuración en `config/` y `database/`.
  - Logs de ejecución y auditoría en carpeta de datos de la aplicación.
  - Plugins Qt/cámara y rutas de OpenCV según entorno Windows.

## Seguridad y arquitectura (resumen operativo)

- **RBAC**: el acceso funcional se controla con permisos/roles (`core/security/access_control.py`).
- **Fase 12C DTO-first**: la UI no intercambia diccionarios crudos con dominio; usar DTOs de `core/dtos.py`.
- **Sincronización offline**: flujo USB/local gestionado por `core/sync_service.py` (comparación y aplicación controlada de cambios).
