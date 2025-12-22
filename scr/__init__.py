"""Compatibilidade para entrypoints que usam o módulo `scr`.

Este pacote reexporta :func:`create_app` para permitir que configurações de
servidor que referenciam equivocadamente ``scr.main:create_app`` continuem
funcionando.
"""
from conecta_senai.main import create_app

__all__ = ["create_app"]
