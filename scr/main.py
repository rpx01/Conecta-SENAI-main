"""Ponto de entrada compatível para Gunicorn/Flask."""
from conecta_senai.main import create_app

__all__ = ["create_app"]
