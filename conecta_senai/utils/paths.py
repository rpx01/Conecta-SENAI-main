"""Utilidades relacionadas a manipulação de caminhos de arquivos."""
from pathlib import Path


def ensure_path_is_safe(path: Path) -> bool:
    """Valida se o caminho fornecido não tenta sair do diretório base."""

    return ".." not in path.parts
