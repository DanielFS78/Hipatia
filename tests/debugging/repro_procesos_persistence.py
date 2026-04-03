import sys
import os
import unittest
from unittest.mock import MagicMock
# Ensure root is in path BEFORE importing local modules
sys.path.append(os.getcwd())

from PyQt6.QtWidgets import QApplication
from ui.widgets.products_widget import ProductsWidget

app = QApplication(sys.argv)

class TestProductDataCollection(unittest.TestCase):
    def test_products_widget_collects_procesos(self):
        """Test that ProductsWidget (edit mode) includes procesos_mecanicos"""
        from core.di_container import DIContainer
        from controllers.product_controller_v2 import ProductController
        
        # Mock controller
        mock_controller = MagicMock()
        DIContainer.get_instance().register(ProductController, instance=mock_controller)
        widget = ProductsWidget(mock_controller)
        
        # Simulate creating edit form
        class MockData:
            codigo = "TEST"
            descripcion = "DESC"
            departamento = "Mecánica"
            donde = "Loc"
            tiene_subfabricaciones = 0
            tiempo_optimo = 0
        
        widget.display_product_form(MockData(), [])
        
        # Simulate adding processes
        test_procesos = [{"nombre": "PEdit", "tiempo": 20}]
        widget.current_procesos_mecanicos = test_procesos
        
        data = widget.get_product_form_data()
        
        self.assertIn("procesos_mecanicos", data, "procesos_mecanicos missing in ProductsWidget (Edit Mode)")
        self.assertEqual(data["procesos_mecanicos"], test_procesos)
        print("Success: ProductsWidget correctly includes processes")

if __name__ == '__main__':
    unittest.main()
