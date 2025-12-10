"""Blueprints do módulo de manutenção da unidade."""

from conecta_senai.routes.manutencao_unidade.admin import manutencao_unidade_admin_bp
from conecta_senai.routes.manutencao_unidade.publico import manutencao_public_bp
from conecta_senai.routes.manutencao_unidade.visitante import (
    manutencao_unidade_paginas_publicas_bp,
    manutencao_unidade_visitante_bp,
)

__all__ = [
    "manutencao_unidade_admin_bp",
    "manutencao_public_bp",
    "manutencao_unidade_visitante_bp",
    "manutencao_unidade_paginas_publicas_bp",
]
