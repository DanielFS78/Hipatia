"""
Tests de Setup para ui/dialogs/ - Fase 3.7 (Refactorizado para Fase 3.8/3.10)
=============================================================================
Tests que verifican la estructura y configuración de los diálogos:
- Existencia de clases en el paquete ui/dialogs
- Herencia correcta
- Señales definidas
- Métodos requeridos

Adaptado para soportar estructura modular (paquete en lugar de archivo único).
"""

import pytest
import ast
import os
from pathlib import Path


# Ruta al directorio de diálogos
DIALOGS_DIR = Path(__file__).resolve().parent.parent.parent / "ui" / "dialogs"


# =============================================================================
# FIXTURES DE SETUP
# =============================================================================

@pytest.fixture(scope="module")
def dialogs_classes():
    """Extrae todas las clases definidas en los archivos .py de ui/dialogs/."""
    classes = {}
    
    # Recorrer todos los archivos .py en el directorio
    for root, _, files in os.walk(DIALOGS_DIR):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    tree = ast.parse(source_code)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes[node.name] = {
                                "bases": [
                                    base.id if isinstance(base, ast.Name) 
                                    else base.attr if isinstance(base, ast.Attribute)
                                    else str(base)
                                    for base in node.bases
                                ],
                                "methods": [
                                    n.name for n in node.body
                                    if isinstance(n, ast.FunctionDef)
                                ],
                                "line": node.lineno,
                                "file": file
                            }
                except Exception as e:
                    print(f"Error parseando {file}: {e}")
                    
    return classes


# =============================================================================
# TESTS DE ESTRUCTURA: Verificación de Existencia de Clases
# =============================================================================

@pytest.mark.setup
class TestDialogsClassesExist:
    """Verifica que todas las clases requeridas existen."""

    # Clases de diálogos principales
    REQUIRED_DIALOG_CLASSES = [
        "PreprocesosSelectionDialog",
        "CreateFabricacionDialog",
        "PreprocesosForCalculationDialog",
        "AssignPreprocesosDialog",
        "DefineProductionFlowDialog",
        "EnhancedProductionFlowDialog",
        "SubfabricacionesDialog",
        "ProductDetailsDialog",
        "PreprocesoDialog",
        "GetUnitsDialog",
        "GetLoteInstanceParametersDialog",
        "GetOptimizationParametersDialog",
        "SeleccionarHojasExcelDialog",
        "AddBreakDialog",
        "DefinirCantidadesDialog",
    ]

    # Clases de widgets auxiliares
    REQUIRED_WIDGET_CLASSES = [
        "CanvasWidget",
        "CardWidget",
    ]

    # Clases de efectos visuales
    REQUIRED_EFFECT_CLASSES = [
        "GoldenGlowEffect",
        "ProcessingGlowEffect",
    ]

    # Clases de configuración
    REQUIRED_CONFIG_CLASSES = [
        "CycleEndConfigDialog",
        "ReassignmentRuleDialog",
        "MultiWorkerSelectionDialog",
    ]

    def test_dialog_classes_exist(self, dialogs_classes):
        """Todas las clases de diálogo principales deben existir."""
        for class_name in self.REQUIRED_DIALOG_CLASSES:
            assert class_name in dialogs_classes, \
                f"Falta la clase de diálogo: {class_name}"

    def test_widget_classes_exist(self, dialogs_classes):
        """Todas las clases de widgets auxiliares deben existir."""
        for class_name in self.REQUIRED_WIDGET_CLASSES:
            assert class_name in dialogs_classes, \
                f"Falta la clase de widget: {class_name}"

    def test_effect_classes_exist(self, dialogs_classes):
        """Todas las clases de efectos visuales deben existir."""
        for class_name in self.REQUIRED_EFFECT_CLASSES:
            assert class_name in dialogs_classes, \
                f"Falta la clase de efecto: {class_name}"

    def test_config_classes_exist(self, dialogs_classes):
        """Todas las clases de configuración deben existir."""
        for class_name in self.REQUIRED_CONFIG_CLASSES:
            assert class_name in dialogs_classes, \
                f"Falta la clase de configuración: {class_name}"


# =============================================================================
# TESTS DE HERENCIA
# =============================================================================

@pytest.mark.setup
class TestDialogsInheritance:
    """Verifica la herencia correcta de las clases."""

    def test_dialog_classes_inherit_from_qdialog(self, dialogs_classes):
        """Las clases de diálogo deben heredar de QDialog."""
        qdialog_children = [
            "PreprocesosSelectionDialog",
            "CreateFabricacionDialog",
            "PreprocesosForCalculationDialog",
            "AssignPreprocesosDialog",
            "DefineProductionFlowDialog",
            "EnhancedProductionFlowDialog",
            "SubfabricacionesDialog",
            "ProductDetailsDialog",
            "GetUnitsDialog",
            "SeleccionarHojasExcelDialog",
            "AddBreakDialog",
        ]
        
        for class_name in qdialog_children:
            if class_name in dialogs_classes:
                bases = dialogs_classes[class_name]["bases"]
                # Aceptamos QDialog o QtWidgets.QDialog
                has_qdialog = any("QDialog" in base for base in bases)
                assert has_qdialog, \
                    f"{class_name} debe heredar de QDialog, tiene: {bases}"

    def test_widget_classes_inherit_from_qwidget(self, dialogs_classes):
        """Las clases de widget deben heredar de QWidget o derivados."""
        valid_bases = ["QWidget", "QFrame", "QGraphicsEffect", "QLabel"]
        
        widget_classes = ["CanvasWidget", "CardWidget"]
        for class_name in widget_classes:
            if class_name in dialogs_classes:
                bases = dialogs_classes[class_name]["bases"]
                has_valid_base = any(
                    any(vb in base for vb in valid_bases) 
                    for base in bases
                )
                assert has_valid_base, \
                    f"{class_name} debe heredar de QWidget o similar, tiene: {bases}"

    def test_effect_classes_inherit_from_qwidget(self, dialogs_classes):
        """Las clases de efectos deben heredar de QWidget o tener Effect en su base."""
        effect_classes = ["GoldenGlowEffect", "ProcessingGlowEffect"]
        for class_name in effect_classes:
            if class_name in dialogs_classes:
                bases = dialogs_classes[class_name]["bases"]
                # Aceptamos QWidget (overlays) o QGraphicsEffect
                valid = any("QWidget" in base or "Effect" in base for base in bases)
                assert valid, \
                    f"{class_name} debe heredar de QWidget o Effect, tiene: {bases}"


# =============================================================================
# TESTS DE MÉTODOS REQUERIDOS
# =============================================================================

@pytest.mark.setup
class TestDialogsRequiredMethods:
    """Verifica que las clases tengan los métodos requeridos."""

    def test_selection_dialogs_have_get_selected_method(self, dialogs_classes):
        """Los diálogos de selección deben tener método get_selected_*."""
        selection_dialogs = {
            "PreprocesosSelectionDialog": "get_selected_preprocesos",
            "PreprocesosForCalculationDialog": "get_selected_preprocesos",
            "MultiWorkerSelectionDialog": "get_selected_workers",
        }
        
        for class_name, required_method in selection_dialogs.items():
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert required_method in methods, \
                    f"{class_name} debe tener método {required_method}"

    def test_creation_dialogs_have_get_data_method(self, dialogs_classes):
        """Los diálogos de creación deben tener método para obtener datos."""
        creation_dialogs = {
            "CreateFabricacionDialog": "get_fabricacion_data",
            "PreprocesoDialog": "get_data",
            "GetUnitsDialog": "get_units",
            "GetLoteInstanceParametersDialog": "get_data",
            "GetOptimizationParametersDialog": "get_parameters",
            "SeleccionarHojasExcelDialog": "get_opciones",
            "DefinirCantidadesDialog": "get_cantidades",
        }
        
        for class_name, required_method in creation_dialogs.items():
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert required_method in methods, \
                    f"{class_name} debe tener método {required_method}"

    def test_flow_dialogs_have_get_production_flow(self, dialogs_classes):
        """Los diálogos de flujo deben tener get_production_flow."""
        flow_dialogs = ["DefineProductionFlowDialog"]
        
        for class_name in flow_dialogs:
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert "get_production_flow" in methods, \
                    f"{class_name} debe tener método get_production_flow"

    def test_config_dialogs_have_get_configuration(self, dialogs_classes):
        """Los diálogos de configuración deben tener método de configuración."""
        config_dialogs = {
            "CycleEndConfigDialog": "get_configuration",
            "ReassignmentRuleDialog": "get_rule",
        }
        
        for class_name, required_method in config_dialogs.items():
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert required_method in methods, \
                    f"{class_name} debe tener método {required_method}"

    def test_all_dialogs_have_init(self, dialogs_classes):
        """Todas las clases deben tener __init__."""
        for class_name, class_info in dialogs_classes.items():
            assert "__init__" in class_info["methods"], \
                f"{class_name} debe tener método __init__"


# =============================================================================
# TESTS DE WIDGETS DEL CANVAS
# =============================================================================

@pytest.mark.setup
class TestCanvasWidgetSetup:
    """Verifica la configuración del CanvasWidget."""

    def test_canvas_has_set_connections(self, dialogs_classes):
        """CanvasWidget debe tener método set_connections."""
        if "CanvasWidget" in dialogs_classes:
            methods = dialogs_classes["CanvasWidget"]["methods"]
            assert "set_connections" in methods

    def test_canvas_has_paint_event(self, dialogs_classes):
        """CanvasWidget debe tener paintEvent."""
        if "CanvasWidget" in dialogs_classes:
            methods = dialogs_classes["CanvasWidget"]["methods"]
            assert "paintEvent" in methods

    def test_canvas_has_drag_events(self, dialogs_classes):
        """CanvasWidget debe manejar eventos de drag & drop."""
        if "CanvasWidget" in dialogs_classes:
            methods = dialogs_classes["CanvasWidget"]["methods"]
            assert "dragEnterEvent" in methods
            assert "dropEvent" in methods


@pytest.mark.setup
class TestCardWidgetSetup:
    """Verifica la configuración del CardWidget."""

    def test_card_has_mouse_events(self, dialogs_classes):
        """CardWidget debe manejar eventos de ratón."""
        if "CardWidget" in dialogs_classes:
            methods = dialogs_classes["CardWidget"]["methods"]
            assert "mousePressEvent" in methods
            assert "mouseMoveEvent" in methods
            assert "mouseReleaseEvent" in methods

    def test_card_has_snap_to_grid(self, dialogs_classes):
        """CardWidget debe tener _snap_to_grid."""
        if "CardWidget" in dialogs_classes:
            methods = dialogs_classes["CardWidget"]["methods"]
            assert "_snap_to_grid" in methods


# =============================================================================
# TESTS DE EFECTOS VISUALES
# =============================================================================

@pytest.mark.setup
class TestVisualEffectsSetup:
    """Verifica la configuración de efectos visuales."""

    def test_effects_have_stop_animation(self, dialogs_classes):
        """Los efectos deben tener stop_animation."""
        effect_classes = ["GoldenGlowEffect", "ProcessingGlowEffect"]
        for class_name in effect_classes:
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert "stop_animation" in methods, \
                    f"{class_name} debe tener stop_animation"

    def test_effects_have_paint_event(self, dialogs_classes):
        """Los efectos deben tener paintEvent."""
        effect_classes = ["GoldenGlowEffect", "ProcessingGlowEffect"]
        for class_name in effect_classes:
            if class_name in dialogs_classes:
                methods = dialogs_classes[class_name]["methods"]
                assert "paintEvent" in methods, \
                    f"{class_name} debe tener paintEvent"


# =============================================================================
# TESTS DE IMPORTACIONES
# =============================================================================

@pytest.mark.setup
class TestDialogsImports:
    """Verifica que los diálogos se pueden importar correctamente."""

    def test_dialog_module_imports(self):
        """El módulo ui.dialogs debe ser importable."""
        try:
            from ui import dialogs
            assert dialogs is not None
        except ImportError as e:
            pytest.fail(f"Error al importar ui.dialogs: {e}")

    def test_main_dialogs_importable(self):
        """Las clases principales deben ser importables."""
        from ui.dialogs import (
            PreprocesosSelectionDialog,
            CreateFabricacionDialog,
            CanvasWidget,
            CardWidget,
        )
        
        assert PreprocesosSelectionDialog is not None
        assert CreateFabricacionDialog is not None
        assert CanvasWidget is not None
        assert CardWidget is not None

    def test_flow_dialogs_importable(self):
        """Los diálogos de flujo deben ser importables."""
        from ui.dialogs import (
            DefineProductionFlowDialog,
            EnhancedProductionFlowDialog,
        )
        
        assert DefineProductionFlowDialog is not None
        assert EnhancedProductionFlowDialog is not None

    def test_utility_dialogs_importable(self):
        """Los diálogos utilitarios deben ser importables."""
        from ui.dialogs import (
            GetUnitsDialog,
            AddBreakDialog,
            SeleccionarHojasExcelDialog,
        )
        
        assert GetUnitsDialog is not None
        assert AddBreakDialog is not None
        assert SeleccionarHojasExcelDialog is not None


# =============================================================================
# TESTS DE CONTEO Y MÉTRICAS
# =============================================================================

@pytest.mark.setup
class TestDialogsMetrics:
    """Verifica métricas del paquete de diálogos."""

    def test_minimum_classes_count(self, dialogs_classes):
        """El paquete debe tener un número mínimo de clases."""
        assert len(dialogs_classes) >= 30, \
            f"Se esperan al menos 30 clases, hay {len(dialogs_classes)}"

    def test_no_empty_classes(self, dialogs_classes):
        """Las clases no deben estar vacías (al menos __init__)."""
        for class_name, class_info in dialogs_classes.items():
            assert len(class_info["methods"]) > 0, \
                f"La clase {class_name} en {class_info['file']} no tiene métodos"

    def test_directory_exists(self):
        """El directorio dialogs debe existir."""
        assert DIALOGS_DIR.exists() and DIALOGS_DIR.is_dir(), \
            f"El directorio {DIALOGS_DIR} no existe"

    def test_directory_has_content(self):
        """El directorio debe tener archivos .py."""
        py_files = list(DIALOGS_DIR.glob("*.py"))
        total_lines = 0
        for p in py_files:
            total_lines += len(p.read_text(encoding='utf-8').splitlines())
            
        assert len(py_files) >= 5, "Debe haber múltiples archivos .py en el paquete"
        assert total_lines > 1000, \
            f"El paquete tiene solo {total_lines} líneas, se esperan más de 1000"
