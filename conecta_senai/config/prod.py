"""Configurações específicas do ambiente de produção."""
import logging

from .base import BaseConfig


class ProdConfig(BaseConfig):
    """Aplicação configurada para execução em produção."""

    LOG_LEVEL = logging.INFO
