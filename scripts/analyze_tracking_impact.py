import os
import re

def search_usages(root_dir):
    methods_to_check = [
        "get_fabricaciones_por_trabajador",
        "obtener_o_crear_trabajo_log_por_qr",
        "obtener_trabajo_por_qr", 
        "obtener_trabajo_por_id",
        "get_paso_activo_por_trabajador",
        "get_ultimo_paso_para_qr",
        "iniciar_nuevo_paso",
        "finalizar_paso",
        "registrar_incidencia",
        "finalizar_trabajo_log",
        "get_trabajo_logs_por_trabajador"
    ]

    print(f"Scanning for usages of TrackingRepository methods in {root_dir}...")

    matches = {}

    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or ".git" in dirpath or "__pycache__" in dirpath:
            continue
            
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
                
            filepath = os.path.join(dirpath, filename)
            
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                for method in methods_to_check:
                    if method in line:
                        if filepath not in matches:
                            matches[filepath] = []
                        matches[filepath].append((i + 1, method, line.strip()))

    print("\nFound usages:")
    for filepath, hits in matches.items():
        print(f"\nFile: {filepath}")
        for line_num, method, content in hits:
            print(f"  Line {line_num}: [{method}] {content}")

if __name__ == "__main__":
    search_usages(".")
