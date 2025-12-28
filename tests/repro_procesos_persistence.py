import sys
import os
import unittest
# Ensure root is in path BEFORE importing local modules
sys.path.append(os.getcwd())

from PyQt6.QtWidgets import QApplication
from ui.widgets.products_widget import AddProductWidget, ProductsWidget
from abc import ABC, abstractmethod

app = QApplication(sys.argv)

class TestProductDataCollection(unittest.TestCase):
    def test_add_product_widget_collects_procesos(self):
        """Test that AddProductWidget includes procesos_mecanicos in get_data()"""
        widget = AddProductWidget()
        
        # Simulate adding processes
        test_procesos = [{"nombre": "P1", "tiempo": 10}]
        widget.procesos_mecanicos_temp = test_procesos
        
        # Case 1: No subfabrications
        widget.sub_switch.setChecked(False)
        data = widget.get_data()
        self.assertIn("procesos_mecanicos", data, "procesos_mecanicos missing when no subs")
        self.assertEqual(data["procesos_mecanicos"], test_procesos)
        
        # Case 2: With subfabrications
        widget.sub_switch.setChecked(True)
        data_with_subs = widget.get_data()
        
        self.assertIn("procesos_mecanicos", data_with_subs, "procesos_mecanicos missing when has_subs=True")
        self.assertEqual(data_with_subs["procesos_mecanicos"], test_procesos)
        print("\nSuccess: AddProductWidget correctly includes processes with subs enabled")

    def test_products_widget_collects_procesos(self):
        """Test that ProductsWidget (edit mode) includes procesos_mecanicos"""
        # Mock controller
        mock_controller = None 
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
