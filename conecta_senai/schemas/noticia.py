from __future__ import annotations

import logging
from typing import Any

from marshmallow import Schema, fields
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError


log = logging.getLogger(__name__)


class ImagemNoticiaSchema(Schema):
    id = fields.Int()
    nome_arquivo = fields.Str()
    caminho_relativo = fields.Str()
    url = fields.Str(attribute="url_publica", allow_none=True)


_imagem_schema = ImagemNoticiaSchema()


class NoticiaSchema(Schema):
    id = fields.Int()
    titulo = fields.Str(required=True)
    resumo = fields.Str(allow_none=True)
    conteudo = fields.Str(required=True)
    autor = fields.Str(allow_none=True)
    imagem_url = fields.Method("get_imagem_url")
    imagem = fields.Method("get_imagem", allow_none=True)
    destaque = fields.Bool()
    ativo = fields.Bool()
    marcar_calendario = fields.Bool(attribute="marcar_calendario")
    data_publicacao = fields.DateTime(allow_none=True)
    data_evento = fields.DateTime(allow_none=True)
    criado_em = fields.DateTime()
    atualizado_em = fields.DateTime()

    @staticmethod
    def _get_relacionamento_imagem(obj: Any):
        try:
            return getattr(obj, "imagem", None)
        except (ProgrammingError, SQLAlchemyError) as exc:
            log.debug("Falha ao carregar relacionamento imagem: %s", exc)
            return None

    def get_imagem(self, obj: Any):
        imagem = self._get_relacionamento_imagem(obj)
        if imagem is None:
            return None
        return _imagem_schema.dump(imagem)

    def get_imagem_url(self, obj: Any):
        imagem = self._get_relacionamento_imagem(obj)
        if imagem is not None:
            return getattr(imagem, "url_publica", None)
        return getattr(obj, "imagem_url", None)
