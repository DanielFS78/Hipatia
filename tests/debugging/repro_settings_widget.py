import sys
import unittest
from PyQt6.QtWidgets import QApplication

# Ensure ui package is in path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class TestSettingsWidgetRepro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_settings_widget_instantiation(self):
        """Attempts to instantiate SettingsWidget. Should fail if imports are missing."""
        try:
            from ui.widgets.settings_widget import SettingsWidget
            widget = SettingsWidget(controller=None)
            print("SettingsWidget instantiated successfully.")
        except NameError as e:
            print(f"Caught expected NameError: {e}")
            self.fail(f"SettingsWidget failed to instantiate: {e}")
        except Exception as e:
            self.fail(f"SettingsWidget failed to instantiate with unexpected error: {e}")

if __name__ == '__main__':
    unittest.main()
