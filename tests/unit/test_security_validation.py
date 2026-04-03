# -*- coding: utf-8 -*-
"""Tests unitarios para SecurityService y ValidatorService (login, permisos, validaciones)."""
import pytest
from core.security.security_service import SecurityService, Permission, UserRole
from unittest.mock import MagicMock
from core.validation.validator_service import ValidatorService

pytestmark = pytest.mark.unit


class TestSecurityService:
    def test_initial_state(self):
        service = SecurityService()
        assert service.current_user is None
        assert service.get_current_role() == UserRole.INVITADO

    def test_login_logout(self):
        service = SecurityService()
        user_data = MagicMock(spec=['username', 'role'])
        user_data.username = "admin"
        user_data.role = "admin"
        
        assert service.login_user(user_data) is True
        assert service.current_user == user_data
        assert service.get_current_role() == UserRole.ADMIN
        
        service.logout()
        assert service.current_user is None
        assert service.get_current_role() == UserRole.INVITADO

    def test_permissions_admin(self):
        service = SecurityService()
        service.login_user(MagicMock(spec=['role'], role="admin"))
        assert service.has_permission(Permission.MANAGE_USERS) is True
        assert service.has_permission(Permission.DELETE_PRODUCT) is True

    def test_permissions_operario(self):
        service = SecurityService()
        service.login_user(MagicMock(spec=['role'], role="operario"))
        
        # Debe tener
        assert service.has_permission(Permission.VIEW_FABRICATIONS) is True
        
        # No debe tener
        assert service.has_permission(Permission.DELETE_PRODUCT) is False
        assert service.has_permission(Permission.MANAGE_USERS) is False

class TestValidatorService:
    def test_validate_product_code(self):
        assert ValidatorService.validate_product_code("PROD-001").is_valid is True
        assert ValidatorService.validate_product_code("").is_valid is False
        assert ValidatorService.validate_product_code("A").is_valid is False # Too short
        assert ValidatorService.validate_product_code("PROD 001").is_valid is False # Invalid char space

    def test_validate_product_description(self):
        # Valid descriptions
        assert ValidatorService.validate_product_description("Valid description").is_valid is True
        # Invalid descriptions
        assert ValidatorService.validate_product_description("").is_valid is False
        assert ValidatorService.validate_product_description("   ").is_valid is False  # Whitespace only
        assert ValidatorService.validate_product_description(None).is_valid is False  # type: ignore[arg-type]

    def test_validate_positive_number(self):
        assert ValidatorService.validate_positive_number("10.5").is_valid is True
        assert ValidatorService.validate_positive_number("10,5").is_valid is True # Comma handling
        assert ValidatorService.validate_positive_number("-5").is_valid is False
        assert ValidatorService.validate_positive_number("abc").is_valid is False
        assert ValidatorService.validate_positive_number("0").is_valid is False  # Zero is not positive

    def test_validate_username(self):
        # Valid usernames
        assert ValidatorService.validate_username("abc").is_valid is True
        assert ValidatorService.validate_username("longusername").is_valid is True
        # Invalid usernames
        assert ValidatorService.validate_username("ab").is_valid is False  # Too short
        assert ValidatorService.validate_username("").is_valid is False
        assert ValidatorService.validate_username(None).is_valid is False # type: ignore[arg-type]

    def test_validate_password(self):
        assert ValidatorService.validate_password_strength("1234").is_valid is True
        assert ValidatorService.validate_password_strength("123").is_valid is False
