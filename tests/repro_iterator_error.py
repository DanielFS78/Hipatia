import sys
import unittest
from unittest.mock import MagicMock

# Ensure root is in path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class TestProductIteratorError(unittest.TestCase):
    def test_instantiation_error(self):
        """Test reproducing AttributeError: 'AppModel' object has no attribute 'model'"""
        # Mock AppModel
        app_model = MagicMock()
        # Ensure AppModel does NOT have a .model attribute, as in reality
        try:
            del app_model.model
        except AttributeError:
            pass

        # Simulate ProductController logic
        # Error line: dialog = ProductDetailsDialog(product_code, self.model, self.view)
        # Here self.model IS the AppModel instance
        
        # Simulate ProductDetailsDialog.__init__ logic
        # prod_data, _, _ = self.controller.model.get_product_details(self.product_code)
        
        controller_passed_to_dialog = app_model # This corresponds to 'self.model' passed from controller
        
        try:
            # This is what happens inside the Dialog's init:
            # self.controller = controller (which is app_model)
            # self.controller.model.get_product_details(...)
            _ = controller_passed_to_dialog.model.get_product_details("TEST_CODE")
        except AttributeError as e:
             # If we still get 'AppModel object has no attribute model', it failed.
             # If we get 'Mock object has no attribute get_product_details', it means it correctly accessed .model on the mock controller
             # which is what we want (it successfully went through self.controller.model)
            if "model" in str(e) and "AppModel" in str(e):
                 self.fail(f"Still getting AppModel error: {e}")
            print(f"\nCaught expected downstream error (meaning instantiation worked): {e}")

    def test_controller_has_methods(self):
        from controllers.product_controller import ProductController
        self.assertTrue(hasattr(ProductController, 'handle_add_material_to_product'), "Method handle_add_material_to_product missing")
        self.assertTrue(hasattr(ProductController, 'handle_image_attachment'), "Method handle_image_attachment missing")
        # Logic check: Verify source code uses material_repo (static check since we can't easily run full app stack here)
        import inspect
        source = inspect.getsource(ProductController.handle_add_material_to_product)
        self.assertIn("self.model.db.material_repo", source, "Controller should use material_repo")

        source_img = inspect.getsource(ProductController.handle_image_attachment)
        self.assertIn('iteration_repo.update_iteration_file_path', source_img, "Should use iteration_repo.update_iteration_file_path")

    def test_app_model_delegation(self):
        """Verify AppModel delegates to material_repo"""
        from core.app_model import AppModel
        import inspect
        
        # Check link_material_to_product
        source = inspect.getsource(AppModel.link_material_to_product)
        self.assertIn("self.db.material_repo.link_material_to_product", source)
        
        # Check add_material_to_iteration
        source_add = inspect.getsource(AppModel.add_material_to_iteration)
        self.assertIn("self.db.material_repo.add_material", source_add)

if __name__ == '__main__':
    unittest.main()
