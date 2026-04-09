# Fase 3.7: Análisis de código muerto — paquete `ui/dialogs/`

> **Fecha de análisis:** 04 de April de 2026, 21:05
> **Generado por:** `scripts/detect_dead_code.py`

---

## 1. Resumen Ejecutivo

| Categoría | Cantidad | Porcentaje |
|-----------|----------|------------|
| **Métodos totales** | 322 | 100% |
| Usados externamente | 272 | 84% |
| Solo uso interno | 0 | 0% |
| Dunders (implícitos) | 50 | 15% |
| **⚠️ Potencialmente muertos** | 0 | 0% |

> **Líneas de código potencialmente eliminables:** ~0 líneas

---

## 2. Clases sin Uso Externo Detectado

> [!WARNING]
> Estas clases no tienen instanciaciones detectadas fuera de su fichero en `ui/dialogs/`.
> Podrían ser usadas dinámicamente o a través de imports indirectos.

| Clase | Líneas | Métodos |
|-------|--------|---------|
| `ui/dialogs/fabrication/bitacora_dialog.py::BitacoraEntryDTO` | 6 | 1 |

---

## 5. Métodos con Solo Uso Interno

Estos métodos solo tienen llamadas detectadas dentro del mismo módulo o sin referencias externas claras:

| Clase | Método | Líneas | Es Privado |
|-------|--------|--------|------------|

---

## 6. Recomendaciones

### Paso 1: Eliminar Código Muerto de Alta Confianza

### Paso 2: Verificar Manualmente Métodos de Media Confianza

Antes de eliminar métodos públicos, verificar:

1. ¿Son slots conectados via `signal.connect(self.metodo)`?
2. ¿Son llamados desde UI via eventos (`clicked`, `textChanged`, etc.)?
3. ¿Son parte de la API pública que devuelve datos al controlador?

### Paso 3: Ejecutar Tests Después de Cada Eliminación

```bash
source .venv/bin/activate && python -m pytest tests/ -v --tb=short
```

---

## 7. Eliminaciones en esta pasada

La heurística no detectó métodos sin referencias (ni privados de alta confianza ni públicos de media confianza). **0 eliminaciones** automáticas recomendadas.

*Documento generado automáticamente - 04/04/2026 21:05*