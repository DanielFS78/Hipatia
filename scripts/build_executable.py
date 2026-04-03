"""
Script ejecutable (`build_executable`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import os
import shutil
import sys
import PyInstaller.__main__

def clean_build_environment():
    """Limpia compilaciones anteriores para evitar basura o conflictos."""
    print("[*] Limpiando directorios 'build' y 'dist'...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"    - {folder}/ eliminado.")

def build_hipatia():
    """Ejecuta PyInstaller de forma programática con toda la configuración de Hipatia."""
    print("\n[*] Configurando el motor de compilación para Hipatia...")
    
    # 1. El separador de rutas cambia según el Sistema Operativo (Windows es ';' y Mac/Linux es ':')
    sep = ';' if sys.platform == 'win32' else ':'
    
    # 2. Archivos de datos (Data Files)
    # ¡CRÍTICO!: Hipatia necesita la carpeta 'migrations' y 'alembic.ini' para crear 
    # la base de datos si el cliente la instala en un ordenador nuevo.
    # Usamos rutas relativas desde la raíz del proyecto
    datas = [
        f"migrations{sep}migrations",
        f"alembic.ini{sep}.",
        # f"ui/assets{sep}ui/assets", 
    ]
    
    # 3. Imports ocultos (Librerías que PyInstaller a veces no detecta automáticamente)
    hidden_imports = [
        'sqlalchemy',
        'alembic',
        'psycopg2',    # Para el modo Servidor (PostgreSQL)
        'reportlab',   # Generador de etiquetas APLI
        'qrcode',
        'cv2',         # OpenCV para las cámaras
        'sqlalchemy.ext.baked', # A veces necesario para SQLAlchemy
        'sqlalchemy.sql.default_comparator',
    ]
    
    # 4. Argumentos base de PyInstaller
    args = [
        'app.py',              # Punto de entrada de la aplicación
        '--name=Hipatia',      # Nombre del ejecutable final
        '--windowed',          # Modo interfaz gráfica
        '--noconfirm',         # Sobrescribe el output sin preguntar
        '--clean',             # Limpia la caché de PyInstaller
        '--log-level=WARN',    # Solo muestra warnings o errores en la consola
    ]
    
    # Inyectar datas
    for data in datas:
        args.extend(['--add-data', data])
        
    # Inyectar hidden imports
    for h_import in hidden_imports:
        args.extend(['--hidden-import', h_import])
        
    # Si tienes un icono corporativo (ej. un .ico en Windows), puedes añadirlo así:
    # args.extend(['--icon=ui/assets/icon.ico'])

    print("[*] Lanzando PyInstaller... (esto puede tardar un par de minutos)")
    # Ejecutamos PyInstaller llamando a su API interna
    try:
        PyInstaller.__main__.run(args)
        print("\n[+] ¡Compilación completada con éxito!")
        print("[+] Encontrarás el ejecutable de Hipatia dentro de la carpeta 'dist/'")
    except Exception as e:
        print(f"\n[!] Error durante la compilación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Asegurarnos de que estamos en la raíz del proyecto para que las rutas relativas funcionen
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    clean_build_environment()
    build_hipatia()
