"""Configurações específicas do ambiente de testes automatizados."""
import logging

from .base import BaseConfig


class TestConfig(BaseConfig):
    """Aplicação configurada para execução de testes."""

    TESTING = True
    LOG_LEVEL = logging.WARNING
