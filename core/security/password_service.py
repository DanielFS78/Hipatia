"""
Nombre del Módulo: core.security.password_service

Descripción: Define protocolos o tipos principales: ``PasswordService``. Servicio para el manejo seguro de contraseñas utilizando bcrypt. Integración típica con: ``bcrypt``.
"""

import bcrypt
import logging

class PasswordService:
    """
    Servicio para el manejo seguro de contraseñas utilizando bcrypt.
    Reemplaza el uso de SHA-256 simple.
    """
    
    def __init__(self) -> None:
        self.logger = logging.getLogger("PasswordService")

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Genera un hash seguro para la contraseña proporcionada usando bcrypt.
        
        Args:
            plain_password: La contraseña en texto plano.
            
        Returns:
            El hash de la contraseña como string (utf-8).
        """
        if not plain_password:
            return ""
            
        # bcrypt requiere bytes
        password_bytes = plain_password.encode('utf-8')
        # generar salt y hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # devolver como string para almacenamiento en BD
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica si la contraseña coincide con el hash almacenado.
        
        Args:
            plain_password: La contraseña en texto plano a verificar.
            hashed_password: El hash almacenado en la base de datos.
            
        Returns:
            True si coinciden, False en caso contrario.
        """
        if not plain_password or not hashed_password:
            return False
            
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            # Capturar errores de formato de hash inválido, etc.
            logging.getLogger("PasswordService").error(f"Error verificando contraseña: {e}")
            return False

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Valida que la contraseña cumpla con los requisitos de complejidad.
        
        Requisitos:
        - Mínimo 8 caracteres
        - Al menos un número
        - Al menos una letra
        
        Returns:
            Tuple[bool, str]: (Es válida, Mensaje de error si no lo es)
        """
        if not password:
             return False, "La contraseña no puede estar vacía."

        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        
        import re
        if not re.search(r"\d", password):
            return False, "La contraseña debe contener al menos un número."
            
        if not re.search(r"[a-zA-Z]", password):
            return False, "La contraseña debe contener al menos una letra."
            
        return True, ""
