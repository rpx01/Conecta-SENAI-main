"""Jobs relacionados a notícias."""

import logging

from conecta_senai.services.noticia_service import (
    publicar_noticias_agendadas as _publicar_noticias_agendadas,
    remover_destaques_expirados as _remover_destaques_expirados,
)

log = logging.getLogger(__name__)


def publicar_noticias_agendadas() -> dict[str, int]:
    """Executa a publicação de notícias agendadas com registro em log."""

    resultado = _publicar_noticias_agendadas()

    if resultado["total"] == 0:
        return resultado

    if resultado["publicadas"]:
        log.info(
            "Publicadas %d notícias agendadas com sucesso.",
            resultado["publicadas"],
        )

    if resultado["falhas"]:
        log.warning(
            "%d notícias agendadas não puderam ser publicadas devido a erros.",
            resultado["falhas"],
        )

    return resultado


def remover_destaques_expirados() -> dict[str, int]:
    """Remove destaques expirados registrando o total afetado."""

    resultado = _remover_destaques_expirados()

    ajustados = resultado.get("ajustados", 0)
    if ajustados:
        log.info("Removidos %d destaques expirados de notícias.", ajustados)
    else:
        log.debug("Nenhum destaque expirado precisou ser removido no ciclo atual.")

    return resultado
