@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist .venv-build-win (
  python -m venv .venv-build-win
)
call .venv-build-win\Scripts\activate.bat

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-build.txt

pyinstaller --noconfirm hipatia.spec

echo.
echo Salida en: dist\Hipatia\Hipatia.exe
endlocal
