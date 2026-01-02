
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from core.qr_scanner import QrScanner

class TestQrScannerOptimization(unittest.TestCase):
    def test_wechat_qrcode_initialization(self):
        print("\nTesting WeChatQRCode Initialization...")
        
        # Mock dependencies
        mock_camera_manager = MagicMock()
        mock_camera_object = MagicMock()
        mock_camera_object.isOpened.return_value = True

        # Initialize Scanner
        scanner = QrScanner(mock_camera_manager, 0, mock_camera_object)
        
        # Check if WeChatQRCode was loaded
        if scanner.use_wechat:
            print("SUCCESS: WeChatQRCode is active.")
            print("Models found and loaded.")
        else:
            print("FAILURE: Fallback to standard QRCodeDetector.")
            print("Check if opencv-contrib-python is installed and models are in core/models/")
            
        self.assertTrue(scanner.use_wechat, "WeChatQRCode should be active if models are present")

        # Check standard properties
        self.assertTrue(scanner.is_camera_ready)

if __name__ == "__main__":
    unittest.main()
