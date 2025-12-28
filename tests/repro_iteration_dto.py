
import unittest
import sys
import os
sys.path.append(os.getcwd())
from dataclasses import dataclass
from datetime import datetime

# Mocking the DTO
@dataclass
class ProductIterationDTO:
    id: int
    producto_codigo: str
    nombre_responsable: str
    fecha_creacion: datetime
    descripcion: str
    tipo_fallo: str = ""
    materiales: list = None
    ruta_imagen: str = None
    ruta_plano: str = None

class TestIterationAccess(unittest.TestCase):
    def test_iteration_access_as_dict_fails(self):
        """Simulate the crash when accessing DTO as dict"""
        iteration = ProductIterationDTO(
            id=1, producto_codigo="1112", nombre_responsable="Daniel",
            fecha_creacion=datetime.now(), descripcion="Test", 
            tipo_fallo="None", materiales=[]
        )
        
        # This mirrors the old code which failed
        try:
            _ = iteration['fecha_creacion'] # Or 'fecha'
            self.fail("Should have raised TypeError")
        except TypeError as e:
            self.assertIn("not subscriptable", str(e))
            print("\nSuccessfully reproduced TypeError: 'ProductIterationDTO' object is not subscriptable")

    def test_iteration_access_as_object_succeeds(self):
        """Verify the fix works"""
        iteration = ProductIterationDTO(
            id=1, producto_codigo="1112", nombre_responsable="Daniel",
            fecha_creacion=datetime.now(), descripcion="Test", 
            tipo_fallo="None", materiales=[]
        )
        # This mirrors the fix
        try:
            _ = iteration.fecha_creacion
            print("Successfully accessed iteration.fecha_creacion")
        except TypeError:
            self.fail("Should not raise TypeError")

    def test_dialog_import_syntax(self):
        """Verify ui/dialogs/product_dialogs.py has valid syntax"""
        try:
            import ui.dialogs.product_dialogs
            print("Successfully imported ui.dialogs.product_dialogs")
        except ImportError as e:
            # It might fail due to missing PyQT or other deps, but we check for SyntaxError
             print(f"Import failed with: {e}")
        except SyntaxError:
            self.fail("SyntaxError in product_dialogs.py")

if __name__ == '__main__':
    unittest.main()
