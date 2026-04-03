# -*- coding: utf-8 -*-
"""
Nombre del Módulo: security_service.py
Descripción: Servicio central de seguridad para la gestión de roles (RBAC), 
             autenticación de usuarios y verificación de permisos.
"""
from enum import Enum, auto
import logging
from typing import Dict, List, Set, Optional, Any

class UserRole(Enum):
    ADMIN = "admin"
    RESPONSABLE = "responsable"
    OPERARIO = "operario"
    INVITADO = "invitado"

class Permission(Enum):
    # Gestión de Usuarios
    MANAGE_USERS = auto()
    
    # Gestión de Productos
    VIEW_PRODUCTS = auto()
    CREATE_PRODUCT = auto()
    EDIT_PRODUCT = auto()
    DELETE_PRODUCT = auto()
    
    # Gestión de Fabricaciones
    VIEW_FABRICATIONS = auto()
    CREATE_FABRICATION = auto()
    EDIT_FABRICATION = auto()
    DELETE_FABRICATION = auto()
    
    # Gestión de Máquinas
    MANAGE_MACHINES = auto() # Crear, editar, borrar
    
    # Dashboard y Reportes
    VIEW_DASHBOARD = auto()
    GENERATE_REPORTS = auto()
    
    # Configuración
    MANAGE_SETTINGS = auto()
    
    # Historial
    VIEW_HISTORY = auto()

class SecurityService:
    """
    Servicio central de seguridad para autenticación y autorización (RBAC).
    """
    
    def __init__(self) -> None:
        self.logger = logging.getLogger("SecurityService")
        self.current_user: Optional[Dict[str, Any]] = None
        
        # Definición de Permisos por Rol
        self.role_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.ADMIN: {permission for permission in Permission}, # Todos los permisos
            
            UserRole.RESPONSABLE: {
                Permission.MANAGE_USERS, # Requerido para crear/editar/gestionar operarios
                Permission.VIEW_PRODUCTS, Permission.CREATE_PRODUCT, Permission.EDIT_PRODUCT, Permission.DELETE_PRODUCT,
                Permission.VIEW_FABRICATIONS, Permission.CREATE_FABRICATION, Permission.EDIT_FABRICATION, Permission.DELETE_FABRICATION,
                Permission.MANAGE_MACHINES,
                Permission.VIEW_DASHBOARD, Permission.GENERATE_REPORTS,
                Permission.VIEW_HISTORY,
                Permission.MANAGE_SETTINGS  # Para acceso a configuración
            },
            
            UserRole.OPERARIO: {
                Permission.VIEW_PRODUCTS, # Solo ver para consultar
                Permission.VIEW_FABRICATIONS, # Ver sus tareas
                Permission.VIEW_DASHBOARD # Limitado a su carga (controlado por lógica de UI)
            },
            
            UserRole.INVITADO: set()
        }

    def login_user(self, user_data: Any) -> bool:
        """
        Registra al usuario actual en el servicio de seguridad.
        """
        if not user_data:
            self.current_user = None
            return False
            
        self.current_user = user_data
        self.logger.info(f"Usuario autenticado: {getattr(user_data, 'username', 'Unknown')} con rol {getattr(user_data, 'role', 'Unknown')}")
        return True
        
    def logout(self) -> None:
        """Cierra la sesión del usuario actual."""
        if self.current_user:
            self.logger.info(f"Cerrando sesión de: {getattr(self.current_user, 'username', 'Unknown')}")
        self.current_user = None

    def get_current_role(self) -> UserRole:
        """Obtiene el rol del usuario actual como Enum."""
        if not self.current_user:
            return UserRole.INVITADO
            
        role_str = str(getattr(self.current_user, 'role', '')).lower()
        
        # Mapeo de strings de BD a Enum
        role_map: Dict[str, UserRole] = {
            "admin": UserRole.ADMIN,
            "administrador": UserRole.ADMIN,
            "responsable": UserRole.RESPONSABLE,
            "manager": UserRole.RESPONSABLE,
            "operario": UserRole.OPERARIO,
            "trabajador": UserRole.OPERARIO,
            "worker": UserRole.OPERARIO
        }
        
        return role_map.get(role_str, UserRole.INVITADO)

    def has_permission(self, permission: Permission) -> bool:
        """
        Verifica si el usuario actual tiene un permiso específico.
        """
        role = self.get_current_role()
        allowed_permissions = self.role_permissions.get(role, set())
        
        has_perm = permission in allowed_permissions
        
        if not has_perm:
            self.logger.warning(f"Acceso denegado: Rol {role} intentó {permission.name}")
            
        return has_perm

    def check_access(self, permission: Permission) -> bool:
        """Alias de has_permission para uso en decoradores."""
        return self.has_permission(permission)
