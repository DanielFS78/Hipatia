# -*- coding: utf-8 -*-
"""
Tests for PasswordService following the AAA pattern and strict testing guidelines.
"""
import pytest
from unittest.mock import patch, MagicMock, ANY
from core.security.password_service import PasswordService

@pytest.fixture
def password_service():
    """Provides a PasswordService instance for tests."""
    return PasswordService()

@pytest.mark.unit
class TestPasswordServiceHash:
    """Tests for the hash_password functionality."""

    def test_hash_password_valid_input_returns_hashed_string(self):
        # Arrange
        plain_password = "SecurePassword123"

        # Act
        hashed_password = PasswordService.hash_password(plain_password)

        # Assert
        assert isinstance(hashed_password, str)
        assert len(hashed_password) > 0
        assert hashed_password != plain_password
        assert hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$")  # bcrypt prefixes

    def test_hash_password_empty_input_returns_empty_string(self):
        # Arrange
        plain_password = ""

        # Act
        hashed_password = PasswordService.hash_password(plain_password)

        # Assert
        assert hashed_password == ""

    def test_hash_password_generates_unique_hashes_for_same_password(self):
        # Arrange
        plain_password = "SecurePassword123"

        # Act
        hash1 = PasswordService.hash_password(plain_password)
        hash2 = PasswordService.hash_password(plain_password)

        # Assert
        assert hash1 != hash2  # Due to salting, hashes should be different


@pytest.mark.unit
class TestPasswordServiceVerify:
    """Tests for the verify_password functionality."""

    def test_verify_password_correct_password_returns_true(self):
        # Arrange
        plain_password = "SecurePassword123"
        hashed_password = PasswordService.hash_password(plain_password)

        # Act
        is_valid = PasswordService.verify_password(plain_password, hashed_password)

        # Assert
        assert is_valid is True

    def test_verify_password_incorrect_password_returns_false(self):
        # Arrange
        plain_password = "SecurePassword123"
        wrong_password = "WrongPassword123"
        hashed_password = PasswordService.hash_password(plain_password)

        # Act
        is_valid = PasswordService.verify_password(wrong_password, hashed_password)

        # Assert
        assert is_valid is False

    def test_verify_password_empty_plain_password_returns_false(self):
        # Arrange
        plain_password = ""
        hashed_password = "$2b$12$SomeHashedPassword12345678901234567890123456789012"

        # Act
        is_valid = PasswordService.verify_password(plain_password, hashed_password)

        # Assert
        assert is_valid is False

    def test_verify_password_empty_hashed_password_returns_false(self):
        # Arrange
        plain_password = "SecurePassword123"
        hashed_password = ""

        # Act
        is_valid = PasswordService.verify_password(plain_password, hashed_password)

        # Assert
        assert is_valid is False

    def test_verify_password_invalid_hash_format_returns_false_and_logs_error(self, password_service):
        # Arrange
        plain_password = "SecurePassword123"
        invalid_hash = "not_a_valid_bcrypt_hash"
        
        # Act
        with patch('logging.Logger.error') as mock_logger_error:
            is_valid = password_service.verify_password(plain_password, invalid_hash)

        # Assert
        assert is_valid is False
        assert mock_logger_error.call_count == 1
        mock_logger_error.assert_called_once_with(ANY)
        args = mock_logger_error.call_args[0][0]
        assert "Error verificando contraseña" in args


@pytest.mark.unit
class TestPasswordServiceValidate:
    """Tests for the validate_password functionality."""

    def test_validate_password_valid_password_returns_true(self):
        # Arrange
        password = "SecurePass1"

        # Act
        is_valid, msg = PasswordService.validate_password(password)

        # Assert
        assert is_valid is True
        assert msg == ""

    def test_validate_password_too_short_returns_false(self):
        # Arrange
        password = "Short1"

        # Act
        is_valid, msg = PasswordService.validate_password(password)

        # Assert
        assert is_valid is False
        assert "8 caracteres" in msg

    def test_validate_password_no_number_returns_false(self):
        # Arrange
        password = "NoNumberHere"

        # Act
        is_valid, msg = PasswordService.validate_password(password)

        # Assert
        assert is_valid is False
        assert "número" in msg

    def test_validate_password_no_letter_returns_false(self):
        # Arrange
        password = "123456789"

        # Act
        is_valid, msg = PasswordService.validate_password(password)

        # Assert
        assert is_valid is False
        assert "letra" in msg

    def test_validate_password_empty_returns_false(self):
        # Arrange
        password = ""

        # Act
        is_valid, msg = PasswordService.validate_password(password)

        # Assert
        assert is_valid is False
        assert "vacía" in msg
