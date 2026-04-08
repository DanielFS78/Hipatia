---
name: Preparación para Despliegue en Windows
description: Checklist y pasos para validar que Hipatia funcione correctamente en Windows 10/11 (plataforma de producción). Cubre DPI scaling, paths del sistema, cámaras, Qt plugins y empaquetado PyInstaller.
---

# Preparación para Despliegue en Windows — Proyecto Hipatia

> **Contexto:** El desarrollo se realiza en macOS (Apple Silicon). La plataforma de producción es **Windows 10/11** en PCs de fábrica.

## 1. Validación de UI y DPI Scaling

### El riesgo
Windows 10/11 usa escalado de pantalla (DPI scaling) por defecto al 125% o 150%. PyQt6 lo maneja con `Qt::HighDpiScaling`, pero widgets con tamaños fijos en píxeles pueden verse cortados o desalineados.

### Acciones
- [ ] Probar la aplicación en Windows con escalado al **100%**, **125%** y **150%**
- [ ] Verificar que `UIScaler` (si existe) no entra en bucle con el DPI scaling de Windows
- [ ] Confirmar que los `QScrollArea` aplicados en SettingsWidget y otros widgets pesados funcionan correctamente
- [ ] Verificar que las columnas de tablas con `setColumnWidth()` se ven bien en las 3 resoluciones
- [ ] Probar el Production Flow Canvas (editor visual) — es el widget más complejo

### Código a revisar
```python
# En app.py — _fix_qt_macos() solo se ejecuta en macOS.
# Verificar que Qt en Windows no necesita workarounds similares para plugins:
if sys.platform == "darwin":
    # ... solo macOS
```

## 2. Sistema de Archivos Windows

### El riesgo
Rutas con caracteres especiales (`C:\Users\José García\...`), separadores `\` vs `/`, y archivos bloqueados por antivirus.

### Acciones
- [ ] Verificar que `pathlib.Path` se usa en lugar de concatenación de strings para rutas
- [ ] Buscar uso de `/` hardcodeado en rutas: `grep -rn "os.path.join\|'/'" core/ controllers/ database/`
- [ ] Probar con un usuario Windows cuyo nombre contenga Ñ, acentos o espacios
- [ ] Verificar que `resource_path()` resuelve correctamente en Windows
- [ ] Comprobar que la BD SQLite se crea en la ruta correcta (`data/montaje.db`)

## 3. Sistema de Cámaras (OpenCV)

### El riesgo
En macOS, OpenCV usa **AVFoundation**. En Windows usa **DirectShow** o **MSMF**. El `CameraManager` debería funcionar, pero el backend cambia completamente.

### Acciones
- [ ] Conectar una webcam al PC Windows y verificar que `CameraManager` la detecta
- [ ] Verificar que el QR scanner funciona con la cámara de Windows
- [ ] Confirmar que los warnings de AVFoundation NO aparecen en Windows (son exclusivos de macOS)
- [ ] Si la cámara no funciona, verificar la instalación de `opencv-contrib-python` en Windows

## 4. Empaquetado con PyInstaller

### Objetivo
Generar un archivo `.exe` que funcione sin Python instalado.

### Pasos (canónicos en el repo)

En la raíz del proyecto, en un PC Windows:

```bat
build_windows.bat
```

Esto usa `hipatia.spec` (modo `onedir`), `requirements.txt` y `requirements-build.txt`. Detalle de rutas de datos y variables de entorno: `Documentacion/Despliegue_Windows.md`.

Comando equivalente manual:

```bash
pip install -r requirements.txt
pip install -r requirements-build.txt
pyinstaller hipatia.spec
```

Salida: `dist/Hipatia/Hipatia.exe`.

### Archivos a incluir en el empaquetado
- `templates/` — plantillas de documentos Word
- `config/config.ini` — configuración inicial
- `data/montaje.db` — base de datos vacía inicial
- `resources/` — recursos gráficos si existen
- `qr_codes/` — directorio para generar QR (crear vacío)

### Acciones
- [x] Crear un archivo `hipatia.spec` con la configuración de PyInstaller
- [x] Verificar que `resource_path()` funciona con PyInstaller (`sys._MEIPASS`); datos de usuario junto al `.exe` vía `core.paths.get_writable_app_root`
- [x] Crear un script `build_windows.bat` con los comandos de empaquetado
- [ ] Probar el `.exe` generado en un PC Windows limpio (sin Python)
- [ ] Opcional: crear un instalador con Inno Setup o NSIS para acceso directo

## 5. Configuración del Scheduler

### El riesgo
La hora de backup está hardcodeada en `startup_controller.py:173`:
```python
SCHEDULED_BACKUP_TIME = QTime(2, 0)  # 02:00 AM
```

### Acción
- [ ] Mover la hora de backup al `ConfigurationRepository` (BD)
- [ ] Añadir campo en `SettingsWidget` para configurar la hora
- [ ] Verificar que el `QTimer` funciona en Windows (comportamiento idéntico)

## 6. Checklist Final Pre-Producción

- [ ] Todos los flujos de negocio probados en Windows
- [ ] Login + RBAC funciona correctamente
- [ ] Importar/Exportar backups funciona en rutas Windows
- [ ] Sincronización USB funciona con rutas de unidades Windows (`D:\`, `E:\`)
- [ ] Sistema de etiquetado QR genera archivos correctamente
- [ ] El Health Check pre-arranque completa sin errores
- [ ] La terminal de log interna captura mensajes correctamente
- [ ] `generate_daniel_doc.py` genera documentación en Windows

## Estado

- [ ] UI validada en Windows 100%
- [ ] UI validada en Windows 125%
- [ ] UI validada en Windows 150%
- [x] Paths de datos escritura + frozen (repo: `core/paths`, `database/config`, `app`, health, backups)
- [ ] Cámaras validadas en Windows
- [ ] PyInstaller `.exe` generado y probado en PC limpio (artefactos: `hipatia.spec`, `build_windows.bat`)
- [x] Scheduler configurado desde BD (tarea A2 coordinador)
- [ ] Checklist final completado
