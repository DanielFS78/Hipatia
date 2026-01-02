import ast
import os

def check_loose_mocks(directory):
    loose_mocks = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file.startswith("test_"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)
                        
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            # Check for MagicMock() or Mock() calls
                            if isinstance(node.func, ast.Name) and node.func.id in ["MagicMock", "Mock"]:
                                is_loose = True
                                for keyword in node.keywords:
                                    if keyword.arg == "spec" or keyword.arg == "spec_set":
                                        is_loose = False
                                        break
                                if is_loose:
                                    loose_mocks.append((path, node.lineno))
                            
                            # Check for attribute access like unittest.mock.MagicMock()
                            elif isinstance(node.func, ast.Attribute) and node.func.attr in ["MagicMock", "Mock"]:
                                is_loose = True
                                for keyword in node.keywords:
                                    if keyword.arg == "spec" or keyword.arg == "spec_set":
                                        is_loose = False
                                        break
                                if is_loose:
                                    loose_mocks.append((path, node.lineno))
                                    
                except Exception as e:
                    print(f"Error parsing {path}: {e}")
                    
    return loose_mocks

if __name__ == "__main__":
    results = check_loose_mocks("tests")
    print(f"Found {len(results)} instances of loose mocks.")
    
    # Bundle by file
    files_map = {}
    for path, lineno in results:
        if path not in files_map:
            files_map[path] = []
        files_map[path].append(lineno)
        
    print("\nSummary by File:")
    for path, lines in sorted(files_map.items()):
        print(f"{path}: {len(lines)} loose mocks")
