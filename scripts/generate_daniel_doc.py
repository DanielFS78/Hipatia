#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nombre del Módulo: generate_daniel_doc
Descripción: Genera documentación técnica completa de Hipatia en Markdown con
             diagramas Mermaid automáticos (ERD, arquitectura, árbol de carpetas,
             flujo de fabricación) extraídos del código real del proyecto.
             Incluye sección de Suite de Tests generada desde compliance_data.json.

             La narrativa embebida (p. ej. Fase 12C y CI) debe mantenerse alineada con
             `.github/workflows/ci.yml` y con las skills de Fase 12C al cambiar gates.
"""
import argparse
import os
import ast
import json
import datetime
import sys
from pathlib import Path
from typing import TypedDict

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "Documentacion"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "Documentacion Daniel.md"

INCLUDE_DIRS = ["controllers", "core", "database", "features", "ui", "scripts", "tools", "migrations"]
INCLUDE_ROOT_FILES = [
    "app.py",
    "analyze_ui.py",
    "generate_ui_report.py",
    "run_tests.py",
    "run_tests_safe.py",
]
INDEX_SCOPE_DIRS = ["controllers", "core", "database", "features", "ui", "scripts", "tools", "migrations"]
INDEX_MAX_CLASS_LINKS = 12  # Evita líneas descomunales en el índice.
IGNORE_NAMES = {
    "__pycache__", "tests", "Documentacion", "venv", ".git", ".agents",
    "data", "logs", "htmlcov", "test_reports", ".venv", "migrations",
    "migration", "Backup", "iteration_images", "qr_codes", "temp_chunks",
}
from doc_audit_common import FRASES_IGNORADAS, module_docstring_raw

# ---------------------------------------------------------------------------
# ESTILOS DE IMPRESIÓN (PDF)
# ---------------------------------------------------------------------------

PRINT_CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: DejaVu Sans, Arial, sans-serif; font-size: 10.5pt; line-height: 1.22; }
h1 { font-size: 20pt; margin: 0 0 10pt 0; }
h2 { font-size: 15pt; margin: 14pt 0 8pt 0; }
h3 { font-size: 12.5pt; margin: 10pt 0 6pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt 0; }
th, td { border: 1px solid #333; padding: 3pt 4pt; vertical-align: top; }
code { font-family: DejaVu Sans Mono, Menlo, monospace; font-size: 9.5pt; }
pre code { font-size: 9pt; }
.pagebreak { page-break-before: always; }
.keepwithnext { page-break-after: avoid; }
"""


# ---------------------------------------------------------------------------
# DIAGRAMAS MERMAID — generados estáticamente desde el conocimiento del modelo
# ---------------------------------------------------------------------------

MERMAID_ERD = '''```mermaid
erDiagram
    Producto {
        string codigo PK
        string descripcion
        string departamento
        int tipo_trabajador
        float tiempo_optimo
    }
    Subfabricacion {
        int id PK
        string producto_codigo FK
        string descripcion
        float tiempo
        int maquina_id FK
    }
    ProcesoMecanico {
        int id PK
        string producto_codigo FK
        string nombre
        float tiempo
    }
    ProductIteration {
        int id PK
        string producto_codigo FK
        datetime fecha_creacion
        string nombre_responsable
    }
    Material {
        int id PK
        string codigo_componente
    }
    Preproceso {
        int id PK
        string nombre
        float tiempo
        int tipo_trabajador
    }
    Fabricacion {
        int id PK
        string codigo
        string descripcion
    }
    Trabajador {
        int id PK
        string nombre_completo
        string username
        string role
        int tipo_trabajador
        bool activo
    }
    Maquina {
        int id PK
        string nombre
        string departamento
        bool activa
    }
    GrupoPreparacion {
        int id PK
        string nombre
        int maquina_id FK
        string producto_codigo FK
    }
    PreparacionPaso {
        int id PK
        int grupo_id FK
        string nombre
        float tiempo_fase
        bool es_diario
    }
    Pila {
        int id PK
        string nombre
        string producto_origen_codigo FK
    }
    Lote {
        int id PK
        string codigo
    }

    Producto ||--o{ Subfabricacion : "tiene"
    Producto ||--o{ ProcesoMecanico : "tiene"
    Producto ||--o{ ProductIteration : "tiene"
    Producto }o--o{ Material : "requiere"
    Producto }o--o{ Lote : "agrupa"
    Preproceso }o--o{ Material : "consume"
    Preproceso }o--o{ Fabricacion : "vincula"
    Fabricacion }o--o{ Trabajador : "asignados"
    Fabricacion }o--o{ Lote : "agrupa"
    Maquina ||--o{ GrupoPreparacion : "tiene"
    Maquina ||--o{ Subfabricacion : "ejecuta"
    GrupoPreparacion ||--o{ PreparacionPaso : "contiene"
    GrupoPreparacion }o--o| Producto : "especifico_de"
    Pila }o--o| Producto : "origen"
```'''

MERMAID_ARQUITECTURA = '''```mermaid
graph TD
    subgraph UI["🖥️ Capa UI (PyQt6)"]
        MV[MainView — único orquestador que retiene AppController]
        subgraph REP["Reportes: hijos sin AppController"]
            RW[ReportesWidget]
            SSW[SmartSearchWidget]
            OLW[OrderListWidget]
            RCH[ReportsChartsWidget]
            RW --> SSW
            RW --> OLW
            RW --> RCH
        end
        subgraph LEAF["Widgets hoja / diálogos: dependencias explícitas"]
            PMW[ProductMaterialsWidget]
            PIW[ProductIterationsWidget]
            PDD[ProductDetailsDialog]
            GDW[GestionDatosWidget pestañas vía DI]
            PSW[PrepStepsWidget señales / notificador]
            PMW --> PF[ProductFacade / servicios inyectados]
            PIW --> PF
            PDD --> PMW
            PDD --> PIW
        end
        subgraph WK["Vista trabajador"]
            WMW[WorkerMainWindow filas WorkerTaskListRowDTO]
        end
        WOTH[Otras páginas: Home Historial Fabricación Settings …]
        DLG[Otros diálogos DefineFlow Bitácora Prep …]
        MV --> RW
        MV --> WOTH
        MV --> DLG
        MV --> LEAF
        MV --> WK
    end

    subgraph CTRL["⚙️ Capa Controllers"]
        AC[AppController coordinador]
        ST[StartupController]
        SC[SessionController]
        LC[LoteController]
        FC[FabricacionController]
        PC[ProductController]
        WC[WorkerController]
        SIMC[SimulationController]
        RPC[ReportController]
        HRC[HistorialController + HistorialReportManager]
        BCIO[BackupControllerIOManager ZIP/TAR import export sync]
        AC --> SC
        AC --> LC
        AC --> FC
        AC --> PC
        AC --> WC
        AC --> SIMC
        AC --> RPC
        AC --> HRC
        AC -.->|copias y fusión BD| BCIO
        ST -.->|registro DI + wiring| AC
    end

    subgraph CORE["🧠 Capa Core: DI + servicios + fachada"]
        DI[DIContainer singleton]
        AM[AppModel fachada]
        RS[ReportService]
        WS[WorkerService]
        PS[ProductService]
        FS[FabricacionService]
        PLS[PilaService]
        LM[LabelManager]
        QR[QrGenerator]
        ENG[SimulationEngine]
        AC -->|self.container| DI
        DI -->|resolve| RS
        DI -->|resolve| PF
        AM --> WS
        AM --> PS
        AM --> FS
        AM --> PLS
        AM --> RS
        AM --> LM
        AM --> ENG
        LM --> QR
    end

    subgraph DB["🗄️ Capa Database"]
        DM[DatabaseManager]
        SYN[SyncService compare/apply SQLite]
        DM -.->|compare_with_db apply_sync_changes| SYN
        WR[WorkerRepository]
        PR[ProductRepository]
        IR[IterationRepository]
        TR[TrackingRepository]
        LR[LabelCounterRepo]
        RPR[ReportsRepository]
        DM --> WR
        DM --> PR
        DM --> IR
        DM --> TR
        DM --> LR
        DM --> RPR
    end

    subgraph SCR["🔧 Scripts mantenimiento y calidad"]
        BK[backup_database.py mypy estricto]
        RA[reset_admin.py mypy estricto]
        DC[detect_dead_code.py paquete ui/dialogs]
        TQA[test_quality_analyzer.py techo vs corregible]
        UDA[ui_dto_boundary_analyzer Fase 12C gate CI]
    end

    MV -->|set_controller| AC
    RW -->|.container → ReportService; si no, .model.report_service| AC
    SSW -->|search_reports_data| RS
    OLW -->|get_orders_for_product| RS
    RCH -->|stats y gráficas| RS
    WOTH -->|señales| AC
    DLG -->|señales| AC
    HRC -->|informes PDF iteraciones| IR
    FC -.->|delegación| FS
    SIMC -.->|motor| ENG
    CTRL --> CORE
    RS --> RPR
    CORE --> DB
    SCR -.->|no runtime app| DB
```'''

MERMAID_FLUJO_FABRICACION = '''```mermaid
sequenceDiagram
    actor U as Operario
    participant UI as UI (Widget)
    participant CTRL as FabricacionController
    participant SVC as FabricacionService
    participant DB as Repository
    participant QR as QR Generator

    U->>UI: Crear nueva Fabricación
    UI->>CTRL: on_create_fabricacion(datos)
    CTRL->>SVC: create_fabricacion(codigo, preprocesos)
    SVC->>DB: fabricacion_repo.add(fabricacion)
    DB-->>SVC: fabricacion_id
    SVC->>QR: generate_labels(fabricacion_id, unidades)
    QR-->>SVC: rutas_etiquetas[]
    SVC-->>CTRL: FabricacionDTO
    CTRL->>UI: refresh_view()
    UI-->>U: Etiquetas QR listas para imprimir

    U->>UI: Escanear QR (inicio tarea)
    UI->>CTRL: on_qr_scan(qr_data)
    CTRL->>SVC: registrar_inicio_trabajo(qr_data)
    SVC->>DB: tracking_repo.log_inicio(trabajador_id, fabricacion_id)
    DB-->>SVC: TrabajoLog creado
    SVC-->>CTRL: ok
    CTRL->>UI: actualizar_estado_operario()
```'''

MERMAID_FLUJO_SIMULACION = '''```mermaid
graph LR
    A[Pila de Trabajo] --> B[SimulationEngine]
    B --> C{Motor de Eventos}
    C --> D[Asignar Trabajador]
    C --> E[Asignar Máquina]
    D --> F[Calcular Tiempo]
    E --> F
    F --> G{¿Conflicto?}
    G -- Sí --> H[Replanificar]
    H --> C
    G -- No --> I[TimelineTask]
    I --> J[ResultsCompiler]
    J --> K[GanttWidget]
    J --> L[SimulationDTO]
```'''

MERMAID_FLUJO_IMPORT_BOM = '''```mermaid
flowchart TD
    excelFile["Archivo Excel A3RP"] --> excelAdapter["A3RPExcelAdapter.parse_file"]
    excelAdapter --> bomNodeTree["BOMNodeDTO tree"]
    bomNodeTree --> previewDialog["BOMImportPreviewDialog (supervisión)"]
    previewDialog --> bomService["BOMImportService.import_bom_tree"]
    bomService --> productRepo["ProductRepository (crear/actualizar productos)"]
    bomService --> materialRepo["MaterialRepository (crear/vincular materiales)"]
    bomService --> relationLayer["Relaciones BOM producto-material"]
```'''
 
MERMAID_SISTEMA_ETIQUETADO = '''```mermaid
graph TD
    subgraph SVC["📦 Core Services"]
        LM[LabelManager]
        QR[QrGenerator]
    end
    
    subgraph PORT["🔌 Ports (Interfaces)"]
        IDG[IDocumentGenerator]
    end
    
    subgraph ADAPT["🔌 Adapters (Infraestructure)"]
        DOCX[DocxGeneratorAdapter - Plantillas]
        APLI[Apli1861LabelGenerator - Dinámico A5]
    end
    
    LM --> IDG
    IDG <|-- DOCX
    IDG <|-- APLI
    LM --> QR
    APLI -->|Genera| DOC[Archivo .docx A5 / 66 etiquetas]
```'''

MERMAID_FLUJO_SYNC_USB = '''```mermaid
sequenceDiagram
    actor U as Usuario
    participant UI as SyncDialog
    participant SVC as SyncService
    participant FDB as SQLiteExterna
    participant LDB as SQLiteLocal

    U->>UI: Seleccionar archivo .db en USB
    UI->>SVC: compare_databases(foreign_db_path)
    SVC->>FDB: Leer tablas sincronizables
    SVC->>LDB: Leer tablas locales
    SVC-->>UI: DatabaseComparisonDTO
    UI-->>U: Mostrar diferencias por tabla

    U->>UI: Confirmar cambios seleccionados
    UI->>SVC: apply_changes(DatabaseComparisonDTO)
    SVC->>LDB: Upsert por SyncRecordDTO
    LDB-->>SVC: Commit
    SVC-->>UI: Total de cambios aplicados
    UI-->>U: Sincronizacion completada
```'''

MERMAID_FLUJO_LOGIN_AUTORIZACION = '''```mermaid
sequenceDiagram
    actor U as Usuario
    participant DLG as LoginDialog
    participant RL as RateLimiter
    participant WS as WorkerService
    participant AL as AuditLogger
    participant SS as SecurityService
    participant UI as MainView

    U->>DLG: Introduce credenciales
    DLG->>RL: is_blocked(username)
    alt Usuario bloqueado
        RL-->>DLG: True
        DLG->>AL: log_login(fallido, bloqueado)
        DLG-->>U: Mensaje de bloqueo
    else Usuario permitido
        RL-->>DLG: False
        DLG->>WS: authenticate_user(username, password)
        alt Credenciales validas
            WS-->>DLG: AuthResponseDTO
            DLG->>RL: check_and_record_attempt(success=True)
            DLG->>AL: log_login(exitoso)
            DLG->>SS: login_user(user_data)
            DLG->>UI: _update_ui_for_role()
            UI-->>U: Acceso habilitado por permisos
        else Credenciales invalidas
            WS-->>DLG: None
            DLG->>RL: check_and_record_attempt(success=False)
            DLG->>AL: log_login(fallido)
            DLG-->>U: Credenciales incorrectas
        end
    end
```'''


# ---------------------------------------------------------------------------
# GENERACIÓN DEL ÁRBOL DE CARPETAS (Mermaid)
# ---------------------------------------------------------------------------

def _build_folder_tree_mermaid() -> str:
    """Genera un diagrama Mermaid del árbol de carpetas principales."""
    lines = ["```mermaid", "graph TD"]
    lines.append('    ROOT["📁 Hipatia (raíz)"]')

    main_dirs = {
        "controllers": "⚙️ controllers",
        "core": "🧠 core",
        "database": "🗄️ database",
        "ui": "🖥️ ui",
        "features": "🔌 features",
        "scripts": "🛠️ scripts",
        "tests": "🧪 tests",
        "migrations": "📦 migrations",
    }

    for folder, label in main_dirs.items():
        folder_path = PROJECT_ROOT / folder
        if not folder_path.exists():
            continue
        node_id = folder.replace("/", "_")
        lines.append(f'    ROOT --> {node_id}["{label}"]')

        # Subcarpetas de primer nivel
        try:
            subdirs = sorted([
                d for d in folder_path.iterdir()
                if d.is_dir() and d.name not in IGNORE_NAMES and not d.name.startswith(".")
            ])
            for sub in subdirs[:6]:  # máximo 6 para no saturar el diagrama
                sub_id = f"{node_id}_{sub.name}"
                lines.append(f'    {node_id} --> {sub_id}["{sub.name}/"]')
        except PermissionError:
            pass

    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ÍNDICE COMPLETO (carpetas/subcarpetas/archivos/clases) + estado mypy
# ---------------------------------------------------------------------------

class FileIndexInfo(TypedDict):
    rel_path: str
    top_dir: str
    classes_all: list[str]
    classes_in_body: list[str]
    include_in_body: bool
    omit_reason: str
    mypy_strict_status: str
    mypy_reason: str


class DirIndexNode(TypedDict):
    subdirs: dict[str, "DirIndexNode"]
    files: list[FileIndexInfo]


def _path_to_module(rel_path: str) -> str:
    """
    Convierte una ruta tipo `core/services/foo.py` a módulo Python:
    `core.services.foo`. Si es `__init__.py`, se interpreta como paquete.
    """
    p = rel_path.replace("\\", "/")
    if not p.endswith(".py"):
        return p
    parts = p[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([x for x in parts if x])


def _load_mypy_disallow_untyped_defs() -> dict[str, bool]:
    """
    Devuelve un mapa {pattern: disallow_untyped_defs}.
    pattern es el nombre del módulo/patrón que sigue a `mypy-` en mypy.ini.
    """
    cache: dict[str, bool] | None = getattr(_load_mypy_disallow_untyped_defs, "_cache", None)
    if cache is not None:
        return cache

    mypy_ini = PROJECT_ROOT / "mypy.ini"
    default_disallow: bool = False
    patterns: dict[str, bool] = {}

    current_section: str | None = None
    for raw_line in mypy_ini.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            continue
        if current_section is None:
            continue
        if "=" not in line:
            continue
        key, value_raw = [x.strip() for x in line.split("=", 1)]
        value = value_raw.lower()
        bool_value = value in ("true", "1", "yes", "on")

        if current_section == "mypy" and key == "disallow_untyped_defs":
            default_disallow = bool_value
        if current_section.startswith("mypy-") and key == "disallow_untyped_defs":
            pattern_blob = current_section[len("mypy-") :]
            for pattern in [p.strip() for p in pattern_blob.split(",")]:
                if pattern:
                    patterns[pattern] = bool_value

    # Registrar patrones sin disallow explícito como default (config gradual)
    # para poder etiquetar sin ambigüedad.
    for dirname in INDEX_SCOPE_DIRS:
        # Si no hay sección explícita para scripts/tools/migrations, se usa default.
        patterns.setdefault(dirname + ".*", default_disallow)
    setattr(_load_mypy_disallow_untyped_defs, "_cache", patterns)
    return patterns


def _pattern_matches_module(pattern: str, module: str) -> bool:
    """
    Soporte simple de patrones tipo `core.*` y `controllers.foo`.
    """
    p = pattern.strip()
    if not p:
        return False
    if p.endswith(".*"):
        prefix = p[: -len(".*")]
        return module == prefix or module.startswith(prefix + ".")
    if "*" in p:
        # Patrón genérico (raramente usado aquí).
        parts = [x for x in p.split("*") if x]
        return all(part in module for part in parts)
    return module == p


def _mypy_strict_for_file(rel_path: str) -> tuple[str, str]:
    """
    Etiqueta + motivo (breve) de por qué el archivo no está al 100%.
    """
    module = _path_to_module(rel_path)
    patterns = _load_mypy_disallow_untyped_defs()

    best_match: str | None = None
    best_disallow: bool | None = None
    for pattern, disallow in patterns.items():
        if _pattern_matches_module(pattern, module):
            if best_match is None or len(pattern) > len(best_match):
                best_match = pattern
                best_disallow = disallow

    if best_disallow is True:
        return "Sí", "disallow_untyped_defs=True en mypy.ini (fase avanzada/módulo completado)."

    # Si no hay match con disallow=True, se considera parcial/gradual.
    # Explicación simple para no técnicos.
    return "Parcial", (
        "configuración gradual: disallow_untyped_defs=False en mypy.ini "
        "tipar todo al 100% no compensa el esfuerzo; se prioriza estabilidad."
    )


def _parse_all_classes(filepath: Path) -> list[str]:
    """
    Extrae solo nombres de clases (sin depender de docstrings).
    Esto permite que el índice no “omita” clases aunque luego no aparezcan en el cuerpo.
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except Exception:
        return []

    classes: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return classes


def _parse_all_symbols(filepath: Path) -> tuple[list[str], list[str]]:
    """
    Extrae nombres de clases y funciones top-level sin depender de docstrings.
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except Exception:
        return ([], [])

    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
    return (classes, functions)


def _has_ast_content(filepath: Path) -> bool:
    """
    Determina si un archivo Python contiene contenido parseable por AST.
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(tree.body)


def _is_package_init(filepath: Path) -> bool:
    """Indica si el archivo es un `__init__.py` de paquete."""
    return filepath.name == "__init__.py"


def _omit_reason_for_file(filepath: Path) -> str:
    if _is_package_init(filepath):
        return ""

    info = _parse_file(filepath)
    if "error" in info:
        return f"Error al parsear: {info['error']}"

    doc_valid = info["doc"].strip() not in FRASES_IGNORADAS
    if doc_valid:
        return ""
    if info["classes"] or info["functions"]:
        return ""
    classes_ast, functions_ast = _parse_all_symbols(filepath)
    if classes_ast or functions_ast:
        return ""
    if _has_ast_content(filepath):
        return ""
    return "Sin docstrings relevantes (por reglas de `FRASES_IGNORADAS`/docstrings vacíos)."


def _collect_index_tree() -> DirIndexNode:
    """
    Recorre todas las rutas `.py` bajo los directorios del alcance del índice
    y construye el árbol de carpetas/subcarpetas.
    """
    root: DirIndexNode = {"subdirs": {}, "files": []}

    # Archivos raíz (si existen y están dentro del alcance)
    for rel in INCLUDE_ROOT_FILES:
        fp = PROJECT_ROOT / rel
        if fp.exists() and fp.is_file():
            rel_path = rel.replace("\\", "/")
            include_in_body = _is_valid_file(fp)
            classes_all = _parse_all_classes(fp)
            classes_in_body = [c["name"] for c in _parse_file(fp).get("classes", [])]
            omit_reason = _omit_reason_for_file(fp) if not include_in_body else ""
            mypy_status, mypy_reason = _mypy_strict_for_file(rel_path)
            info: FileIndexInfo = {
                "rel_path": rel_path,
                "top_dir": "",
                "classes_all": classes_all,
                "classes_in_body": classes_in_body,
                "include_in_body": include_in_body,
                "omit_reason": omit_reason,
                "mypy_strict_status": mypy_status,
                "mypy_reason": mypy_reason,
            }
            root["files"].append(info)

    for top in INDEX_SCOPE_DIRS:
        top_path = PROJECT_ROOT / top
        if not top_path.exists():
            continue
        for root_dir, dirs, files in os.walk(top_path):
            # Filtrar subdirectorios ocultos/ignorados
            dirs[:] = [
                d
                for d in sorted(dirs)
                if d not in IGNORE_NAMES and not d.startswith(".") and d != "test_"
            ]
            for fname in sorted(files):
                if not fname.endswith(".py"):
                    continue
                if fname in IGNORE_NAMES:
                    continue
                full = Path(root_dir) / fname
                try:
                    rel_path = str(full.relative_to(PROJECT_ROOT)).replace("\\", "/")
                except ValueError:
                    continue
                # Saltar archivos dentro de paths que contengan piezas ignoradas.
                if any(f"/{x}/" in rel_path for x in IGNORE_NAMES):
                    continue

                include_in_body = _is_valid_file(full)
                classes_all = _parse_all_classes(full)
                parsed = _parse_file(full)
                classes_in_body = [c["name"] for c in parsed.get("classes", [])] if "error" not in parsed else []
                omit_reason = _omit_reason_for_file(full) if not include_in_body else ""

                mypy_status, mypy_reason = _mypy_strict_for_file(rel_path)
                info = {
                    "rel_path": rel_path,
                    "top_dir": top,
                    "classes_all": classes_all,
                    "classes_in_body": classes_in_body,
                    "include_in_body": include_in_body,
                    "omit_reason": omit_reason,
                    "mypy_strict_status": mypy_status,
                    "mypy_reason": mypy_reason,
                }

                parts = rel_path.split("/")
                # parts[0] es top_dir; el resto es ruta interna.
                internal_dir_parts = parts[1:-1]
                node = root
                for part in internal_dir_parts:
                    node = node["subdirs"].setdefault(part, {"subdirs": {}, "files": []})
                node["files"].append(info)

    # Normalizar orden en cada nodo (determinismo)
    def _normalize(n: DirIndexNode) -> None:
        n["files"].sort(key=lambda x: x["rel_path"])
        for k in list(n["subdirs"].keys()):
            _normalize(n["subdirs"][k])

    _normalize(root)
    return root


def _render_index_tree_md(node: DirIndexNode, page_map: dict[str, int] | None, depth: int = 0) -> str:
    """
    Renderiza el árbol como lista jerárquica (texto), incluyendo archivos y clases.
    """
    indent = "  " * depth
    lines: list[str] = []

    # Subcarpetas primero
    for sub in sorted(node["subdirs"].keys()):
        lines.append(f"{indent}- {sub}/")
        lines.append(_render_index_tree_md(node["subdirs"][sub], page_map, depth + 1))

    def _truncate(text: str, max_len: int = 110) -> str:
        t = " ".join(text.split())
        if len(t) <= max_len:
            return t
        return t[: max_len - 3] + "..."

    def _class_preview(classes: list[str]) -> str:
        if not classes:
            return ""
        if len(classes) <= INDEX_MAX_CLASS_LINKS:
            return ", ".join(classes)
        head = ", ".join(classes[:INDEX_MAX_CLASS_LINKS])
        return f"{head} (+{len(classes) - INDEX_MAX_CLASS_LINKS})"

    # Archivos en esta carpeta
    for f in node["files"]:
        rel = f["rel_path"]
        cls_preview = _class_preview(f["classes_all"])
        mypy_status = f["mypy_strict_status"]
        mypy_reason = _truncate(f["mypy_reason"], max_len=140)
        if f["include_in_body"]:
            if page_map is None:
                page_str = "p0000"
            else:
                page_str = f"p{page_map.get(rel, 0):04d}"
            extra = []
            if cls_preview:
                extra.append(f"clases: {cls_preview}")
            extra.append(f"Mypy: {mypy_status} ({mypy_reason})")
            lines.append(f"{indent}- `{rel}` → {page_str}" + (" | " + " | ".join(extra) if extra else ""))
        else:
            reason = f["omit_reason"] or "omitido por reglas de docstrings"
            extra = []
            if cls_preview:
                extra.append(f"clases: {cls_preview}")
            extra.append(f"Mypy: {mypy_status} ({mypy_reason})")
            lines.append(
                f"{indent}- `{rel}` → Omitido"
                + ((" | " + " | ".join(extra)) if extra else "")
                + f" ({_truncate(reason, max_len=80)})"
            )

    return "\n".join(lines)


def _folder_connections_mermaid(top_dir: str) -> str:
    """
    Diagrama Mermaid compacto de conexiones por capa.
    Basado en la arquitectura fija UI -> Controllers -> Core -> Database.
    """
    layer_graph = {
        "ui": (
            "graph TD\n"
            "  UI[UI (PyQt6)] -->|señales/slots| CTRL[Controllers]\n"
            "  CTRL -->|delegación| CORE[Core/Services]\n"
        ),
        "controllers": (
            "graph TD\n"
            "  DIC[DIContainer] --> CTRL[Controllers]\n"
            "  CTRL -->|orquestación| CORE[Core/Services]\n"
        ),
        "core": (
            "graph TD\n"
            "  CTRL[Controllers] -->|invocan| CORE[Core/Services]\n"
            "  CORE -->|persisten/consultan| DB[Database]\n"
        ),
        "database": (
            "graph TD\n"
            "  CORE[Core/Services] -->|repositorios| DB[Database/Repos]\n"
        ),
        "features": (
            "graph TD\n"
            "  CTRL[Controllers] -->|usa módulos| FEAT[Features]\n"
            "  FEAT -->|apoya| CORE[Core/Services]\n"
        ),
        "scripts": (
            "graph TD\n"
            "  SCRIPTS[Scripts/Tools de análisis] --> QA[Calidad/Docs/Test]\n"
        ),
        "tools": (
            "graph TD\n"
            "  TOOLS[Herramientas auxiliares] --> QA[Calidad/Docs/Test]\n"
        ),
        "migrations": (
            "graph TD\n"
            "  MIG[Schema de BD (Alembic)] --> DB[Database]\n"
        ),
    }
    body = layer_graph.get(top_dir, f"graph TD\n  X[{top_dir}] -->|depende| Y[Core]\n")
    return f"```mermaid\n{body}```"


def _index_stats(index_tree: DirIndexNode) -> dict[str, int]:
    """
    Calcula métricas rápidas para auditoría en papel:
    - total_py: total de .py considerados en el índice
    - included: incluidos en cuerpo
    - omitted: omitidos (docstrings/reglas)
    """
    total_py = 0
    included = 0
    omitted = 0

    def walk(n: DirIndexNode) -> None:
        nonlocal total_py, included, omitted
        total_py += len(n["files"])
        for f in n["files"]:
            if f["include_in_body"]:
                included += 1
            else:
                omitted += 1
        for sub in n["subdirs"].values():
            walk(sub)

    walk(index_tree)
    return {"total_py": total_py, "included": included, "omitted": omitted}


def _folder_stats(index_tree: DirIndexNode, top_dir: str) -> dict[str, int]:
    """
    Resumen por carpeta para portada de capítulo (modo papel).
    """
    included = 0
    omitted = 0
    total_py = 0
    total_classes = 0

    def walk(n: DirIndexNode) -> None:
        nonlocal included, omitted, total_py, total_classes
        for f in n["files"]:
            rel = f["rel_path"]
            if not rel.startswith(top_dir + "/"):
                continue
            total_py += 1
            total_classes += len(f["classes_all"])
            if f["include_in_body"]:
                included += 1
            else:
                omitted += 1
        for sub in n["subdirs"].values():
            walk(sub)

    walk(index_tree)
    return {
        "total_py": total_py,
        "included": included,
        "omitted": omitted,
        "total_classes": total_classes,
    }


def _split_markdown_into_sections(md_text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Particiona el markdown en secciones independientes para impresión:
    - prefix: portada + índice + secciones intro hasta antes de la referencia por carpetas/archivos
    - sections: lista ordenada de (kind:key, text)

    kind:
    - folder:<dirname>
    - file:<rel_path>
    """
    import re

    folder_marker = r"<div id='folder_([^']+)'>"
    file_marker = r"<div id='sec_([^']+)'>"

    # Encontrar todos los marcadores en orden
    matches: list[tuple[int, str, str]] = []
    for m in re.finditer(folder_marker, md_text):
        matches.append((m.start(), "folder", m.group(1)))
    for m in re.finditer(file_marker, md_text):
        matches.append((m.start(), "file", m.group(1)))
    matches.sort(key=lambda x: x[0])

    if not matches:
        return md_text, []

    prefix = md_text[: matches[0][0]]
    sections: list[tuple[str, str]] = []

    for i, (start, kind, key) in enumerate(matches):
        end = matches[i + 1][0] if i + 1 < len(matches) else len(md_text)
        seg = md_text[start:end]

        if kind == "file":
            # Intentar capturar rel_path desde el encabezado del archivo
            m_rel = re.search(r"###\s+📄\s+`([^`]+)`", seg)
            rel_path = m_rel.group(1) if m_rel else key
            sections.append((f"file:{rel_path}", seg))
        else:
            sections.append((f"folder:{key}", seg))

    return prefix, sections


def _measure_page_starts_for_file_sections(md_text: str) -> dict[str, int]:
    """
    Renderiza el markdown en secciones discretas para obtener:
    {rel_path: page_start}.
    """
    from markdown_pdf import MarkdownPdf, Section

    prefix, sections = _split_markdown_into_sections(md_text)
    page_map: dict[str, int] = {}
    n_sections = len(sections)
    print(
        f"  (Midiendo PDF: {n_sections} bloques de contenido; puede tardar varios minutos.)",
        flush=True,
    )

    pdf = MarkdownPdf(toc_level=2, optimize=True)

    current_page = 1
    prefix_section = Section(prefix, toc=False)
    pdf.add_section(prefix_section, user_css=PRINT_CSS)
    if getattr(prefix_section, "page_count", 0):
        current_page += int(prefix_section.page_count)

    for idx, (kind_key, seg) in enumerate(sections, start=1):
        if idx == 1 or idx % 25 == 0 or idx == n_sections:
            print(f"  … medición PDF bloque {idx}/{n_sections}", flush=True)
        s = Section(seg, toc=False)
        pdf.add_section(s, user_css=PRINT_CSS)
        if kind_key.startswith("file:"):
            rel = kind_key[len("file:") :]
            page_map[rel] = current_page
        if getattr(s, "page_count", 0):
            current_page += int(s.page_count)

    # No hace falta guardar; si `page_count` no se calculó, fallará en uso posterior.
    # Aun así, guardamos en un path temporal para forzar render si es necesario.
    try:
        tmp_pdf = str(OUTPUT_FILE).replace(".md", ".page_measure_tmp.pdf")
        pdf.save(tmp_pdf)
    except Exception:
        pass

    return page_map


def _render_pdf_from_markdown(md_text: str) -> None:
    """
    Convierte markdown -> PDF usando partición por archivo para estabilidad.
    """
    from markdown_pdf import MarkdownPdf, Section

    prefix, sections = _split_markdown_into_sections(md_text)
    n_sections = len(sections)
    print(f"  (Render PDF final: {n_sections} bloques.)", flush=True)

    pdf = MarkdownPdf(toc_level=2, optimize=True)
    prefix_section = Section(prefix, toc=False)
    pdf.add_section(prefix_section, user_css=PRINT_CSS)

    for idx, (_, seg) in enumerate(sections, start=1):
        if idx == 1 or idx % 25 == 0 or idx == n_sections:
            print(f"  … PDF final bloque {idx}/{n_sections}", flush=True)
        pdf.add_section(Section(seg, toc=False), user_css=PRINT_CSS)

    pdf_file = str(OUTPUT_FILE).replace(".md", ".pdf")
    pdf.save(pdf_file)


# ---------------------------------------------------------------------------
# EXTRACCIÓN AST
# ---------------------------------------------------------------------------

def _get_anchor(path: str) -> str:
    return "sec_" + path.replace("/", "_").replace(".", "_").replace(" ", "_")


def _get_technologies() -> list[dict]:
    req_file = PROJECT_ROOT / "requirements.txt"
    techs = []
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for sep in (">=", "==", "~="):
                if sep in line:
                    name, ver = line.split(sep, 1)
                    techs.append({"name": name.strip(), "version": ver.strip()})
                    break
            else:
                techs.append({"name": line, "version": "N/A"})
    return techs


def _parse_file(filepath: Path) -> dict:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": str(e), "doc": "", "classes": [], "functions": []}

    info: dict = {
        "doc": module_docstring_raw(tree),
        "classes": [],
        "functions": [],
    }

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node) or ""
            methods = []
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name in ("_setup_ui", "_connect_signals") or item.name.startswith("_on_"):
                    continue
                m_doc = (ast.get_docstring(item) or "").strip()
                if not m_doc or m_doc in FRASES_IGNORADAS:
                    continue
                if item.name == "__init__" and len(m_doc) < 15:
                    continue
                methods.append({"name": item.name, "doc": m_doc})

            if class_doc.strip() not in FRASES_IGNORADAS or methods:
                info["classes"].append({"name": node.name, "doc": class_doc, "methods": methods})

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f_doc = (ast.get_docstring(node) or "").strip()
            if f_doc and f_doc not in FRASES_IGNORADAS:
                info["functions"].append({"name": node.name, "doc": f_doc})

    return info


def _is_valid_file(filepath: Path) -> bool:
    if _is_package_init(filepath):
        return True

    info = _parse_file(filepath)
    if "error" in info and not info["classes"] and not info["functions"]:
        return False
    doc_valid = info["doc"].strip() not in FRASES_IGNORADAS
    if doc_valid or bool(info["classes"]) or bool(info["functions"]):
        return True

    # Fallback: incluir archivos con símbolos reales aunque aún no tengan docstrings.
    classes_ast, functions_ast = _parse_all_symbols(filepath)
    if classes_ast or functions_ast:
        return True

    # Último fallback: archivo parseable con contenido AST (incluye __init__.py no vacíos).
    return _has_ast_content(filepath)


def _collect_files() -> tuple[list[str], dict[str, list[str]]]:
    """Devuelve (root_files, {dirname: [rel_paths]})."""
    root_files = [
        f for f in INCLUDE_ROOT_FILES
        if (PROJECT_ROOT / f).exists() and _is_valid_file(PROJECT_ROOT / f)
    ]

    dir_files: dict[str, list[str]] = {}
    for dirname in INCLUDE_DIRS:
        dir_path = PROJECT_ROOT / dirname
        if not dir_path.exists():
            continue
        collected = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in sorted(dirs) if d not in IGNORE_NAMES]
            for fname in sorted(files):
                if fname.endswith(".py"):
                    full = Path(root) / fname
                    if _is_valid_file(full):
                        collected.append(str(full.relative_to(PROJECT_ROOT)))
        if collected:
            dir_files[dirname] = collected

    return root_files, dir_files


# ---------------------------------------------------------------------------
# ESCRITURA DEL MARKDOWN
# ---------------------------------------------------------------------------

def _write_file_section(md, filepath: Path) -> None:
    rel = str(filepath.relative_to(PROJECT_ROOT))
    anchor = _get_anchor(rel)
    info = _parse_file(filepath)
    classes_ast, functions_ast = _parse_all_symbols(filepath)
    has_ast_content = _has_ast_content(filepath)

    doc_valid = info["doc"].strip() not in FRASES_IGNORADAS
    if (
        not _is_package_init(filepath)
        and not doc_valid
        and not info["classes"]
        and not info["functions"]
        and not classes_ast
        and not functions_ast
        and not has_ast_content
    ):
        return

    md.write(f"<div id='{anchor}'>\n\n### 📄 `{rel}`\n\n</div>\n\n")

    if "error" in info:
        md.write(f"> ⚠️ Error al parsear: {info['error']}\n\n")
        return

    if doc_valid:
        md.write(f"{info['doc']}\n\n")

    for cls in info["classes"]:
        md.write(f"#### 🏛️ Clase `{cls['name']}`\n\n")
        if cls["doc"].strip() not in FRASES_IGNORADAS:
            md.write(f"{cls['doc'].strip()}\n\n")
            
        if cls["methods"]:
            md.write("**Métodos Principales:**\n\n")
            for m in cls["methods"]:
                # Imprimir el docstring completo del método preservando su formato multilinea
                # de forma amigable (sin tabulaciones masivas)
                lines = m['doc'].strip().splitlines()
                first_line = lines[0].strip()
                rest_lines = " ".join([l.strip() for l in lines[1:] if l.strip()])
                
                if rest_lines:
                    md.write(f"- `{m['name']}`: {first_line} {rest_lines}\n")
                else:
                    md.write(f"- `{m['name']}`: {first_line}\n")
            md.write("\n")

    if info["functions"]:
        for func in info["functions"]:
            lines = func['doc'].strip().splitlines()
            first_line = lines[0].strip()
            rest_lines = " ".join([l.strip() for l in lines[1:] if l.strip()])
            if rest_lines:
                md.write(f"- 🔧 `{func['name']}`: {first_line} {rest_lines}\n")
            else:
                md.write(f"- 🔧 `{func['name']}`: {first_line}\n")
        md.write("\n")

    if not doc_valid and not info["classes"] and not info["functions"]:
        if _is_package_init(filepath):
            md.write("> 📦 Archivo de paquete (`__init__.py`) incluido para trazabilidad del árbol de módulos.\n\n")
            md.write("---\n\n")
            return

        md.write("> ⚠️ Archivo incluido por detección AST: faltan docstrings descriptivos.\n\n")
        if classes_ast:
            md.write("**Clases detectadas (sin docstring detallado):**\n\n")
            for cls_name in classes_ast:
                md.write(f"- `{cls_name}`\n")
            md.write("\n")
        if functions_ast:
            md.write("**Funciones detectadas (sin docstring detallado):**\n\n")
            for func_name in functions_ast:
                md.write(f"- `{func_name}`\n")
            md.write("\n")
        if not classes_ast and not functions_ast:
            md.write(
                "**Contenido detectado:** módulo parseable con imports o configuración de paquete "
                "(sin clases/funciones documentables).\n\n"
            )

    md.write("---\n\n")


# ---------------------------------------------------------------------------
# SECCIÓN DE SUITE DE TESTS
# ---------------------------------------------------------------------------

# Decisiones técnicas por archivo — una línea explicando el patrón de mocking
# Clave: nombre del archivo (sin ruta). Valor: decisión técnica.
_TESTING_DECISIONS: dict[str, str] = {
    "test_label_manager.py": (
        "python-docx sin stubs → `sys.modules['docx'] = MagicMock()` en módulo; "
        "`create_autospec(logging.Logger)` para logger; `MagicMock(spec=['método'])` para QrGenerator"
    ),
    "test_calculation_controller_comprehensive.py": (
        "CalculateTimesWidget es Qt → `MagicMock()` con `__class__` forzado para `isinstance`; "
        "`@patch('QFileDialog')` y `@patch('builtins.open')` sin autospec (inevitables)"
    ),
    "test_schedule_controller_comprehensive.py": (
        "SettingsWidget es Qt → `MagicMock()` con `__class__` forzado; "
        "factories `_make_db/_make_view/_make_schedule_manager` con `spec=` mínimo; "
        "`@patch('AddBreakDialog')` y `@patch` de otras clases Qt sin autospec; "
        "ScheduleController con QDialog inline"
    ),
    "test_report_controller_comprehensive.py": (
        "Controlador con múltiples widgets Qt → `MagicMock()` para widgets; "
        "`create_autospec` para servicios de negocio puros"
    ),
    "test_session_controller_comprehensive.py": (
        "SessionController sin dependencias Qt directas → `create_autospec` para todos los servicios"
    ),
    "test_simulation_controller_comprehensive.py": (
        "SimulationEngine puro Python → `create_autospec(SimulationEngine)`; "
        "widgets de resultado Qt → `MagicMock()`"
    ),
    "test_simulation_events_comprehensive.py": (
        "Eventos de simulación sin UI → `create_autospec` para engine y repositorios"
    ),
    "test_startup_controller.py": (
        "StartupController orquesta arranque → `MagicMock(spec=[...])` para cada subsistema"
    ),
    "test_machines_widget.py": (
        "Widget Qt puro → todos los mocks son `MagicMock()` inevitables; "
        "sin lógica de negocio testeable con autospec"
    ),
    "test_machine_service.py": (
        "MachineService puro Python → `create_autospec(DatabaseManager, instance=True)` y "
        "`create_autospec(MachineRepository, instance=True)`"
    ),
    "test_worker_service.py": (
        "WorkerService puro Python → `create_autospec(DatabaseManager, instance=True)` y "
        "`create_autospec` en WorkerRepository, TrackingRepository, PreprocesoRepository, "
        "ProductRepository, PilaRepository"
    ),
    "test_detect_dead_code.py": (
        "Script de análisis estático sin Qt → `MethodExtractor`, `extract_package_classes`, "
        "`main` mockeado con `DIALOGS_PACKAGE` y paquete `ui/dialogs/`"
    ),
    "test_reports_repository.py": (
        "Repositorio SQLAlchemy → `create_autospec(Session)` para sesión de BD"
    ),
    "test_reports_infrastructure.py": (
        "Infraestructura de reportes → `create_autospec` para generadores; "
        "`@patch('builtins.open')` inevitable"
    ),
    "test_sync_service.py": (
        "SyncService con threading → `create_autospec` para repositorios; "
        "`MagicMock()` para objetos de hilo"
    ),
    "test_tracking_assignment_service.py": (
        "TrackingService puro Python → `create_autospec` para todos los repositorios"
    ),
    "test_security_improvements.py": (
        "Módulo de seguridad sin UI → `create_autospec` para hasher y validadores"
    ),
    "test_security_validation.py": (
        "Validación de seguridad pura → tests sin mocks, solo asserts sobre lógica"
    ),
    "test_smart_search.py": (
        "SmartSearch puro Python → `create_autospec` para índice; sin dependencias externas"
    ),
    "test_bitacora_dialog.py": (
        "FabricacionBitacoraDialog (Qt) → mock `controller.model.planning_facade` o `pila_service`; "
        "ya no se asertan llamadas a `AppModel.get_diario_bitacora`"
    ),
    "test_scheduler_logic.py": (
        "Lógica de planificación pura → tests sin mocks, solo DTOs reales"
    ),
    "test_backup_restore_dialog.py": (
        "Diálogo Qt → `MagicMock()` inevitable para todos los widgets del diálogo"
    ),
    "test_historial_report_manager_security.py": (
        "`require_permission` + `set_security_service` con `MagicMock(spec=SecurityService)`; sin Qt real"
    ),
    "test_temporal_storage.py": (
        "RegistroTemporal en archivo temporal real → un evento, `close()`, `consultar_eventos`; `cleanup()` en finally"
    ),
    "test_qr_scanner.py": (
        "QR Scanner con cámara → `@patch('cv2.VideoCapture')` sin autospec (C extension)"
    ),
    "test_tracking_dialogs.py": (
        "Diálogos de tracking Qt → `MagicMock()` para widgets; `create_autospec` para servicios"
    ),
    "test_tracking_exceptions.py": (
        "Excepciones de dominio puras → tests sin mocks, solo instanciación y asserts"
    ),
    "test_reportes_widget.py": (
        "ReportesWidget (hub Qt) → hub con `container` (DI) y/o `model.report_service`; "
        "`create_autospec(ReportService)`; sub-widgets solo `set_report_service`; sin `report_controller` en el widget"
    ),
    "test_report_sheets.py": (
        "Hojas de reporte con openpyxl → `create_autospec(Workbook)` para libro Excel"
    ),
    "test_report_strategy_comprehensive.py": (
        "Estrategias de reporte puras → `create_autospec` para cada estrategia concreta"
    ),
    "test_settings_widget.py": (
        "SettingsWidget Qt → `MagicMock()` inevitable; `create_autospec` para ScheduleController"
    ),
    "test_timeline_widget.py": (
        "TimelineWidget Qt puro → todos los mocks `MagicMock()` inevitables"
    ),
    "test_app_coverage.py": (
        "Cobertura de app.py → `@patch('QApplication')` sin autospec (Qt inevitable)"
    ),
    "test_security_phase2_integration.py": (
        "Test de integración de seguridad → usa BD real en memoria (SQLite); sin mocks de repositorio"
    ),
    # ── Fase A: archivos reescritos desde stub vacío (2026-03-15) ────────────
    "test_library_panel.py": (
        "TaskLibraryPanel es QWidget (PyQt6) → MagicMock() inevitable para dependencias visuales; "
        "update_visual_state() parcheado en tests que lo invocan indirectamente porque "
        "palette().color() devuelve mock en headless y setForeground() rechaza tipos no-QBrush"
    ),
    "test_fabrication_dialogs_coverage.py": (
        "CreateFabricacionDialog es QDialog (PyQt6) → MagicMock() inevitable para widgets; "
        "objetos Preproceso/Producto simulados con MagicMock() con id=int explícito porque "
        "CreateFabricacionPresenter usa sorted() sobre el atributo id y MagicMock no es comparable"
    ),
    "test_dialog_integration_smoke.py": (
        "CycleEndConfigDialog, ReassignmentRuleDialog, DefinirCantidadesDialog son QDialog (PyQt6) → "
        "MagicMock() inevitable para widgets; tareas del canvas como dicts Python puros (no mocks) "
        "porque los diálogos acceden a task['data']['id'] directamente"
    ),
    "test_reports_widgets.py": (
        "StatCard, OrderListWidget, SmartSearchWidget, ReportsChartsWidget son QWidget/QFrame (PyQt6) → "
        "MagicMock() inevitable; isVisible() False en headless; "
        "datos solo vía `report_service=` / `set_report_service` (`create_autospec(ReportService)`)"
    ),
    "test_canvas_widgets_coverage.py": (
        "FlowCardWidget y ProductionFlowCanvas (PyQt6): widgets reales en tests; "
        "MagicMock() solo en extremos de aristas en set_connections; ver testing_pyqt6_headless."
    ),
    "test_define_flow_dialog_edge.py": (
        "DefineProductionFlowDialog depende de DefineControlPanel (QWidget) → sustituido por "
        "FakeControlPanel(QWidget) real con señales como objetos FakeSignal (connect/emit vacíos) "
        "porque pyqtSignal no se puede instanciar fuera de QObject; "
        "DefineFlowPresenter sin `model`: tests usan `machine_service`/`preparation_service` en el mock del `controller.model`"
    ),
    "test_define_flow_presenter.py": (
        "DefineFlowPresenter lógica pura → `create_autospec(MachineService)` / mocks de "
        "`PreparationService` para consultas de dominio; ya no se asigna `presenter.model = AppModel`"
    ),
    # ── Fase A: archivos del Grupo A corregidos (2026-03-15) ─────────────────
    "test_pila_controller_comprehensive.py": (
        "PilaService/ProductService/FabricacionService → create_autospec(); "
        "repositorios con MagicMock(spec=[métodos mínimos]); schedule_manager.BREAKS=[] "
        "porque CalculadorDeTiempos itera sobre ese atributo en __init__; "
        "componentes Qt (QDialog, QListWidgetItem) → MagicMock(spec=['método'])"
    ),
    "test_historial_controller_comprehensive.py": (
        "Widgets Qt del historial → MagicMock() sin spec (inevitable en UI); "
        "`iteration_repo` y `product_repo` → `create_autospec(IterationRepository/ProductRepository, instance=True)`; "
        "assert call_count antes de assert_called_once_with()"
    ),
    "test_ui_controller_comprehensive.py": (
        "HomeWidget y widgets de progreso son Qt → MagicMock() sin spec inevitable; "
        "llamadas asíncronas verificadas con assert call_count antes de assert_called_once_with(); "
        "no se usa autospec en clases Qt"
    ),
    "test_worker_main_window.py": (
        "WorkerMainWindow es QMainWindow (PyQt6) → MagicMock() inevitable para widgets internos; "
        "usuario activo simulado con MagicMock() con atributos id/nombre/rol explícitos; "
        "WorkerDTO importado para isinstance() en código bajo test"
    ),
    "test_machine_controller_comprehensive.py": (
        "MachinesWidget y GestionDatosWidget son Qt → MagicMock() sin spec; "
        "servicio de seguridad parcheado globalmente con autouse=True; "
        "MachineDTO usado en tests que verifican tipo de objetos pasados al repositorio"
    ),
    "test_lote_controller_comprehensive.py": (
        "Componentes Qt (QTableWidgetItem, QSpinBox, pyqtSignal) parcheados antes de importar "
        "LoteController para evitar SIGABRT en headless; "
        "ProductDTO usado en tests que verifican tipo de objetos devueltos"
    ),
    "test_lote_manager_isolated.py": (
        "create_autospec() con IPilaDatabase/IProductService/IFabricacionService para garantizar "
        "que las llamadas respetan las firmas de los protocolos; "
        "QListWidget/QListWidgetItem importados para isinstance() pero instancias con MagicMock()"
    ),
    "test_pila_manager_isolated.py": (
        "create_autospec() con IPilaService para garantizar interfaz; "
        "QDialog importado para isinstance() pero instancias con MagicMock(); "
        "no se usa autospec en clases Qt"
    ),
    "test_navigation_controller_comprehensive.py": (
        "Widgets de destino (CalculateTimesWidget, DefinirLoteWidget, GestionDatosWidget) "
        "importados para isinstance() pero instancias con MagicMock() sin spec; "
        "autospec=True solo en funciones Python puras, nunca en clases Qt"
    ),
    "test_gestion_datos_widget.py": (
        "GestionDatosWidget instancia pestañas vía DI → monkeypatch ``DIContainer.get_instance`` "
        "con mock ``resolve``/``is_registered``; sin ``AppController`` en el contenedor"
    ),
    "test_prep_steps_widget.py": (
        "PrepStepsWidget: avisos de validación con ``validation_warning`` (pyqtSignal); "
        "qtbot.waitSignal en tests de campos vacíos / tiempo inválido"
    ),
    "test_product_dialogs_coverage.py": (
        "Diálogos Qt heredan de QDialog → MagicMock() inevitable para widgets internos; "
        "ProductDetailsDialog usa ``ProductController`` mock con ``product_facade``, "
        "``material_service``, ``product_service``, ``db``, ``app.file_controller``; "
        "ProductDTO/ProductIterationDTO/MaterialDTO con atributos explícitos; PropertyMock donde haga falta"
    ),
    "test_product_controller_preprocesos.py": (
        "ProductController depende de AppController → MagicMock() estándar; "
        "QDialog/QMessageBox parcheados con patch() para interceptar creación sin instanciar; "
        "Permission usado para verificar llamadas al servicio de seguridad"
    ),
    "test_product_controller_v2_comprehensive.py": (
        "mock_app con create_autospec(AppController) y servicios/repos; "
        "PreprocesoDialog se aserta con material_port=controller (puerto de materiales), no controller="
    ),
    "test_dashboard_widget.py": (
        "DummyChartView(QWidget) en patch de QChartView; Dashboard sin set_controller ni hub — "
        "solo update_* desde UIController"
    ),
    "test_app_startup_integration.py": (
        "MainView + init_ui: sustituto de QChartView como QWidget real (_FakeChartView) para addWidget; "
        "GestionDatosWidget verificado por pestañas DI, sin atributo controller"
    ),
    "test_widgets_integration.py": (
        "WorkersWidget() tras registrar WorkerController en DIContainer; señales a management_manager"
    ),
}


def _load_compliance_data() -> list[dict]:
    """
    Carga los datos de compliance desde test_reports/compliance_data.json.

    Si el archivo no existe, devuelve lista vacía (la sección se omite).
    """
    compliance_path = PROJECT_ROOT / "test_reports" / "compliance_data.json"
    if not compliance_path.exists():
        return []
    try:
        return json.loads(compliance_path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_testing_section(md, compliance_data: list[dict]) -> None:
    """
    Escribe la sección 'Suite de Tests' en el documento Markdown.

    Incluye:
    - Filosofía general de testing del proyecto
    - Explicación del sistema de scoring y techo real
    - Tabla resumen global (score absoluto, techo, estado)
    - Tabla por archivo con decisión técnica de mocking
    """
    md.write("## Suite de Tests\n\n")
    md.write(
        "> Sección generada automáticamente desde `test_reports/compliance_data.json`. "
        "Ejecutar `python3 scripts/test_quality_analyzer.py` para actualizar.\n\n"
    )

    # ── Filosofía ────────────────────────────────────────────────────────────
    md.write("### Filosofía de Testing\n\n")
    md.write(
        "La suite de tests de Hipatia sigue un modelo de **calidad verificable** "
        "con tres principios fundamentales:\n\n"
    )
    md.write(
        "1. **Mocks estrictos por defecto** — `create_autospec()` o `MagicMock(spec=...)` "
        "para cualquier dependencia que tenga stubs de tipo disponibles. "
        "Esto garantiza que los tests fallen si la interfaz real cambia.\n\n"
    )
    md.write(
        "2. **Excepciones documentadas** — PyQt6 y python-docx no tienen stubs de tipo "
        "completos: en **widgets y diálogos Qt** suele usarse `MagicMock()` sin spec; el analizador "
        "solo trata como **inevitables** los mocks sueltos en líneas con indicios de widget Qt (heurística). "
        "Los **repositorios y servicios Python del proyecto** no entran en esa excepción: deben usar "
        "`create_autospec(ClaseReal, instance=True)` o `MagicMock(spec=[...])` acotado cuando proceda "
        "(ver `.agents/skills/testing_fixtures_y_mocks/SKILL.md`).\n\n"
    )
    md.write(
        "3. **Verificación de interacciones explícita** — En controladores y servicios, "
        "cada test que verifica una llamada usa `assert x.call_count == N` antes de "
        "`assert_called_once_with(...)`. Esto evita el antipatrón de `assert_called_once()` "
        "sin argumentos, que no verifica qué se pasó.\n\n"
    )
    md.write(
        "4. **Asserts observables por defecto** — `assert True` se considera un **smoke test** "
        "y solo se permite como último recurso, siempre documentado como "
        "`assert True  # smoke_test: ...`. Si existe un observable (estado/retorno/interacción), "
        "se prefiere ese assert.\n\n"
    )
    md.write(
        "El marcador `pytestmark = pytest.mark.unit` se aplica a nivel de módulo "
        "en todos los archivos de tests unitarios, permitiendo ejecutar subconjuntos "
        "con `pytest -m unit`.\n\n"
    )

    # ── Sistema de scoring ───────────────────────────────────────────────────
    md.write("### Sistema de Scoring y Techo Real\n\n")
    md.write(
        "El analizador `scripts/test_quality_analyzer.py` asigna un **score absoluto** (0-100) "
        "basado en criterios objetivos, y calcula un **score techo** que descuenta las "
        "penalizaciones inevitables por dependencias externas sin stubs.\n\n"
    )
    md.write("| Criterio | Puntos | Notas |\n")
    md.write("|---|---|---|\n")
    md.write("| Tiene `pytestmark` o `@pytest.mark.*` | +25 | Obligatorio en todos los archivos |\n")
    md.write("| Usa `create_autospec` / `spec=` | +20 | Para dependencias con stubs disponibles |\n")
    md.write("| Verifica interacciones (`assert_called*`) | +15 | Obligatorio en controllers/services |\n")
    md.write("| Valida DTOs con `isinstance(..., XxxDTO)` | +15 | Para tests de capa de servicio |\n")
    md.write("| Todos los `@patch` tienen `autospec=True` | +15 | Excepto builtins/Qt/OS |\n")
    md.write("| Tiene docstrings en clases y métodos | +10 | |\n")
    md.write("| `MagicMock()` sin spec (por mock) | -5 (máx -30) | Inevitable si usa PyQt6/docx |\n")
    md.write("| `@patch` sin autospec (por patch) | -3 (máx -20) | Inevitable para builtins/Qt/OS |\n")
    md.write("| Test sin ningún `assert` (por test) | -5 (máx -20) | Siempre corregible |\n")
    md.write("| `assert True` trivial sin justificar | -1 (máx -10) | Solo permitido con `# smoke_test:` |\n")
    md.write("| `assert_called_once()` sin args | -3 (máx -15) | Antipatrón: no verifica argumentos |\n\n")

    md.write(
        "Cuando un archivo alcanza su **techo real** (`score optimizado = techo`), "
        "el analizador lo marca con ✅ y explica la razón (p. ej. importa PyQt6 y el techo solo perdona "
        "parte de los `MagicMock()` sueltos en contexto de widgets). "
        "El estado del archivo (`Actualizado / En Progreso / Legacy`) se calcula "
        "sobre el score techo, no el absoluto, para no penalizar lo ya optimizado.\n\n"
    )

    if not compliance_data:
        md.write(
            "> ⚠️ No se encontró `test_reports/compliance_data.json`. "
            "Ejecuta `python3 scripts/test_quality_analyzer.py` para generar los datos.\n\n"
        )
        md.write("---\n\n")
        return

    # ── Resumen global ───────────────────────────────────────────────────────
    non_infra = [r for r in compliance_data if not r.get("is_infra", False)]
    total = len(compliance_data)
    updated = sum(1 for r in compliance_data if r.get("status") == "Actualizado")
    in_progress = sum(1 for r in compliance_data if r.get("status") == "En Progreso")
    legacy = sum(1 for r in compliance_data if r.get("status") == "Legacy / Pendiente")
    avg_score = sum(r.get("score", 0) for r in compliance_data) / total if total else 0
    avg_ceiling = sum(r.get("ceiling_score", r.get("score", 0)) for r in compliance_data) / total if total else 0
    at_ceiling_count = sum(1 for r in compliance_data if r.get("at_ceiling", False))

    md.write("### Resumen Global\n\n")
    md.write("| Métrica | Valor |\n")
    md.write("|---|---|\n")
    md.write(f"| Archivos analizados | {total} |\n")
    md.write(f"| Actualizados (≥80 techo) | {updated} |\n")
    md.write(f"| En Progreso (50-79) | {in_progress} |\n")
    md.write(f"| Legacy / Pendiente (<50) | {legacy} |\n")
    md.write(f"| Score absoluto medio | {avg_score:.1f}/100 |\n")
    md.write(f"| Score optimizado medio | {avg_ceiling:.1f}/100 |\n")
    md.write(f"| Archivos en su techo real | {at_ceiling_count}/{total} |\n\n")

    # ── Tabla por archivo ────────────────────────────────────────────────────
    md.write("### Detalle por Archivo\n\n")
    md.write(
        "Columnas: **Score** = score absoluto · **Techo** = score máximo alcanzable · "
        "**✅** = en techo real · **Estado** = calculado sobre techo\n\n"
    )
    md.write("| Archivo | Score | Techo | Estado | Decisión técnica de mocking |\n")
    md.write("|---|---|---|---|---|\n")

    for r in sorted(compliance_data, key=lambda x: x.get("ceiling_score", 0), reverse=True):
        name = r.get("name", "")
        score = r.get("score", 0)
        ceiling = r.get("ceiling_score", score)
        at_ceil = "✅" if r.get("at_ceiling", False) else ""
        status = r.get("status", "")
        decision = _TESTING_DECISIONS.get(name, "—")
        # Truncar decisión larga para que la tabla sea legible
        if len(decision) > 120:
            decision = decision[:117] + "..."
        md.write(f"| `{name}` | {score} | {ceiling} {at_ceil} | {status} | {decision} |\n")

    md.write("\n---\n\n")


def generate_markdown(page_map: dict[str, int] | None = None) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    phase = "índice con páginas reales" if page_map else "índice placeholder (p0000)"
    print(f"→ Generando Markdown ({phase})…", flush=True)
    root_files, dir_files = _collect_files()
    n_ref = len(root_files) + sum(len(v) for v in dir_files.values())
    print(f"  Referencia de código: {n_ref} archivos a volcar en el cuerpo.", flush=True)
    # Índice completo (incluye omitidos) para facilitar verificación visual.
    print("  Construyendo árbol de índice…", flush=True)
    index_tree = _collect_index_tree()
    stats = _index_stats(index_tree)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as md:

        # ── PORTADA ──────────────────────────────────────────────────────────
        md.write(f"# Documentación Técnica: Hipatia\n\n")
        md.write(f"> Generado automáticamente el {now}\n\n")
        md.write("---\n\n")

        # ── ÍNDICE — generado automáticamente por markdown_pdf con toc=True ──
        # No escribir índice manual: markdown_pdf lo construye desde los ## headings

        md.write("## Índice de Código (completo y verificable)\n\n")
        md.write("### Resumen rápido (para auditoría en papel)\n\n")
        md.write("| Métrica | Valor |\n")
        md.write("|---|---:|\n")
        md.write(f"| Archivos `.py` listados en el índice | {stats['total_py']} |\n")
        md.write(f"| Incluidos en el cuerpo (tienen bloque en el PDF) | {stats['included']} |\n")
        md.write(f"| Omitidos (reglas de docstrings/otros) | {stats['omitted']} |\n\n")
        md.write(
            "Leyenda:\n"
            "- `pNNNN`: página exacta donde empieza el bloque del archivo en el PDF (placeholder `p0000` si aún no se calculó).\n"
            "- `Omitido`: el archivo no se incluye en el cuerpo por reglas de docstrings (ver `FRASES_IGNORADAS`).\n"
            "- `FRASES_IGNORADAS`: Conjunto de textos genéricos (ej. 'Sin descripción disponible') o docstrings vacíos. El script ignora intencionalmente los módulos con estas descripciones porque no aportan información útil.\n"
            "- `Mypy Sí`: tipado estricto aplicado a ese módulo en `mypy.ini`.\n"
            "- `Mypy Parcial`: el proyecto usa una configuración gradual allí; se prioriza estabilidad/coste de esfuerzo.\n\n"
        )
        md.write(_render_index_tree_md(index_tree, page_map) + "\n\n")
        md.write("---\n\n")

        # ── 1. VISIÓN GENERAL ────────────────────────────────────────────────
        md.write("## Vision General\n\n")
        md.write(
            "Hipatia es un sistema industrial para la **Simulación y Optimización de Tiempos de Fabricación**. "
            "Permite gestionar flujos de trabajo complejos, planificar cargas de operarios y realizar "
            "trazabilidad en tiempo real mediante **códigos QR**.\n\n"
        )
        md.write("Funcionalidades principales:\n\n")
        md.write("- Cálculo de tiempos de fabricación por procesos mecánicos y manuales\n")
        md.write("- Trazabilidad completa de componentes y órdenes de fabricación\n")
        md.write("- Asignación inteligente de trabajadores y máquinas\n")
        md.write("- Motor de simulación de escenarios de producción\n")
        md.write("- Gestión de backups, auditoría y seguridad por roles\n\n")
        md.write("### Mantenimiento industrial, calidad de tests y análisis estático\n\n")
        md.write(
            "Estado documentado del repo (actualizado en la generación de esta documentación):\n\n"
        )
        md.write(
            "- **`scripts/maintenance/`** — `backup_database.py` y `reset_admin.py` con **tipado estricto** "
            "según `[mypy-scripts.maintenance.*]` en `mypy.ini` (`ignore_errors = False`, "
            "`disallow_untyped_defs = True`). El reset de admin usa `DatabaseConfig` y raíz del proyecto "
            "vía `Path(__file__).resolve().parents[2]` para imports fiables.\n"
        )
        md.write(
            "- **`scripts/detect_dead_code.py`** — Analiza el **paquete** `ui/dialogs/` (no el monolito antiguo), "
            "genera `Documentacion/Analisis_Codigo_Muerto_ui_dialogs.md` con claves `ruta.py::Clase` y sección "
            "de **0 eliminaciones** cuando la heurística no marca métodos muertos (revisión manual obligatoria "
            "antes de borrar código).\n"
        )
        md.write(
            "- **`scripts/test_quality_analyzer.py`** — Distingue penalizaciones **inevitables** (p. ej. "
            "`MagicMock()` en la misma línea que nombres típicos de **widgets Qt**) de penalizaciones "
            "**corregibles**; en archivos con PyQt6, los **repositorios y servicios del proyecto** siguen "
            "pudiendo (y deben) usar `create_autospec` donde aplique (ver skill `testing_fixtures_y_mocks`).\n"
        )
        md.write(
            "- **Tests de servicios** — Ejemplos endurecidos: `test_worker_service.py` y `test_machine_service.py` "
            "usan `create_autospec(DatabaseManager, instance=True)` y `create_autospec` de los repositorios reales; "
            "`test_historial_controller_comprehensive.py` usa `create_autospec` en `IterationRepository` y "
            "`ProductRepository` donde corresponde.\n"
        )
        md.write(
            "- **Historial PDF** — `HistorialReportManager` obtiene el historial de iteraciones vía "
            "`db.iteration_repo.get_product_iterations` (alineado con `IterationRepository` y con "
            "`interaction_manager`).\n\n"
        )
        md.write("---\n\n")

        # ── 2. ARQUITECTURA ──────────────────────────────────────────────────
        md.write("## Arquitectura del Sistema\n\n")
        md.write(
            "Patrón **MVC modernizado** con inyección de dependencias vía `DIContainer`. "
            "Cada capa tiene responsabilidad única y se comunica hacia abajo:\n\n"
        )
        md.write("| Capa | Tecnología | Responsabilidad |\n")
        md.write("|---|---|---|\n")
        md.write("| UI | PyQt6 | Widgets, diálogos, señales/slots |\n")
        md.write("| Controllers | Python | Orquestación, delegación, manejo de eventos UI |\n")
        md.write("| Services | Python | Lógica de negocio pura, sin dependencia de UI |\n")
        md.write("| Core / AppModel | Python | Fachada que expone servicios a los controllers |\n")
        md.write("| Database | SQLAlchemy 2.0 | Repositorios, modelos ORM, migraciones Alembic |\n\n")
        md.write("### Regla de Arquitectura: Fase 12C (DTO-First)\n\n")
        md.write(
            "La Fase 12C define una frontera estricta entre UI y dominio:\n\n"
            "- La UI no debe manipular diccionarios crudos de negocio.\n"
            "- El intercambio entre capas se realiza con DTOs (`*DTO`).\n"
            "- Los analizadores de frontera verifican que no se reintroduzcan accesos legacy en UI.\n"
            "- `PrepStepsWidget` lee filas de preproceso/fase con `_ui_record_field` (dict o DTO), evitando `preproceso['id']` en la lista.\n"
            "- Vista trabajador: `WorkerDbSync.get_assigned_fabricaciones` devuelve `WorkerTaskListRowDTO`; "
            "`WorkerMainWindow` mantiene la selección tipada y las señales emiten `to_signal_dict()` donde el receptor aún espera `dict`.\n"
            "- Nueva iteración de producto: `AddIterationFormData` en el diálogo; `ProductIterationsWidget` usa `asdict(form)` al llamar al controlador.\n"
            "- **CI** ejecuta `scripts/ui_dto_boundary_analyzer.py --enforce-zero`: el job **falla** si hay hallazgos en el alcance por defecto de `ui/` "
            "(sin `continue-on-error`). En fallo, el workflow sube el artefacto `ui_dto_boundary_report.json` para depuración.\n\n"
        )
        md.write("### Desacoplamiento UI: widgets hoja frente a MainView\n\n")
        md.write(
            "**MainView** sigue siendo el lugar que recibe `AppController` para navegación, backup y casos "
            "especiales (p. ej. settings). Los **widgets hoja** y diálogos reutilizables deben preferir:\n\n"
        )
        md.write(
            "- Inyección de **servicios**, **fachadas** (`ProductFacade`, …) o **controladores de dominio acotados** "
            "(`ProductController`) resueltos desde `DIContainer`.\n"
        )
        md.write(
            "- **Señales PyQt** o callbacks mínimos (`show_warning`, abrir fichero) en lugar de "
            "`controller.view.show_message` desde componentes reutilizables.\n"
        )
        md.write(
            "- **GestionDatosWidget**: pestañas construidas con dependencias del contenedor donde proceda; "
            "**PrepStepsWidget**: validación expuesta vía señales hacia el padre.\n"
        )
        md.write(
            "- **Tests de cableado**: arranque con `MainView` real sustituye `QChartView` por un `QWidget` "
            "hijo válido en layout; `WorkersWidget()` sin `controller=` tras registrar `WorkerController` en DI; "
            "`PreprocesoDialog` recibe `material_port` (no el hub completo).\n\n"
        )
        md.write(MERMAID_ARQUITECTURA + "\n\n")
        md.write("### Matriz RBAC (Roles vs Permisos)\n\n")
        md.write("| Permiso | ADMIN | RESPONSABLE | OPERARIO | INVITADO |\n")
        md.write("|---|---|---|---|---|\n")
        md.write("| MANAGE_USERS | Sí | Sí | No | No |\n")
        md.write("| VIEW_PRODUCTS | Sí | Sí | Sí | No |\n")
        md.write("| CREATE_PRODUCT | Sí | Sí | No | No |\n")
        md.write("| EDIT_PRODUCT | Sí | Sí | No | No |\n")
        md.write("| DELETE_PRODUCT | Sí | Sí | No | No |\n")
        md.write("| VIEW_FABRICATIONS | Sí | Sí | Sí | No |\n")
        md.write("| CREATE_FABRICATION | Sí | Sí | No | No |\n")
        md.write("| EDIT_FABRICATION | Sí | Sí | No | No |\n")
        md.write("| DELETE_FABRICATION | Sí | Sí | No | No |\n")
        md.write("| MANAGE_MACHINES | Sí | Sí | No | No |\n")
        md.write("| VIEW_DASHBOARD | Sí | Sí | Sí | No |\n")
        md.write("| GENERATE_REPORTS | Sí | Sí | No | No |\n")
        md.write("| MANAGE_SETTINGS | Sí | Sí | No | No |\n")
        md.write("| VIEW_HISTORY | Sí | Sí | No | No |\n\n")
        md.write("### Defensa en profundidad RBAC (controladores)\n\n")
        md.write(
            "Además del filtrado de UI en `SessionController`, operaciones sensibles usan "
            "`@require_permission` (`core/security/access_control.py`):\n\n"
        )
        md.write("| Área | Permiso | Entrypoints |\n")
        md.write("|---|---|---|\n")
        md.write(
            "| Backup ZIP (import / export / sync) y diálogo restore | MANAGE_SETTINGS | "
            "`BackupController.on_import_databases`, `on_export_databases`, `on_sync_databases`, "
            "`show_backup_restore_dialog` |\n"
        )
        md.write(
            "| PDF desde historial | GENERATE_REPORTS | `HistorialReportManager.on_print_report_clicked` |\n"
        )
        md.write(
            "| Productos, fabricaciones, máquinas, usuarios, preprocesos | (matriz anterior) | "
            "`ProductController` / managers, `MachineController`, `TaskManager`, `PreprocesoManager`, etc. |\n\n"
        )
        md.write("### Simulación: RegistroTemporal\n\n")
        md.write(
            "- SQLite en archivo temporal con **WAL** para reducir pérdida si el proceso termina entre vaciados del buffer.\n"
            "- `MotorDeEventos.ejecutar_simulacion` confía en `consultar_eventos` (vaciado previo del buffer) y en "
            "`finally: registro_temporal.cleanup()`.\n"
            "- `RegistroTemporal.cleanup()` borra el `.db` y los compañeros `-wal` / `-shm`.\n\n"
        )
        md.write("### Política AppModel y nuevas features\n\n")
        md.write(
            "- Registrar servicios en `DIContainer` y resolver dependencias en controladores; evitar nuevos delegadores "
            "en `AppModel` salvo señales Qt o compatibilidad documentada.\n"
            "- Poda de métodos delegadores de `AppModel` solo si **cero usos** en el repo (búsqueda con `rg`), "
            "con `pytest`/`mypy` en módulos tocados.\n\n"
        )
        md.write("### Acciones Auditables\n\n")
        md.write("| Acción | Disparo principal | Registro |\n")
        md.write("|---|---|---|\n")
        md.write("| LOGIN | SessionController.handle_login | AuditLogger.log_login |\n")
        md.write("| LOGOUT | SessionController.logout | AuditLogger.log_logout |\n")
        md.write("| DELETE | Operaciones sensibles de datos | AuditLogger.log_delete |\n")
        md.write("| EXPORT | Exportaciones de reportes/datos | AuditLogger.log_export |\n")
        md.write("| IMPORT | Importaciones y restauraciones | AuditLogger.log_import |\n")
        md.write("| SETTINGS_CHANGE | Cambios de configuración | AuditLogger.log_settings_change |\n\n")
        md.write("---\n\n")

        # ── 3. ÁRBOL DE CARPETAS ─────────────────────────────────────────────
        md.write("## Arbol de Carpetas\n\n")
        md.write(_build_folder_tree_mermaid() + "\n\n")

        # Tabla de carpetas con descripción
        md.write("| Carpeta | Contenido |\n")
        md.write("|---|---|\n")
        md.write("| `controllers/` | Controladores MVC — uno por dominio funcional |\n")
        md.write("| `core/` | AppModel, servicios de negocio, DTOs, simulación, seguridad |\n")
        md.write("| `database/` | Modelos SQLAlchemy, repositorios, DatabaseManager |\n")
        md.write("| `ui/` | Widgets PyQt6, diálogos, ventana principal |\n")
        md.write("| `features/` | Módulos de funcionalidad transversal (worker sync, validación) |\n")
        md.write(
            "| `scripts/` | Generación de docs (`generate_daniel_doc`), QA (`test_quality_analyzer`), "
            "auditoría frontera UI/DTO Fase 12C (`ui_dto_boundary_analyzer`, gate en CI con `--enforce-zero`), "
            "detección de código muerto (`detect_dead_code`), **mantenimiento crítico** (`maintenance/`: backup BD, reset admin), "
            "`init_database.py` con mypy estricto en CI |\n"
        )
        md.write("| `tests/` | Suite de tests (unit, integration, e2e) |\n")
        md.write("| `migrations/` | Migraciones Alembic de la base de datos |\n\n")
        md.write("---\n\n")

        # ── 4. ERD ───────────────────────────────────────────────────────────
        md.write("## Modelo de Base de Datos ERD\n\n")
        md.write(
            "Esquema completo extraído de los modelos SQLAlchemy en `database/models/`. "
            "Las tablas de enlace Many-to-Many (`fabricacion_preproceso_link`, "
            "`trabajador_fabricacion_link`, etc.) están implícitas en las relaciones.\n\n"
        )
        md.write(MERMAID_ERD + "\n\n")
        
        md.write("### Leyenda del Diccionario de Datos\n\n")
        md.write(
            "El esquema ERD contiene campos de control lógico cuyo significado literal es:\n"
            "- **`tipo_trabajador`** (INT) en Tablas `Producto`, `Subfabricacion`, `ProcesoMecanico` y `Trabajador`:\n"
            "  - `1`: **Operario Básico / Junior** (Capaz de montar y ejecutar tareas estándar).\n"
            "  - `2`: **Especialista / Mid** (Capaz de operar maquinaria pesada, Tornos/Fresas y programación CNC sencilla).\n"
            "  - `3`: **Experto / Senior** (Capaz de validar calidad, resolver cuellos de botella y supervisar flujo).\n"
        )
        md.write("---\n\n")

        # Tabla de modelos
        md.write("### Modelos principales\n\n")
        md.write("| Modelo | Tabla | Descripción |\n")
        md.write("|---|---|---|\n")
        md.write("| `Producto` | `productos` | Catálogo de productos con tiempos y procesos |\n")
        md.write("| `Fabricacion` | `fabricaciones` | Orden de fabricación (OF) |\n")
        md.write("| `Trabajador` | `trabajadores` | Operarios y administradores |\n")
        md.write("| `Maquina` | `maquinas` | Recursos físicos de planta |\n")
        md.write("| `Preproceso` | `preprocesos` | Tareas preparatorias reutilizables |\n")
        md.write("| `Material` | `materiales` | Materias primas y componentes (BOM) |\n")
        md.write("| `Pila` | `pilas` | Plan de producción para simulación |\n")
        md.write("| `Lote` | `lotes` | Agrupación logística de fabricaciones |\n")
        md.write("| `GrupoPreparacion` | `grupos_preparacion` | Pasos de setup de máquina |\n\n")
        md.write("---\n\n")

        # ── 5. FLUJOS ────────────────────────────────────────────────────────
        md.write("## Flujos Principales\n\n")

        md.write("### Flujo de Fabricación y Trazabilidad QR\n\n")
        md.write(MERMAID_FLUJO_FABRICACION + "\n\n")

        md.write("### Flujo de Importación BOM (A3RP)\n\n")
        md.write(MERMAID_FLUJO_IMPORT_BOM + "\n\n")

        md.write("### Flujo de Simulación y Gantt\n\n")
        md.write(MERMAID_FLUJO_SIMULACION + "\n\n")
        
        md.write("### Sistema de Etiquetado QR (Apli 1861)\n\n")
        md.write(
            "Arquitectura desacoplada para la generación de etiquetas de trazabilidad. "
            "Soporta plantillas Word estáticas y generación dinámica de cuadrículas A5 (66 etiquetas).\n\n"
        )
        md.write(MERMAID_SISTEMA_ETIQUETADO + "\n\n")
        md.write("### Flujo de Sincronización Offline/USB\n\n")
        md.write(MERMAID_FLUJO_SYNC_USB + "\n\n")
        md.write("### Flujo de Login y Autorización\n\n")
        md.write(MERMAID_FLUJO_LOGIN_AUTORIZACION + "\n\n")
        md.write("---\n\n")

        # ── 6. TECNOLOGÍAS ───────────────────────────────────────────────────
        md.write("## Tecnologias\n\n")
        md.write("| Librería | Versión |\n")
        md.write("|---|---|\n")
        md.write("| Python | 3.12+ |\n")
        for tech in _get_technologies():
            md.write(f"| {tech['name']} | {tech['version']} |\n")
        md.write("\n")

        md.write("### ¿Qué representa cada tecnología? (explicación simple)\n\n")
        md.write(
            "- `Python`: el “lenguaje de trabajo” del proyecto; el sistema programa toda la lógica.\n"
            "- `SQLAlchemy`: traduce objetos Python a “filas/tablas” en la base de datos.\n"
            "- `PyQt6`: crea la interfaz de escritorio (ventanas, botones, diálogos y señales).\n"
            "- `Alembic`: gestiona cambios graduales del esquema de la base de datos.\n"
            "- `pytest`: ejecuta la suite de pruebas para asegurar que todo funciona tras cambios.\n\n"
            "- `mypy`: revisa tipos de forma estática para detectar errores antes de ejecutar.\n"
            "- `Mermaid`: dibuja diagramas (arquitectura, relaciones y flujos) dentro del documento.\n"
            "- `markdown-pdf`: convierte el Markdown final a PDF listo para leer/compartir.\n\n"
        )
        md.write("---\n\n")

        # ── 7. INSTALACIÓN Y DESPLIEGUE ─────────────────────────────────────
        md.write("## Instalacion y Despliegue\n\n")
        md.write("### Requisitos base\n\n")
        md.write(
            "- Python 3.11 o superior; CI en 3.11 y 3.12 (`.github/workflows/ci.yml`); "
            "referencia de tipado mypy `python_version = 3.12`; `.python-version` recomienda 3.12 para pyenv.\n"
        )
        md.write("- Entorno virtual (`venv`) recomendado\n")
        md.write("- Dependencias instaladas desde `requirements.txt`\n\n")
        md.write("### Instalación local (desarrollo)\n\n")
        md.write("1. Crear entorno virtual: `python -m venv .venv`\n")
        md.write("2. Activar entorno:\n")
        md.write("   - macOS/Linux: `source .venv/bin/activate`\n")
        md.write("   - Windows (PowerShell): `.venv\\\\Scripts\\\\Activate.ps1`\n")
        md.write("3. Instalar dependencias: `pip install -r requirements.txt`\n")
        md.write("4. Configurar entorno: copiar `.env.example` a `.env` y ajustar variables\n")
        md.write("5. Ejecutar aplicación: `python app.py`\n\n")
        md.write("### Configuración de rutas (producción)\n\n")
        md.write(
            "- Base de datos: `DB_TYPE` y `DB_PATH` (SQLite por defecto en `data/montaje.db`).\n"
            "- Logs: `LOG_DIR` (por defecto `logs`).\n"
            "- Backups: `BACKUP_DIR` (por defecto `backups`).\n"
            "- Todas las rutas relativas se resuelven desde la raíz del proyecto.\n\n"
        )
        md.write("### Empaquetado para planta\n\n")
        md.write(
            "- Script oficial: `python scripts/build_executable.py`\n"
            "- Motor: PyInstaller\n"
            "- Artefacto final: carpeta `dist/` con ejecutable `Hipatia`\n"
            "- Incluye recursos críticos de migración (`migrations/` y `alembic.ini`).\n\n"
        )
        md.write("---\n\n")

        # ── 8. SUITE DE TESTS ────────────────────────────────────────────────
        compliance_data = _load_compliance_data()
        _write_testing_section(md, compliance_data)

        # ── 9. REFERENCIA DE COMPONENTES ─────────────────────────────────────
        md.write("## Referencia de Componentes\n\n")
        md.write(
            "> Extraído automáticamente de los docstrings del código fuente. "
            "Organizado por capa.\n\n"
        )
        print("  Volcando referencia por archivo (AST por fichero; la fase más larga)…", flush=True)

        if root_files:
            md.write("<div class='pagebreak'></div>\n\n")
            md.write("<div id='folder_root'>\n\n## Raíz del proyecto\n\n</div>\n\n")
            md.write(_folder_connections_mermaid("root") + "\n\n")
            print(f"  · Raíz del proyecto: {len(root_files)} archivo(s)…", flush=True)
            for rel in root_files:
                _write_file_section(md, PROJECT_ROOT / rel)

        for dirname, files in dir_files.items():
            fstats = _folder_stats(index_tree, dirname)

            # Portada de capítulo (1 página)
            md.write("<div class='pagebreak'></div>\n\n")
            md.write(f"<div id='folder_{dirname}'>\n\n## Capítulo: `{dirname}/`\n\n</div>\n\n")
            md.write("| Métrica | Valor |\n")
            md.write("|---|---:|\n")
            md.write(f"| Archivos `.py` en `{dirname}/` | {fstats['total_py']} |\n")
            md.write(f"| Incluidos en el cuerpo | {fstats['included']} |\n")
            md.write(f"| Omitidos (docstrings/reglas) | {fstats['omitted']} |\n")
            md.write(f"| Clases detectadas (AST) | {fstats['total_classes']} |\n\n")
            md.write(_folder_connections_mermaid(dirname) + "\n\n")

            # Contenido del capítulo (empieza en página nueva)
            md.write("<div class='pagebreak'></div>\n\n")
            md.write(f"## {dirname}/ — Referencia\n\n")
            n_dir = len(files)
            print(f"  · Capítulo `{dirname}/`: {n_dir} archivo(s)…", flush=True)
            for i, rel in enumerate(files, start=1):
                if n_dir > 40 and i % 40 == 0:
                    print(f"    … {i}/{n_dir} `{dirname}`", flush=True)
                _write_file_section(md, PROJECT_ROOT / rel)

    print(f"✅ Documentación Markdown generada: {OUTPUT_FILE}", flush=True)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Genera Documentacion Daniel (.md y opcionalmente .pdf).")
    parser.add_argument(
        "--md-only",
        action="store_true",
        help="Solo genera el Markdown (sin PDF ni doble pase). Mucho más rápido.",
    )
    args = parser.parse_args()

    print("Generando documentación de Hipatia...", flush=True)

    # 0. Limpiar archivos antiguos en la carpeta de destino
    if OUTPUT_DIR.exists():
        for old_file in OUTPUT_DIR.glob("Documentacion Daniel.*"):
            try:
                old_file.unlink()
                print(f"Borrando archivo antiguo: {old_file.name}", flush=True)
            except Exception as e:
                print(f"No se pudo borrar {old_file.name}: {e}", flush=True)

    if args.md_only:
        generate_markdown(page_map=None)
        print(f"✅ Modo --md-only: no se generó PDF. Salida: {OUTPUT_FILE}", flush=True)
        return

    # PDF opcional con page-map exacto (2 pases) usando partición por archivo.
    try:
        import markdown_pdf  # noqa: F401

        print("Fase 1/4: Markdown con índice placeholder (p0000)…", flush=True)
        generate_markdown(page_map=None)  # índice con placeholders p0000
        md_placeholder = OUTPUT_FILE.read_text(encoding="utf-8")

        pdf_file = str(OUTPUT_FILE).replace(".md", ".pdf")
        print(f"Fase 2/4: medición de páginas → `{pdf_file}` (lento)…", flush=True)
        page_map = _measure_page_starts_for_file_sections(md_placeholder)

        print("Fase 3/4: Markdown con páginas exactas en el índice…", flush=True)
        generate_markdown(page_map=page_map)  # índice con páginas exactas
        md_final = OUTPUT_FILE.read_text(encoding="utf-8")

        print(f"Fase 4/4: render final del PDF…", flush=True)
        _render_pdf_from_markdown(md_final)
        print(f"✅ PDF generado: {pdf_file}", flush=True)
    except ImportError:
        generate_markdown(page_map=None)
        print("⚠️  markdown_pdf no instalado — solo se generó el .md", flush=True)
    except Exception as e:
        # Fallback seguro: al menos generar el .md final con placeholder.
        generate_markdown(page_map=None)
        print(f"⚠️  Error al generar PDF: {e}", flush=True)


if __name__ == "__main__":
    main()
