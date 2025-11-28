"""Rotinas de convocação automática de turmas."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from flask import current_app
from sqlalchemy.orm import joinedload

from conecta_senai.models import db, InscricaoTreinamento, TurmaTreinamento
from conecta_senai.services.email_service import enviar_convocacao


def _carregar_inscricoes_pendentes() -> Iterable[InscricaoTreinamento]:
    """Retorna as inscrições que ainda não receberam convocação."""

    return (
        InscricaoTreinamento.query.options(
            joinedload(InscricaoTreinamento.usuario),
            joinedload(InscricaoTreinamento.turma).joinedload(
                TurmaTreinamento.treinamento
            ),
            joinedload(InscricaoTreinamento.turma).joinedload(
                TurmaTreinamento.instrutor
            ),
        )
        .filter(InscricaoTreinamento.convocado_em.is_(None))
        .all()
    )


def convocacao_automatica_job() -> None:
    """Executa a convocação automática de participantes."""

    logger = current_app.logger

    inscricoes_a_convocar = _carregar_inscricoes_pendentes()
    if not inscricoes_a_convocar:
        logger.debug("Nenhuma inscrição pendente de convocação encontrada.")
        return

    for inscricao in inscricoes_a_convocar:
        turma = getattr(inscricao, "turma", None)
        treinamento = getattr(turma, "treinamento", None) if turma else None
        if turma is None or treinamento is None:
            logger.warning(
                "Inscrição %s sem turma ou treinamento associado; ignorando.",
                getattr(inscricao, "id", "?"),
            )
            continue

        try:
            enviar_convocacao(inscricao, turma)
        except ValueError as exc:
            logger.warning(
                "Convocação ignorada para inscrição %s: %s",
                getattr(inscricao, "id", "?"),
                exc,
            )
            continue
        except Exception:  # pragma: no cover - apenas log
            logger.exception(
                "Falha ao enviar convocação automática para inscrição %s.",
                getattr(inscricao, "id", "?"),
            )
            continue

        inscricao.convocado_em = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:  # pragma: no cover - apenas log
        db.session.rollback()
        logger.exception(
            "Erro ao salvar o status das convocações automáticas no banco de dados.",
        )
        raise
