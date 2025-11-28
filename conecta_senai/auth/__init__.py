"""Pacote com a lógica de autenticação e autorização."""
from .decorators import admin_required, login_required, verificar_admin, verificar_autenticacao
from .routes import auth_bp
from .reset_routes import auth_reset_bp

__all__ = [
    "admin_required",
    "auth_bp",
    "auth_reset_bp",
    "login_required",
    "verificar_admin",
    "verificar_autenticacao",
]
