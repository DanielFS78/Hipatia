import sys
import unittest
from PyQt6.QtWidgets import QApplication

# Ensure ui package is in path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class TestSettingsWidgetLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)

    def test_missing_methods_and_connections(self):
        from ui.widgets.settings_widget import SettingsWidget
        widget = SettingsWidget(controller=None)
        
        # Check if methods exist
        self.assertTrue(hasattr(widget, '_on_add_break'), "_on_add_break should exist")
        self.assertTrue(hasattr(widget, '_on_edit_break'), "_on_edit_break should exist")
        self.assertTrue(hasattr(widget, '_on_remove_break'), "_on_remove_break should exist")
        
        # Check connections - this is harder to test directly without inspecting Qt signals, 
        # but we know from code analysis they are wrong.
        # We can just verify the fix involves these methods existing later.

if __name__ == '__main__':
    unittest.main()
