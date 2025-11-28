"""Comandos CLI relacionados ao módulo de notícias."""

from datetime import datetime, timezone

import click
from flask import current_app

from conecta_senai.extensions import db
from conecta_senai.models.noticia import Noticia


def register_cli(app):
    """Registra comandos customizados no objeto :class:`Flask`."""

    @app.cli.command("seed_noticias")
    def seed_noticias():
        """Insere uma notícia de demonstração para testes rápidos."""

        exemplo_titulo = "Bem-vindo ao Conecta-SENAI"
        existente = Noticia.query.filter_by(titulo=exemplo_titulo).first()
        if existente:
            click.echo("Uma notícia de exemplo já está cadastrada. Nenhuma alteração realizada.")
            return

        noticia = Noticia(
            titulo=exemplo_titulo,
            resumo="Primeira notícia de teste",
            conteudo="Conteúdo de exemplo",
            autor="Sistema",
            destaque=True,
            ativo=True,
            data_publicacao=datetime.now(timezone.utc),
        )
        db.session.add(noticia)
        db.session.commit()
        current_app.logger.info("Seed de notícias criado.")
        click.echo("Notícia de demonstração criada com sucesso.")
