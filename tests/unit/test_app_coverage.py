import os
import sys
import logging
import pytest
from unittest.mock import patch, MagicMock
from app import resource_path, setup_logging

@pytest.mark.unit
class TestAppUtils:
    """Tests for utility functions in app.py"""

    def test_resource_path_dev(self):
        """Test resource_path in development environment (no _MEIPASS)."""
        # Ensure _MEIPASS is not set
        if hasattr(sys, "_MEIPASS"):
            del sys._MEIPASS
            
        relative = "test_file.txt"
        expected = os.path.join(os.path.abspath("."), relative)
        assert resource_path(relative) == expected

    def test_resource_path_prod(self):
        """Test resource_path in production environment (with _MEIPASS)."""
        fake_meipass = "/tmp/fake_meipass"
        with patch.object(sys, "_MEIPASS", fake_meipass, create=True):
            relative = "config/config.ini"
            expected = os.path.join(fake_meipass, relative)
            assert resource_path(relative) == expected

    @patch("app.os.path.exists")
    @patch("app.os.makedirs")
    @patch("app.ConcurrentRotatingFileHandler")
    @patch("app.logging.StreamHandler")
    @patch("app.logging.getLogger")
    @patch("app.logging.info") # Patch logging.info to avoid root logger calls
    def test_setup_logging(self, mock_info, mock_get_logger, mock_stream, mock_file_handler, mock_makedirs, mock_exists):
        """Test setup_logging logic."""
        # Setup mocks
        mock_exists.return_value = False # Force directory creation path
        
        mock_file_instance = MagicMock()
        mock_file_handler.return_value = mock_file_instance
        
        mock_stream_instance = MagicMock()
        mock_stream.return_value = mock_stream_instance
        
        mock_logger = MagicMock()
        mock_logger.handlers = [] # Initial empty handlers
        mock_get_logger.return_value = mock_logger
        
        # Call function
        setup_logging()
        
        # Verify log directory creation
        mock_makedirs.assert_called_with("logs")
        
        # Verify handlers creation
        assert mock_file_handler.call_count == 1
        assert mock_stream.call_count == 1
        
        # Check if handlers were added to the logger
        assert mock_logger.addHandler.call_count == 2
        mock_logger.addHandler.assert_any_call(mock_file_instance)
        mock_logger.addHandler.assert_any_call(mock_stream_instance)
        
    def test_setup_logging_dir_exists(self):
        """Test setup_logging when directory already exists."""
        with patch("app.os.path.exists", return_value=True), \
             patch("app.os.makedirs") as mock_makedirs, \
             patch("app.ConcurrentRotatingFileHandler"), \
             patch("app.logging.StreamHandler"), \
             patch("app.logging.getLogger"), \
             patch("app.logging.info"):
            
            setup_logging()
            mock_makedirs.assert_not_called()
