"""Regras de negócio para o módulo de notícias."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from flask import current_app
from sqlalchemy import inspect
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from conecta_senai.models import db
from conecta_senai.models.imagem_noticia import ImagemNoticia
from conecta_senai.models.noticia import Noticia
from conecta_senai.repositories.noticia_repository import NoticiaRepository

UPLOAD_SUBDIR = Path("uploads") / "noticias"

_TABELA_IMAGENS_DISPONIVEL: bool | None = None


log = logging.getLogger(__name__)


def _obter_pasta_upload() -> Path:
    static_folder = Path(current_app.static_folder)
    pasta = static_folder / UPLOAD_SUBDIR
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _gerar_nome_arquivo(arquivo: FileStorage) -> str:
    nome_seguro = secure_filename(arquivo.filename or "")
    extensao = Path(nome_seguro).suffix
    return f"{uuid4().hex}{extensao}" if extensao else uuid4().hex


def _salvar_arquivo_imagem(arquivo: FileStorage) -> Tuple[str, str, bytes, str]:
    pasta = _obter_pasta_upload()
    nome_arquivo = _gerar_nome_arquivo(arquivo)
    caminho_absoluto = pasta / nome_arquivo
    arquivo.stream.seek(0)
    conteudo = arquivo.read()
    arquivo.stream.seek(0)
    caminho_absoluto.write_bytes(conteudo)
    caminho_relativo = (UPLOAD_SUBDIR / nome_arquivo).as_posix()
    content_type = arquivo.mimetype or "application/octet-stream"
    return nome_arquivo, caminho_relativo, conteudo, content_type


def _remover_arquivo(caminho_relativo: str | None) -> None:
    if not caminho_relativo:
        return
    static_folder = Path(current_app.static_folder).resolve()
    try:
        caminho = (static_folder / caminho_relativo).resolve()
    except FileNotFoundError:
        return
    if static_folder not in caminho.parents and caminho != static_folder:
        return
    try:
        caminho.unlink(missing_ok=True)
    except TypeError:  # Python < 3.8 compatibility
        if caminho.exists():
            caminho.unlink()
    except OSError:
        current_app.logger.warning(
            "Não foi possível remover o arquivo de imagem %s", caminho, exc_info=True
        )


def _registrar_tabela_imagens_indisponivel(exc: Exception | None = None) -> None:
    global _TABELA_IMAGENS_DISPONIVEL
    _TABELA_IMAGENS_DISPONIVEL = False
    if exc:
        current_app.logger.debug(
            "Tabela 'imagens_noticias' indisponível: %s", exc, exc_info=False
        )


def _tabela_imagens_disponivel(force_refresh: bool = False) -> bool:
    global _TABELA_IMAGENS_DISPONIVEL
    if _TABELA_IMAGENS_DISPONIVEL is not None and not force_refresh:
        return _TABELA_IMAGENS_DISPONIVEL

    try:
        bind = db.session.get_bind()
    except SQLAlchemyError:
        bind = None

    if bind is None:
        bind = db.engine

    try:
        inspector = inspect(bind)
        resultado = inspector.has_table(ImagemNoticia.__tablename__)
        if not resultado:
            try:
                current_app.logger.warning(
                    "Tabela 'imagens_noticias' ausente; criando automaticamente."
                )
            except RuntimeError:  # pragma: no cover - logger fora do contexto Flask
                log.warning("Tabela 'imagens_noticias' ausente; criando automaticamente.")

            ImagemNoticia.__table__.create(bind, checkfirst=True)

            inspector = inspect(bind)
            resultado = inspector.has_table(ImagemNoticia.__tablename__)
    except SQLAlchemyError as exc:  # pragma: no cover - introspecção defensiva
        _registrar_tabela_imagens_indisponivel(exc)
        return False

    _TABELA_IMAGENS_DISPONIVEL = resultado
    return resultado


def _extrair_caminho_relativo_de_url(url: str | None) -> str | None:
    if not url:
        return None
    prefixo = "/static/"
    if url.startswith(prefixo):
        return url[len(prefixo) :]
    return url.lstrip("/")


def _construir_url_publica(caminho_relativo: str | None) -> str | None:
    if not caminho_relativo:
        return None
    caminho = caminho_relativo.lstrip("/")
    if not caminho:
        return None
    return f"/static/{caminho}"


def _carregar_imagem_relacionada(
    noticia: Noticia,
) -> Tuple[ImagemNoticia | None, str | None, bool]:
    tabela_disponivel = _tabela_imagens_disponivel()
    imagem_relacionada: ImagemNoticia | None = None
    caminho_relativo: str | None = None

    if tabela_disponivel:
        try:
            imagem_relacionada = getattr(noticia, "imagem", None)
        except (ProgrammingError, SQLAlchemyError) as exc:
            _registrar_tabela_imagens_indisponivel(exc)
            tabela_disponivel = False
        else:
            if imagem_relacionada is not None:
                caminho_relativo = getattr(imagem_relacionada, "caminho_relativo", None)

    if caminho_relativo is None:
        caminho_relativo = _extrair_caminho_relativo_de_url(getattr(noticia, "imagem_url", None))

    return imagem_relacionada, caminho_relativo, tabela_disponivel


def _aplicar_imagem(noticia: Noticia, arquivo: FileStorage | None) -> Tuple[str | None, str | None]:
    """Aplica uma nova imagem à notícia e retorna o caminho removido."""

    if not arquivo or not arquivo.filename:
        return None, None

    nome_arquivo, caminho_relativo, conteudo, content_type = _salvar_arquivo_imagem(arquivo)
    imagem_relacionada, caminho_antigo, tabela_disponivel = _carregar_imagem_relacionada(noticia)

    if tabela_disponivel and imagem_relacionada is not None:
        imagem_relacionada.nome_arquivo = nome_arquivo
        imagem_relacionada.caminho_relativo = caminho_relativo
        imagem_relacionada.conteudo = conteudo
        imagem_relacionada.tem_conteudo = bool(conteudo)
        imagem_relacionada.content_type = content_type
        noticia.imagem_url = imagem_relacionada.url_publica
        return caminho_antigo, caminho_relativo

    if tabela_disponivel:
        try:
            noticia.imagem = ImagemNoticia(
                nome_arquivo=nome_arquivo,
                caminho_relativo=caminho_relativo,
                conteudo=conteudo,
                tem_conteudo=bool(conteudo),
                content_type=content_type,
            )
        except (ProgrammingError, SQLAlchemyError) as exc:
            _registrar_tabela_imagens_indisponivel(exc)
            tabela_disponivel = False
            noticia.imagem = None
        else:
            noticia.imagem_url = noticia.imagem.url_publica
            return caminho_antigo, caminho_relativo

    if tabela_disponivel:
        noticia.imagem = None
    noticia.imagem_url = _construir_url_publica(caminho_relativo)
    current_app.logger.debug(
        "Persistindo caminho da imagem no campo 'imagem_url' por indisponibilidade da tabela 'imagens_noticias'."
    )
    return caminho_antigo, caminho_relativo


def criar_noticia(dados: Dict[str, Any], arquivo_imagem: FileStorage | None = None) -> Noticia:
    """Persiste uma nova notícia validada."""

    caminho_salvo = None
    noticia = Noticia(**dados)
    try:
        if arquivo_imagem and arquivo_imagem.filename:
            _, caminho_salvo = _aplicar_imagem(noticia, arquivo_imagem)
        noticia = NoticiaRepository.add(noticia)
        return noticia
    except SQLAlchemyError as exc:  # pragma: no cover - erros de banco são delegados
        NoticiaRepository.rollback()
        if caminho_salvo:
            _remover_arquivo(caminho_salvo)
        raise exc


def atualizar_noticia(
    noticia: Noticia,
    dados: Dict[str, Any],
    arquivo_imagem: FileStorage | None = None,
) -> Noticia:
    """Atualiza a notícia informada com os dados fornecidos."""

    caminho_antigo = None
    caminho_novo = None
    if arquivo_imagem and arquivo_imagem.filename:
        caminho_antigo, caminho_novo = _aplicar_imagem(noticia, arquivo_imagem)

    for campo, valor in dados.items():
        setattr(noticia, campo, valor)

    try:
        NoticiaRepository.commit()
        if caminho_antigo and caminho_antigo != caminho_novo:
            _remover_arquivo(caminho_antigo)
        return noticia
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        if caminho_novo:
            _remover_arquivo(caminho_novo)
        raise exc


def excluir_noticia(noticia: Noticia) -> None:
    """Remove a notícia do banco de dados."""

    _, caminho_antigo, _ = _carregar_imagem_relacionada(noticia)
    try:
        NoticiaRepository.delete(noticia)
        if caminho_antigo:
            _remover_arquivo(caminho_antigo)
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        raise exc


def publicar_noticias_agendadas() -> dict[str, int]:
    """Ativa notícias agendadas cuja data de publicação já passou."""

    agora = datetime.now(timezone.utc)
    noticias_para_publicar = Noticia.query.filter(
        Noticia.ativo.is_(False),
        Noticia.data_publicacao <= agora,
    ).all()

    total = len(noticias_para_publicar)
    if total == 0:
        log.info("Nenhuma notícia agendada para publicar no momento.")
        return {"total": 0, "publicadas": 0, "falhas": 0}

    sucesso_count = 0
    falha_count = 0

    for noticia in noticias_para_publicar:
        try:
            noticia.ativo = True
            db.session.add(noticia)
            sucesso_count += 1
        except SQLAlchemyError:
            falha_count += 1
            log.exception(
                "Falha ao tentar publicar a notícia agendada com ID %s",
                noticia.id,
            )

    if sucesso_count > 0:
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            log.exception(
                "Erro ao commitar a publicação de notícias. Nenhuma alteração foi salva."
            )
            falha_count += sucesso_count
            sucesso_count = 0

    return {"total": total, "publicadas": sucesso_count, "falhas": falha_count}


def _normalizar_para_utc(data: datetime) -> datetime:
    if data.tzinfo is None:
        return data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


def _dias_uteis_decorridos(inicio: datetime, fim: datetime) -> int:
    data_inicio = _normalizar_para_utc(inicio).date()
    data_fim = _normalizar_para_utc(fim).date()

    if data_fim <= data_inicio:
        return 0

    dias_uteis = 0
    dia_atual = data_inicio

    while dia_atual < data_fim:
        if dia_atual.weekday() < 5:
            dias_uteis += 1
        dia_atual += timedelta(days=1)

    return dias_uteis


def remover_destaques_expirados() -> dict[str, int]:
    """Remove o destaque de notícias cuja data ultrapassou cinco dias úteis."""

    try:
        noticias_em_destaque = (
            Noticia.query.filter(
                Noticia.destaque.is_(True),
                Noticia.data_publicacao.isnot(None),
            ).all()
        )
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Erro ao buscar notícias em destaque para verificação de expiração.")
        return {"total": 0, "ajustados": 0, "falhas": 0}

    total = len(noticias_em_destaque)
    if total == 0:
        return {"total": 0, "ajustados": 0, "falhas": 0}

    agora = datetime.now(timezone.utc)
    ajustados = 0

    for noticia in noticias_em_destaque:
        data_publicacao = noticia.data_publicacao
        if not data_publicacao:
            continue

        dias_uteis = _dias_uteis_decorridos(data_publicacao, agora)
        if dias_uteis >= 5:
            noticia.destaque = False
            ajustados += 1

    if ajustados == 0:
        return {"total": total, "ajustados": 0, "falhas": 0}

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.exception("Erro ao remover destaques expirados de notícias.")
        return {"total": total, "ajustados": 0, "falhas": ajustados}

    log.info("Removidos %d destaques de notícias expiradas.", ajustados)
    return {"total": total, "ajustados": ajustados, "falhas": 0}
