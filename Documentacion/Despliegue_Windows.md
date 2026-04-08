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

Para depuración con consola, en `hipatia.spec` se puede poner `console=True` en `EXE` y volver a empaquetar.

## Datos de usuario junto al ejecutable

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

## Qt en Windows

[`app.py`](../app.py): `_fix_qt_macos()` solo se ejecuta en `darwin`. En Windows no se aplica ese workaround; el `onedir` debe incluir los plugins de PyQt6 que recoja PyInstaller.
