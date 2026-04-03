"""
Script ejecutable (`generate_monolitos_finales`): automatización, informes o mantenimiento del proyecto (no forma parte del runtime de la app).
"""

import json
import os

def generate_markdown(data):
    lines = []
    lines.append("# Plan de Fragmentación: Monolitos Finales (Top 75 Archivos Pesados)\n")
    
    lines.append("Este documento contiene el listado exhaustivo de los 75 archivos más pesados y complejos del proyecto Hipatia que requieren fragmentación obligatoria. Se detallan las instrucciones paso a paso para desmantelar cada monolito, garantizando un tipado estricto (0 errores mypy), cobertura de tests del 100% sin omitidos ni advertencias, y documentación exhaustiva en español.\n")
    
    lines.append("## 🚨 Reglas Estrictas de Obligado Cumplimiento\n")
    lines.append("Al fragmentar cualquier archivo de esta lista, se debe asegurar lo siguiente:\n")
    
    lines.append("### 1. Tipado Estricto (Mypy)")
    lines.append("- **Cero errores**: No se permite introducir `type: ignore`. Todos los archivos resultantes deben pasar la comprobación de Mypy en modo estricto.")
    lines.append("- **Frontera UI/DTO sana**: No pasar diccionarios a la UI ni usar accesos por subíndice (`dict['key']`). Utilizar DTOs inmutables estrictamente definidos.\n")
    
    lines.append("### 2. Testing Exhaustivo y de Alta Calidad")
    lines.append("- **Cobertura 100%**: Cada nuevo archivo extraído debe tener su propio archivo de test asociado con cobertura total.")
    lines.append("- **Cero Errores/Warnings/Skips**: `pytest` debe estar en verde sin advertencias ni tests saltados.")
    lines.append("- **Mocks Estrictos Obligatorios**: Se prohíbe el uso de `MagicMock()` sin spec. Se debe usar obligatoriamente `create_autospec(Clase)`. Para `@patch`, es mandatorio pasar `autospec=True`.")
    lines.append("- **Aserciones de Interacción**: En pruebas de servicios y controladores, usar `assert_called_once_with` o similar para verificar la delegación.")
    lines.append("- **Validación DTO**: Usar `assert isinstance(result, XXXDTO)` para asegurar que las capas devuelven el tipo correcto.")
    lines.append("- **Tests por Capa**: ")
    lines.append("  - **UI (Headless)**: Instanciar el widget real. No simular el widget mismo. Usar `paintEvent` directo, NO usar `repaint()`. Testear visibilidad con `isHidden()`, no con `isVisible()`.")
    lines.append("  - **Capa Controladores**: Mockear `AppController` estricto, mockear el Model/View.")
    lines.append("  - **Capa Servicios/Core**: Mockear la persistencia (DatabaseManager).")
    lines.append("  - **Capa Repositorios**: Usar la fixture `repos`, sin mocks (SQLite real en memoria).\n")
    
    lines.append("### 3. Documentación Estándar")
    lines.append("- **Docstrings obligatorios**: Todos los módulos, clases y métodos deben estar documentados siguiendo el estilo Google Style en español.")
    lines.append("- **Script de Documentación**: Al terminar, ejecutar `python3 scripts/generate_daniel_doc.py` para asegurar que el archivo `Documentacion Daniel.md` incorpore las nuevas firmas y arquitecturas.\n")
    
    lines.append("---")
    lines.append("## 📜 Listado de los 75 Archivos a Fragmentar e Instrucciones\n")
    
    for idx, f in enumerate(data, start=1):
        path = f['path']
        loc = f['loc']
        metrics = f['metrics']
        
        nc = metrics.get('num_classes', 0)
        nm = metrics.get('num_methods', 0)
        nf = metrics.get('num_functions', 0)
        max_comp = metrics.get('max_complexity', 0)
        
        lines.append(f"### {idx}. `{path}`")
        lines.append(f"- **Métricas actuales**: {loc} LOC | {nc} Clases | {nm} Métodos | {nf} Funciones aisladas | Complejidad Máxima: {max_comp}")
        
        lines.append("**Explicación y Diagnóstico:**")
        if loc > 350:
            lines.append(f"El archivo es extremadamente extenso ({loc} líneas). Conforma un macro-módulo cuyo mantenimiento entorpece la legibilidad.")
        else:
            lines.append(f"El archivo presenta un acoplamiento sustancial. Es necesario refactorizarlo para aligerar su volumen ({loc} líneas).")
            
        if nc > 1:
            lines.append(f"Contiene {nc} clases definidas en el mismo archivo, rompiendo el principio de Responsabilidad Única (SRP).")
        if max_comp > 40:
            lines.append(f"Posee ramas de ejecución sumamente enrevesadas (complejidad máxima: {max_comp}). Requiere extracción de lógica condicional pesada.")
            
        lines.append("\n**Instrucciones de Fragmentación:**")
        
        if path.startswith("ui/"):
            lines.append("1. **Extracción de Delegados/Presenters**: Mover toda la lógica que no sea puramente wiring gráfico a un `XxxPresenter` o manager independiente (ej: `estado_manager`, `builder_manager`).")
            lines.append("2. **División de UI**: Si agrupa múltiples sub-widgets, separar en módulos de la carpeta de componentes (`ui/widgets/components/XxxWidget.py`).")
            lines.append("3. **Extracción de Utilidades**: Stylesheets, constantes de color y lógica geométrica (en canvas gui) deben ir a archivos de configuración o helpers.")
            if max_comp > 30:
                lines.append(f"4. **Refactorización de Pintado/Refresco**: Reducir la complejidad ciclomática de {max_comp} dividiendo los métodos pesados o `paintEvent` masivos en renders encadenados menores.")
        elif path.startswith("controllers/"):
            lines.append("1. **Extracción Sub-managers**: Desvincular lógicas dependientes separando el código en dominios de adaptadores/managers secundarios (`controllers/xxx/yyy_manager.py`).")
            lines.append("2. **Inyección de Dependencias Limpia**: Asegurarse de que el controlador no instancia repositorios propios sino que los consume desde un servicio o el model general inyectado.")
            lines.append("3. **Romper Ciclos Import**: Evitar in_degree/out_degree combinados hacia UI. Sustituir referencias circulares por protocolos (`core.interfaces.`).")
        else: # core o database
            lines.append("1. **Extracción de Lógica de Negocio**: Fragmentar calculadoras complejas y motores de simulación/procesado hacia sub-componentes (ej: `TimeCalculator`, `StrategyProcessor`).")
            lines.append("2. **Separación de Entidades**: En repositorios, garantizar que cada archivo atiende a una sola tabla (si hay persistencia combinada excesiva, dividir el repositorio).")
            
        if nc > 1:
            lines.append(f"4. **Divide y Vencerás**: Mover al menos {nc-1} de las clases alojadas a sus propios archivos `.py` dedicados.")
            
        lines.append(f"\n**Métricas Objetivo para esta tarea:**")
        lines.append(f"Debe resultar en Múltiples módulos < 200 LOC.")
        lines.append("Crear un nuevo archivo `test_xxx.py` para cada clase/módulo extraído. Refactorizar el actual `test_xxx.py`.\n")
        lines.append("---\n")
        
    return "\n".join(lines)

def main():
    root = "/Users/danielsanz/Library/Mobile Documents/com~apple~CloudDocs/Programacion/Calcular_tiempos_fabricacion"
    json_path = "/tmp/top_75_analysis.json"
    dest_dir = os.path.join(root, "documentacion")
    dest_path = os.path.join(dest_dir, "Monolitos_finales.md")
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    content = generate_markdown(data)
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"✅ Generado correctamente: {dest_path}")

if __name__ == "__main__":
    main()
