import sys
import unittest
from PyQt6.QtWidgets import QApplication

# Ensure ui package is in path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class TestSettingsWidgetHolidays(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)

    def test_missing_holiday_methods(self):
        from ui.widgets.settings_widget import SettingsWidget
        widget = SettingsWidget(controller=None)
        
        # Check if methods exist
        self.assertTrue(hasattr(widget, '_on_add_holiday'), "_on_add_holiday should exist")
        self.assertTrue(hasattr(widget, '_on_remove_holiday'), "_on_remove_holiday should exist")
        self.assertTrue(hasattr(widget, '_highlight_holidays'), "_highlight_holidays should exist")

if __name__ == '__main__':
    unittest.main()
