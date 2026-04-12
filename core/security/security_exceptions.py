"""
Nombre del Módulo: core.security.security_exceptions

Descripción: Define protocolos o tipos principales: ``SecurityError``, ``SecurityServiceNotInitializedError``, ``InsufficientPermissionsError``, ``RateLimitExceededError``. Excepción base para errores de seguridad.
"""


class SecurityError(Exception):
    """Excepción base para errores de seguridad."""
    pass


class SecurityServiceNotInitializedError(SecurityError):
    """El servicio de seguridad no está inicializado."""
    pass


class InsufficientPermissionsError(SecurityError):
    """El usuario no tiene los permisos necesarios."""
    pass


class RateLimitExceededError(SecurityError):
    """Se excedió el límite de intentos permitidos."""
    pass
