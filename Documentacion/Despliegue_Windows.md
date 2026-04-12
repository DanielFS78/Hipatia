# Despliegue en Windows (Hipatia)

## Requisitos

- Windows 10 u 11 (64 bits).
- Python 3.11+ solo en la **máquina de build**, no en los PCs de fábrica si se distribuye el `dist/` ya generado.
- Dependencias del sistema para Qt headless no aplican al `.exe` gráfico; en fábrica, resolución y DPI: ver checklist en [`.agents/skills/preparacion_windows/SKILL.md`](../.agents/skills/preparacion_windows/SKILL.md).

## Build (PyInstaller, modo `onedir`)

1. Clonar o copiar el repositorio en el PC Windows.
2. Desde la raíz del proyecto:

   ```bat
   build_windows.bat
   ```

   Crea `.venv-build-win`, instala `requirements.txt` + `requirements-build.txt` y ejecuta `pyinstaller hipatia.spec`.

3. Salida esperada: `dist\Hipatia\Hipatia.exe` junto con DLLs y carpeta `_internal` (o equivalente según versión de PyInstaller).

### Compilar solo desde la terminal (sin el `.bat`)

En la raíz del repo, con un venv ya activado y dependencias instaladas (`pip install -r requirements.txt` y `pip install -r requirements-build.txt`):

```bat
pyinstaller --noconfirm hipatia.spec
```

Equivalente multiplataforma (misma limpieza + spec que CI):

```bash
python scripts/build_executable.py
```

**No hace falta GitHub** para obtener un `.exe`: cualquier PC Windows con Python sirve como máquina de build.

### Si el error del `.exe` no coincide con el código del repo

PyInstaller incrusta el `app.py` que había en disco **en el momento del build**. Si el traceback menciona `app.py`, línea 29, y en tu `app.py` actual la línea relevante está mucho más abajo (por ejemplo el `import` de `AppController` cambió de sitio), el ejecutable **no se generó con esa versión del código**: vuelve a compilar tras `git pull` en la rama correcta, borra la carpeta antigua `dist\Hipatia` y prueba solo el nuevo `dist\Hipatia\Hipatia.exe`.

En GitHub Actions, el workflow **Build Windows EXE** solo hace push automático en `main`; en ejecución manual (*Run workflow*) elige la rama que contenga el commit deseado. En el log del job aparece el commit tras el checkout (ver paso «Show git revision» en el workflow).

Para depuración con consola, en `hipatia.spec` se puede poner `console=True` en `EXE` y volver a empaquetar.

## Datos de usuario junto al ejecutable

**Primer arranque (SQLite nueva):** si no hay ningún trabajador con `username` en la base, el ejecutable PyInstaller crea automáticamente el usuario **admin** / **admin** (rol Admin) y deja un aviso en el log. En desarrollo con `python app.py` sigue siendo válido `python scripts/maintenance/reset_admin.py` o la variable `HIPATIA_BOOTSTRAP_DEFAULT_ADMIN=1` para el mismo comportamiento sobre un fichero SQLite.

En binario congelado (`sys.frozen`):

- **SQLite** por defecto: `<carpeta_del_exe>\data\montaje.db`
- **Logs**: `<carpeta_del_exe>\logs\EvolucionTiempos.log`
- **Backups**: `<carpeta_del_exe>\backups` (u otras rutas según `DatabaseConfig` / env)
- **Configuración editable**: en el primer arranque se copia `config\config.ini` del bundle a `<carpeta_del_exe>\config\config.ini` para poder guardar el modo de conexión.

Variables de entorno opcionales (sin prefijo frozen): `DB_PATH`, `LOG_DIR`, `BACKUP_DIR`, `DB_TYPE`, etc. (ver [`database/config.py`](../database/config.py)).

## Recursos embebidos

Rutas de solo lectura (iconos, migraciones Alembic embebidas, `config` inicial) se resuelven con `resource_path()` → `_MEIPASS` en frozen. El archivo [`hipatia.spec`](../hipatia.spec) incluye `config/`, `resources/`, `migrations/` y `alembic.ini`.

## Validación manual pendiente (Fase C4–C6)

DPI 100/125/150 %, cámara/QR, checklist §6 de `preparacion_windows`, y prueba en PC **sin** Python. Marcar esas casillas en la skill tras ejecutarlas.

## C1 — Auditoría de rutas, DPI y cámara (abril 2026)

Comandos ejecutados en desarrollo (repetir en Windows tras cambios en rutas o empaquetado):

```bash
python scripts/windows_path_audit.py
pytest tests/unit
```

- **Informe de rutas:** [`reports/windows_path_audit.md`](../reports/windows_path_audit.md) (severidades P0/P1/P2). Última generación del script: sin hallazgos P0/P1 en el árbol auditado (`core/`, `controllers/`, `database/`, `features/`, `ui/`, `app.py`).
- **DPI:** [`app.py`](../app.py) aplica `QApplication.setHighDpiScaleFactorRoundingPolicy(PassThrough)` antes de crear `QApplication`. `core/utils/ui_scaler.py` documenta que usa geometría lógica Qt6; comprobar en 125 %/150 % que el QSS no queda desmesurado.
- **Cámara / OpenCV:** [`core/camera_manager/capture.py`](../core/camera_manager/capture.py) (`open_video_capture`, `open_video_capture_with_backends`) unifica backends con `CameraManager` y alternativas en Windows; [`controllers/hardware_controller.py`](../controllers/hardware_controller.py) abre la captura vía ese helper.

## Qt en Windows

[`app.py`](../app.py): `_fix_qt_macos()` solo se ejecuta en `darwin`. En Windows no se aplica ese workaround; el `onedir` debe incluir los plugins de PyQt6 que recoja PyInstaller. La política de redondeo High DPI anterior es independiente y aplica también en Windows.
