# -*- coding: utf-8 -*-
"""
Nombre del Módulo: validator_service.py
Descripción: Servicio de validación de datos. Centraliza las reglas de negocio 
             para asegurar la integridad de productos, códigos y cantidades.
"""
import re
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None

class ValidatorService:
    """
    Servicio centralizado para validación de entradas de usuario.
    Previene datos corruptos y mejora la experiencia de usuario.
    """

    @staticmethod
    def validate_product_code(code: str) -> ValidationResult:
        if not code or not code.strip():
            return ValidationResult(False, "El código del producto no puede estar vacío.")
        
        if len(code) < 3:
            return ValidationResult(False, "El código debe tener al menos 3 caracteres.")
            
        if not re.match(r"^[A-Z0-9_\-]+$", code.upper()):
            return ValidationResult(False, "El código solo puede contener letras, números, guiones y guiones bajos.")
            
        return ValidationResult(True)

    @staticmethod
    def validate_product_description(desc: str) -> ValidationResult:
        if not desc or not desc.strip():
            return ValidationResult(False, "La descripción es obligatoria.")
        return ValidationResult(True)

    @staticmethod
    def validate_positive_number(value: str, field_name: str = "Valor") -> ValidationResult:
        try:
            num = float(value.replace(',', '.'))
            if num <= 0:
                return ValidationResult(False, f"{field_name} debe ser mayor que cero.")
            return ValidationResult(True)
        except ValueError:
            return ValidationResult(False, f"{field_name} debe ser un número válido.")

    @staticmethod
    def validate_username(username: str) -> ValidationResult:
        if not username or len(username) < 3:
            return ValidationResult(False, "El usuario debe tener al menos 3 caracteres.")
        return ValidationResult(True)
        
    @staticmethod
    def validate_password_strength(password: str) -> ValidationResult:
        if not password or len(password) < 4: # Política simple por ahora
            return ValidationResult(False, "La contraseña debe tener al menos 4 caracteres.")
        return ValidationResult(True)
