import ast
import os
import re
from pathlib import Path

# Configuration
PROJECT_ROOT = Path('/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion')
CONTROLLER_PATH = PROJECT_ROOT / 'controllers/app_controller.py'
DOC_PATH = PROJECT_ROOT / 'Documentacion/Fase 3/Nomenclatura_AppController.md'

class AppControllerVisitor(ast.NodeVisitor):
    def __init__(self):
        self.methods = set()
        self.internal_calls = set()

    def visit_FunctionDef(self, node):
        if not node.name.startswith('__'):
            self.methods.add(node.name)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.internal_calls.add(node.attr)
        self.generic_visit(node)

def parse_documentation(doc_path):
    documented_methods = set()
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for method names in the markdown tables or lists
            # Assuming format like | `method_name` | ... or - `method_name`
            matches = re.findall(r'`([a-zA-Z0-9_]+)`', content)
            for m in matches:
                # Filter out obvious non-methods keywords if mixed in, but for now capture all code-quoted words
                if not m.startswith('__') and m != 'AppController' and m != 'self':
                     documented_methods.add(m)
    except Exception as e:
        print(f"Error parsing documentation: {e}")
    return documented_methods

def find_external_usage(project_root, methods, ignore_files):
    usage_counts = {m: 0 for m in methods}
    
    for root, dirs, files in os.walk(project_root):
        # Exclusions
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if 'venv' in dirs: dirs.remove('venv')
        if '.idea' in dirs: dirs.remove('.idea')
        
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = Path(root) / file
            if file_path == CONTROLLER_PATH: # Don't count definition as usage
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for method in methods:
                        # Simple regex check for method name usage
                        # We verify if it is preceded by . to indicate a method call or connections
                        if re.search(r'\.' + re.escape(method) + r'\b', content):
                            usage_counts[method] += 1
                        # Also check for text-based references (e.g. in signals connecting by name string, though less common now)
                        elif re.search(r'["\']' + re.escape(method) + r'["\']', content):
                            usage_counts[method] += 1
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
    return usage_counts

def analyze():
    print("Starting Analysis...")
    
    # 1. Parse AppController
    if not CONTROLLER_PATH.exists():
        print(f"Error: {CONTROLLER_PATH} does not exist.")
        return

    with open(CONTROLLER_PATH, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
        
    visitor = AppControllerVisitor()
    visitor.visit(tree)
    
    defined_methods = visitor.methods
    internal_calls = visitor.internal_calls
    
    print(f"Found {len(defined_methods)} methods in AppController.")
    
    # 2. Parse Documentation
    if DOC_PATH.exists():
        documented_methods = parse_documentation(DOC_PATH)
        print(f"Found {len(documented_methods)} methods in documentation.")
    else:
        print("Documentation not found. Skipping doc comparison.")
        documented_methods = set()

    # 3. Check External Usage
    print("Scanning for external usage...")
    external_usage = find_external_usage(PROJECT_ROOT, defined_methods, [CONTROLLER_PATH])
    
    # 4. Report Generation
    print("\n" + "="*50)
    print("ANALYSIS REPORT")
    print("="*50)
    
    potentially_dead = []
    undocumented = []
    
    for method in sorted(defined_methods):
        is_internal = method in internal_calls
        ext_count = external_usage[method]
        is_documented = method in documented_methods
        
        status = []
        if not is_internal and ext_count == 0:
            status.append("POTENTIALLY DEAD (0 calls)")
            potentially_dead.append(method)
        
        if not is_documented:
            status.append("UNDOCUMENTED")
            undocumented.append(method)
            
        if status:
            print(f"Method: {method}")
            print(f"  - Internal Calls: {'Yes' if is_internal else 'No'}")
            print(f"  - External Refs: {ext_count}")
            print(f"  - Documented: {'Yes' if is_documented else 'No'}")
            print(f"  - Status: {', '.join(status)}")
            print("-" * 30)

    print("\n" + "="*50)
    print("SUMMARY")
    print(f"Total Methods: {len(defined_methods)}")
    print(f"Potentially Dead Code Candidates: {len(potentially_dead)}")
    print(f"Undocumented Methods: {len(undocumented)}")
    print("="*50)
    
    if potentially_dead:
        print("\nCANDIDATES FOR REMOVAL:")
        for m in potentially_dead:
            print(f"- {m}")

if __name__ == "__main__":
    analyze()
