import os
import re

def analyze_directory(directory_path, search_patterns):
    results = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                for pattern_name, pattern_regex in search_patterns.items():
                    if re.search(pattern_regex, line):
                        if file_path not in results:
                            results[file_path] = []
                        results[file_path].append((i + 1, pattern_name, line.strip()))
    return results

def main():
    base_dir = "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
    search_patterns = {
        "get_all_materials": r"get_all_materials\(",
        "get_problematic_components_stats": r"get_problematic_components_stats\(",
        "material_access_by_index": r"\[\d\]" # Simple heuristic, manual review needed
    }
    
    print("Analyzing codebase for MaterialRepository usage...")
    matches = analyze_directory(base_dir, search_patterns)
    
    print(f"\nFound {len(matches)} files with potential impacts:\n")
    for file_path, hits in matches.items():
        print(f"File: {file_path}")
        for line_num, type, content in hits:
            print(f"  Line {line_num} [{type}]: {content}")
        print("-" * 40)

if __name__ == "__main__":
    main()
