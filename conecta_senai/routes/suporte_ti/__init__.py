from .publico import suporte_ti_public_bp
from .admin import suporte_ti_admin_bp
from .visitante import (
    suporte_ti_paginas_publicas_bp,
    suporte_ti_visitante_bp,
)

__all__ = [
    "suporte_ti_public_bp",
    "suporte_ti_admin_bp",
    "suporte_ti_visitante_bp",
    "suporte_ti_paginas_publicas_bp",
]
