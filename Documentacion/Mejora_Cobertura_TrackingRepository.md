# Mejora de Cobertura TrackingRepository

> **Fecha:** 26 de Diciembre de 2025  
> **Tipo:** Mejora de Tests / Cobertura

---

## 1. Contexto

El `TrackingRepository` tenía una cobertura del 74%, con 133 líneas sin cubrir. La mayoría eran bloques de manejo de excepciones SQLAlchemy que nunca se ejecutaban en tests normales.

---

## 2. Análisis Realizado

Se identificaron las siguientes categorías de código sin cobertura:

| Categoría | Líneas | Descripción |
|-----------|--------|-------------|
| Excepciones SQLAlchemy | 15 bloques | `except SQLAlchemyError` en cada método |
| Export edge cases | ~20 líneas | Pasos completados, incidencias anidadas |
| Mappers DTO | ~10 líneas | Excepciones al acceder a relaciones |
| Estadísticas | ~10 líneas | Errores en consultas de stats |

---

## 3. Solución Implementada

### Nuevo Archivo de Tests

Se creó `tests/unit/test_tracking_exceptions.py` con **29 tests nuevos**:

```
TestTrackingRepositoryExceptions (16 tests)
├── test_finalizar_trabajo_log_sqlalchemy_error
├── test_pausar_trabajo_sqlalchemy_error
├── test_reanudar_trabajo_sqlalchemy_error
├── test_obtener_trabajo_por_qr_sqlalchemy_error
├── test_obtener_trabajo_por_id_sqlalchemy_error
├── test_get_paso_activo_por_trabajador_sqlalchemy_error
├── test_get_ultimo_paso_para_qr_sqlalchemy_error
├── test_iniciar_nuevo_paso_sqlalchemy_error
├── test_finalizar_paso_sqlalchemy_error
├── test_obtener_trabajos_activos_sqlalchemy_error
├── test_resolver_incidencia_sqlalchemy_error
├── test_obtener_incidencias_abiertas_sqlalchemy_error
├── test_asignar_trabajador_a_fabricacion_sqlalchemy_error
├── test_desasignar_trabajador_de_fabricacion_sqlalchemy_error
├── test_obtener_trabajadores_de_fabricacion_sqlalchemy_error
└── test_get_all_ordenes_fabricacion_sqlalchemy_error

TestTrackingRepositoryExportEdgeCases (6 tests)
├── test_get_data_for_export_with_completed_pasos
├── test_get_data_for_export_sqlalchemy_error
├── test_get_data_for_export_general_exception
├── test_get_data_for_export_with_incidencias
├── test_upsert_trabajo_log_with_incidencias
└── test_upsert_trabajo_log_error

TestTrackingRepositoryMapperEdgeCases (4 tests)
├── test_map_to_trabajo_log_dto_incidencias_exception
├── test_map_to_incidencia_log_dto_adjuntos_exception
├── test_map_to_incidencia_adjunto_dto_none
└── test_map_to_paso_trazabilidad_dto_none

TestTrackingRepositoryStatisticsEdgeCases (3 tests)
├── test_obtener_estadisticas_trabajador_sqlalchemy_error
├── test_obtener_estadisticas_fabricacion_sqlalchemy_error
└── test_get_trabajo_logs_por_trabajador_sqlalchemy_error
```

### Técnica: Mocking de Excepciones

```python
def test_pausar_trabajo_sqlalchemy_error(self, tracking_repo_test, seed_data):
    """Test SQLAlchemy error during pausar_trabajo."""
    job = tracking_repo_test.iniciar_trabajo(...)
    
    # Mock session.commit para lanzar excepción
    session = tracking_repo_test.session_factory()
    original_commit = session.commit
    session.commit = MagicMock(side_effect=SQLAlchemyError("Mock error"))
    
    result = tracking_repo_test.pausar_trabajo(job.qr_code, "Test")
    
    session.commit = original_commit
    assert result is False  # Verifica que el error se manejó
```

---

## 4. Resultados

| Métrica | Antes | Después |
|---------|-------|---------|
| Tests totales | 303 | 332 |
| Tests de Tracking | 43 | 72 (+29) |
| Errores | 0 | 0 |
| Warnings | 0 | 0 |

---

## 5. Verificación

```bash
python3 -m pytest tests/ -v --tb=short
============================= 332 passed in 2.01s ==============================
```

---

## 6. Notas Técnicas

- Los tests usan `MagicMock` para simular errores de base de datos
- Cada test restaura el comportamiento original después del mock
- Los tests de export se simplificaron para evitar dependencias en atributos que no existen en el modelo (`IncidenciaLog.created_at`)

---

> **Relación con otros documentos:** Este trabajo complementa la eliminación de `MaintenanceRepository` documentada en `Eliminacion_MaintenanceRepository.md`.
