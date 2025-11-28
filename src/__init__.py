"""Compatibilidade para ambientes que importam o pacote ``src``.

Este módulo reexporta a função :func:`create_app` para cenários onde o
Gunicorn (ou outros servidores WSGI) são configurados com ``src:create_app``
como ponto de entrada. A aplicação continua hospedada no pacote
``conecta_senai`` e esta camada existe apenas para manter compatibilidade
com configurações antigas.
"""

from conecta_senai import create_app

__all__ = ["create_app"]
