from __future__ import annotations
import os
import base64
from typing import (
    Iterable,
    Optional,
    Dict,
    Any,
    List,
    Union,
    TYPE_CHECKING,
    Callable,
)
import logging
import re
import time as time_module
import threading
from collections import deque

import resend
from flask import current_app, render_template
from types import SimpleNamespace
from datetime import time, date
from resend.exceptions import ResendError

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from conecta_senai.models.treinamento import TurmaTreinamento
    from conecta_senai.models.instrutor import Instrutor

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
# Permite definir o remetente tanto via MAIL_FROM quanto RESEND_FROM
DEFAULT_FROM = os.getenv("MAIL_FROM") or os.getenv(
    "RESEND_FROM", "no-reply@example.com"
)
DEFAULT_REPLY_TO = os.getenv("RESEND_REPLY_TO")

Address = Union[str, Iterable[str]]

# Intervalo mínimo entre notificações para respeitar o limite de 2 requisições
# por segundo imposto pelo provedor externo.
RATE_LIMIT_DELAY = 0.5
MAX_EMAIL_RETRIES = 2


class RateLimiter:
    """Decorator que limita a taxa de execução de uma função."""

    def __init__(self, max_calls: int, period: int = 1) -> None:
        self.calls: deque[float] = deque()
        self.period = period
        self.max_calls = max_calls
        self.lock = threading.Lock()

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self.lock:
                now = time_module.monotonic()
                while self.calls and now - self.calls[0] >= self.period:
                    self.calls.popleft()

                if len(self.calls) >= self.max_calls:
                    sleep_for = (self.calls[0] + self.period) - now
                    if sleep_for > 0:
                        time_module.sleep(sleep_for)
                        now = time_module.monotonic()
                        while (
                            self.calls and now - self.calls[0] >= self.period
                        ):
                            self.calls.popleft()

                self.calls.append(time_module.monotonic())

            return func(*args, **kwargs)

        return wrapper


def _normalize(addr: Address | None) -> Optional[List[str]]:
    """Converte o destinatário em lista de strings."""

    if addr is None:
        return None
    if isinstance(addr, str):
        return [addr]
    return list(addr)


def _parse_time(value: Any) -> time | None:
    """Tenta extrair uma instância de ``time`` a partir de diferentes formatos."""

    if isinstance(value, time):
        return value
    if isinstance(value, str):
        digits = [int(x) for x in re.findall(r"\d+", value)]
        if digits:
            hour = digits[0]
            minute = digits[1] if len(digits) > 1 else 0
            try:
                return time(hour, minute)
            except ValueError:
                return None
    return None


def build_turma_context(turma: Any) -> SimpleNamespace:
    """Monta o contexto mínimo usado nos templates de e-mail de turmas."""

    treino = getattr(turma, "treinamento", None)
    return SimpleNamespace(
        treinamento=SimpleNamespace(nome=getattr(treino, "nome", "")),
        nome=getattr(turma, "nome", ""),
        instrutor=getattr(turma, "instrutor", None),
        data_inicio=getattr(turma, "data_inicio", None),
        data_termino=getattr(turma, "data_fim", None),
        horario_inicio=_parse_time(
            getattr(turma, "horario_inicio", getattr(turma, "horario", None))
        )
        or time(0, 0),
        horario_fim=_parse_time(
            getattr(turma, "horario_fim", getattr(turma, "horario", None))
        )
        or time(0, 0),
        local=getattr(turma, "local", getattr(turma, "local_realizacao", "")),
        capacidade_maxima=getattr(turma, "capacidade_maxima", None),
    )


def build_user_context(nome: str) -> SimpleNamespace:
    """Cria um namespace simples apenas com o nome do usuário."""

    return SimpleNamespace(name=nome)


@RateLimiter(max_calls=2, period=1)
def send_email(
    to: Address,
    subject: str,
    html: str,
    text: Optional[str] = None,
    cc: Address | None = None,
    bcc: Address | None = None,
    reply_to: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    tags: Optional[List[Dict[str, str]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    from_: Optional[str] = None,
) -> Dict[str, Any]:
    """Envia e-mail via Resend."""
    params = {
        "from": from_ or DEFAULT_FROM,
        "to": _normalize(to),
        "subject": subject,
        "html": html,
    }
    if text:
        params["text"] = text
    if cc:
        params["cc"] = _normalize(cc)
    if bcc:
        params["bcc"] = _normalize(bcc)
    if reply_to or DEFAULT_REPLY_TO:
        params["reply_to"] = reply_to or DEFAULT_REPLY_TO
    if headers:
        params["headers"] = headers
    if tags:
        params["tags"] = tags
    attachments = list(attachments) if attachments else []
    logo_path = None
    try:
        logo_path = os.path.join(
            current_app.static_folder, "img", "Logo-assinatura do e-mail.png"
        )
    except RuntimeError:
        logo_path = None

    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        attachments.append(
            {
                "filename": "logo_assinatura.png",
                "content": encoded,
                "content_id": "logo_assinatura",
            }
        )
    else:
        try:
            current_app.logger.warning(
                f"Logo de assinatura não encontrado em: {logo_path}"
            )
        except RuntimeError:
            pass

    if attachments:
        params["attachments"] = attachments

    log.debug(
        "EMAIL_SEND_START", extra={"to": params["to"], "subject": subject}
    )
    for attempt in range(1, MAX_EMAIL_RETRIES + 1):
        try:
            result = resend.Emails.send(params)
            log.info(
                "EMAIL_SEND_SUCCESS",
                extra={"email_id": result.get("id"), "subject": subject},
            )
            return result
        except ResendError as exc:  # pragma: no cover - network failure
            if (
                getattr(exc, "code", None) == 429
                and attempt < MAX_EMAIL_RETRIES
            ):
                log.warning(
                    "EMAIL_RATE_LIMIT_HIT",
                    extra={"subject": subject, "attempt": attempt},
                )
                time_module.sleep(RATE_LIMIT_DELAY)
                continue
            log.error(
                "EMAIL_SEND_FAILURE",
                extra={"subject": subject, "error": str(exc)},
            )
            raise


def render_email_template(name: str, **ctx: Any) -> str:
    template = current_app.jinja_env.get_or_select_template(f"email/{name}")
    return template.render(**ctx)


def _resolve_participante_nome(inscricao: Any) -> str:
    """Retorna o nome do participante priorizando o registro da inscrição."""

    if getattr(inscricao, "nome", None):
        return inscricao.nome

    usuario = getattr(inscricao, "usuario", None)
    if usuario is None:
        return ""

    return (
        getattr(usuario, "nome", None)
        or getattr(usuario, "name", None)
        or ""
    )


def _resolve_participante_email(inscricao: Any) -> str:
    """Obtém o e-mail do participante a partir da inscrição ou do usuário."""

    email = getattr(inscricao, "email", "") or ""
    if email:
        return email

    usuario = getattr(inscricao, "usuario", None)
    if usuario:
        return getattr(usuario, "email", "") or ""

    return ""


def _formatar_periodo(
    data_inicio: date | None, data_fim: date | None
) -> str:
    """Gera o texto do período apresentado no e-mail de convocação."""

    if data_inicio and data_fim:
        return (
            f"De {data_inicio.strftime('%d/%m/%Y')} "
            f"a {data_fim.strftime('%d/%m/%Y')}"
        )

    if data_inicio:
        return data_inicio.strftime("%d/%m/%Y")

    if data_fim:
        return data_fim.strftime("%d/%m/%Y")

    return ""


def _formatar_periodo_texto(
    data_inicio: str | None, data_fim: str | None
) -> str:
    """Formata período já convertido em texto para exibição em e-mails."""

    if data_inicio and data_fim:
        return f"De {data_inicio} a {data_fim}"

    if data_inicio:
        return data_inicio

    if data_fim:
        return data_fim

    return ""


def _montar_dados_turma_email(turma: Any) -> Dict[str, Any]:
    """Monta o dicionário padrão com informações da turma para e-mails."""

    treinamento = getattr(turma, "treinamento", None)
    periodo = _formatar_periodo(
        getattr(turma, "data_inicio", None),
        getattr(turma, "data_fim", None),
    )

    instrutor = getattr(turma, "instrutor", None)
    instrutor_nome = getattr(instrutor, "nome", None) or "Não definido"

    local_pratica = getattr(turma, "local_pratica", None)
    tem_pratica = bool(getattr(treinamento, "tem_pratica", False))
    if not local_pratica and tem_pratica:
        local_pratica = getattr(treinamento, "local_pratica", None)

    return {
        "treinamento_nome": getattr(treinamento, "nome", "") or "",
        "treinamento_codigo": getattr(treinamento, "codigo", "") or "",
        "periodo": periodo,
        "horario": getattr(turma, "horario", "") or "",
        "carga_horaria": getattr(treinamento, "carga_horaria", None),
        "instrutor_nome": instrutor_nome,
        "local_realizacao": getattr(turma, "local_realizacao", "") or "",
        "teoria_online": bool(getattr(turma, "teoria_online", False)),
        "tem_pratica": tem_pratica,
        "local_pratica": local_pratica,
    }


def _aplicar_diff_em_dados_antigos(
    dados_base: Dict[str, Any], diff: Dict[str, Any]
) -> Dict[str, Any]:
    """Retorna cópia dos dados aplicando valores antigos presentes no diff."""

    dados_antigos = dict(dados_base)

    data_inicio_antiga = diff.get("data_inicio", (None, None))[0]
    data_fim_antiga = diff.get("data_fim", (None, None))[0]
    if data_inicio_antiga or data_fim_antiga:
        dados_antigos["periodo"] = _formatar_periodo_texto(
            data_inicio_antiga,
            data_fim_antiga,
        )

    if "horario" in diff:
        dados_antigos["horario"] = diff["horario"][0] or ""

    if "local_realizacao" in diff:
        dados_antigos["local_realizacao"] = (
            diff["local_realizacao"][0] or ""
        )

    if "instrutor" in diff:
        dados_antigos["instrutor_nome"] = (
            diff["instrutor"][0] or "Não definido"
        )

    if "teoria_online" in diff:
        dados_antigos["teoria_online"] = bool(diff["teoria_online"][0])

    for chave in (
        "treinamento_nome",
        "treinamento_codigo",
        "carga_horaria",
        "tem_pratica",
        "local_pratica",
    ):
        if chave in diff:
            dados_antigos[chave] = diff[chave][0]

    return dados_antigos


def enviar_convocacao(
    inscricao: Any, turma: Any, send_email_fn: Callable[..., Any] = send_email
) -> None:
    """Envia e-mail de convocação para um inscrito."""
    treinamento = getattr(turma, "treinamento", None)
    if treinamento is None:
        raise ValueError("Turma sem treinamento associado")

    destinatario = _resolve_participante_email(inscricao)
    if not destinatario:
        raise ValueError("Inscrição sem e-mail cadastrado")

    participante_nome = _resolve_participante_nome(inscricao)
    log.info(f"Tentando enviar e-mail de convocação para {destinatario}")

    is_teoria_online = bool(getattr(turma, "teoria_online", False))
    has_tem_pratica = bool(getattr(treinamento, "tem_pratica", False))

    data_inicio = getattr(turma, "data_inicio", None)
    data_fim = getattr(turma, "data_fim", None)
    periodo = _formatar_periodo(data_inicio, data_fim)

    instrutor = getattr(getattr(turma, "instrutor", None), "nome", "A definir")
    local_realizacao = getattr(turma, "local_realizacao", "")

    html = render_template(
        "email/convocacao.html.j2",
        nome=participante_nome,
        nome_do_treinamento=getattr(treinamento, "nome", ""),
        periodo=periodo,
        horario=getattr(turma, "horario", ""),
        carga_horaria=getattr(treinamento, "carga_horaria", ""),
        instrutor=instrutor,
        local_de_realizacao=local_realizacao,
        email_fornecido_na_inscricao=destinatario,
        local_da_pratica=local_realizacao,
        teoria_online=is_teoria_online,
        tem_pratica=has_tem_pratica,
    )

    attachments: List[Dict[str, Any]] = []
    if is_teoria_online:
        try:
            file_path = os.path.join(
                current_app.static_folder,
                "docs",
                "Tutorial de Acesso e Navegação - Aluno Anglo.pdf",
            )
            file_name = "Tutorial de Acesso e Navegação - Aluno Anglo.pdf"
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            attachments.append({"filename": file_name, "content": encoded})
        except FileNotFoundError:
            current_app.logger.error("Arquivo de tutorial não encontrado.")

    data_inicio_str = data_inicio.strftime("%d/%m/%Y") if data_inicio else ""
    subject = (
        f"Convocação: {getattr(treinamento, 'nome', '')} — {data_inicio_str}"
    )
    if send_email_fn is send_email:
        send_email_fn(
            to=destinatario,
            subject=subject,
            html=html,
            attachments=attachments,
        )
    else:
        send_email_fn(to=destinatario, subject=subject, html=html)
    log.info(f"E-mail de convocação enviado com sucesso para {destinatario}")


def listar_emails_secretaria() -> List[str]:
    """Retorna e-mails da secretaria de treinamentos."""
    from conecta_senai.models.secretaria_treinamentos import (
        SecretariaTreinamentos,
    )  # lazy import

    registros = SecretariaTreinamentos.query.all()
    return [r.email for r in registros if getattr(r, "email", None)]


def send_turma_alterada_secretaria(
    emails: Iterable[str], dados_antigos: Dict[str, Any], turma: Any
) -> None:
    """Envia e-mail comparando dados antigos e novos de uma turma."""
    turma_ctx = build_turma_context(turma)
    dados_novos = _montar_dados_turma_email(turma)
    subject = (
        "Alteração de Agendamento de Turma: "
        f"{turma_ctx.treinamento.nome} - Turma {turma_ctx.nome}"
    )
    dados_antigos_completos = dict(dados_novos)
    dados_antigos_completos.update(dados_antigos or {})

    html = render_email_template(
        "turma_alterada_secretaria.html.j2",
        dados_antigos=dados_antigos_completos,
        dados_novos=dados_novos,
        turma=turma_ctx,
    )
    send_email(list(emails), subject, html)


def send_turma_alterada_email(dados_antigos: dict, dados_novos: dict):
    """Envia e-mail à secretaria informando alteração de uma turma."""
    try:
        recipients = listar_emails_secretaria()
        if not recipients:
            current_app.logger.warning(
                "Nenhum e-mail de secretaria encontrado para "
                "notificação de turma alterada."
            )
            return

        dados_antigos_completos = dict(dados_novos)
        dados_antigos_completos.update(dados_antigos or {})

        html_body = render_template(
            "email/turma_alterada_secretaria.html.j2",
            dados_antigos=dados_antigos_completos,
            dados_novos=dados_novos,
        )

        subject = (
            "Alteração de Agendamento de Turma: "
            f"{dados_novos.get('treinamento_nome')}"
        )
        send_email(recipients, subject, html_body)
        current_app.logger.info(
            (
                "E-mail de alteração da turma "
                f"'{dados_novos.get('treinamento_nome')}' "
                "enviado para a secretaria."
            )
        )
    except Exception as e:  # pragma: no cover - log de erro
        current_app.logger.error(
            f"Falha ao enviar e-mail de turma alterada: {e}", exc_info=True
        )


def send_treinamento_desmarcado_email(
    recipients: Iterable[str], turma: "TurmaTreinamento"
) -> None:
    """Envia e-mail informando sobre o cancelamento de um treinamento."""
    recipients_list = list(recipients)
    if not recipients_list:
        return

    treinamento = getattr(turma, "treinamento", None)
    periodo = ""
    if getattr(turma, "data_inicio", None) and getattr(
        turma, "data_fim", None
    ):
        periodo = (
            f"{turma.data_inicio.strftime('%d/%m/%Y')} a "
            f"{turma.data_fim.strftime('%d/%m/%Y')}"
        )
    elif getattr(turma, "data_inicio", None):
        periodo = turma.data_inicio.strftime("%d/%m/%Y")

    turma_ctx = SimpleNamespace(
        treinamento=SimpleNamespace(
            nome=getattr(treinamento, "nome", ""),
            codigo=getattr(treinamento, "codigo", ""),
            carga_horaria=getattr(treinamento, "carga_horaria", None),
            tem_pratica=getattr(treinamento, "tem_pratica", False),
        ),
        periodo=periodo,
        horario=getattr(turma, "horario", ""),
        instrutor=getattr(turma, "instrutor", None),
        local=getattr(turma, "local_realizacao", ""),
        local_pratica=getattr(turma, "local_pratica", None),
        teoria_online=getattr(turma, "teoria_online", False),
    )

    subject = f"Treinamento desmarcado - {turma_ctx.treinamento.nome}"
    html = render_email_template(
        "treinamento_desmarcado.html.j2", turma=turma_ctx
    )
    send_email(recipients_list, subject, html)


def send_nova_turma_instrutor_email(
    turma: "TurmaTreinamento",
    instrutor: "Instrutor",
) -> None:
    """Envia um e-mail para o instrutor informando sobre a nova turma."""
    if not instrutor or not getattr(instrutor, "email", None):
        return

    treinamento = getattr(turma, "treinamento", None)
    carga_horaria = getattr(treinamento, "carga_horaria", None)
    if carga_horaria is not None:
        carga_horaria = f"{carga_horaria} horas"
    else:
        carga_horaria = "-"

    horario = getattr(turma, "horario", None)
    if not horario:
        hora_inicio = _parse_time(getattr(turma, "horario_inicio", None))
        hora_fim = _parse_time(getattr(turma, "horario_fim", None))
        if hora_inicio and hora_fim:
            horario = f"{hora_inicio.strftime('%H:%M')} às {hora_fim.strftime('%H:%M')}"
        elif hora_inicio:
            horario = f"A partir das {hora_inicio.strftime('%H:%M')}"
        else:
            horario = "-"

    html = render_email_template(
        "nova_turma_instrutor.html.j2",
        instrutor_nome=getattr(instrutor, "nome", ""),
        treinamento_nome=getattr(treinamento, "nome", ""),
        treinamento_codigo=getattr(treinamento, "codigo", "-") or "-",
        data_inicio=(
            turma.data_inicio.strftime("%d/%m/%Y")
            if getattr(turma, "data_inicio", None)
            else ""
        ),
        data_fim=(
            turma.data_fim.strftime("%d/%m/%Y")
            if getattr(turma, "data_fim", None)
            else None
        ),
        horario=horario,
        carga_horaria=carga_horaria,
        instrutor_antigo=getattr(instrutor, "nome", "-") or "-",
        local_realizacao=getattr(turma, "local_realizacao", "-") or "-",
        teoria_online=getattr(turma, "teoria_online", False),
        tem_pratica=getattr(treinamento, "tem_pratica", False),
        local_pratica=getattr(turma, "local_pratica", "-") or "-",
    )
    subject = f"Nova turma designada - {getattr(treinamento, 'nome', '')}"
    send_email(instrutor.email, subject, html)


def notificar_nova_turma(turma: "TurmaTreinamento") -> None:
    """Notifica instrutor e secretaria sobre criação de nova turma."""
    treinamento = getattr(turma, "treinamento", None)
    if not treinamento:
        return

    fmt = "%d/%m/%Y"
    data_inicio = (
        turma.data_inicio.strftime(fmt)
        if getattr(turma, "data_inicio", None)
        else ""
    )
    data_fim = (
        turma.data_fim.strftime(fmt)
        if getattr(turma, "data_fim", None)
        else None
    )
    ctx = {
        "treinamento_nome": getattr(treinamento, "nome", ""),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "horario": getattr(turma, "horario", "-") or "-",
        "local_realizacao": getattr(turma, "local_realizacao", "-") or "-",
    }

    instrutor = getattr(turma, "instrutor", None)
    if instrutor and getattr(instrutor, "email", None):
        send_nova_turma_instrutor_email(turma, instrutor)

    emails_secretaria = listar_emails_secretaria()
    if emails_secretaria:
        turma_ctx = build_turma_context(turma)
        html_sec = render_email_template(
            "nova_turma_secretaria.html.j2",
            turma=turma_ctx,
        )
        subject_sec = f"Nova turma cadastrada - {ctx['treinamento_nome']}"
        send_email(emails_secretaria, subject_sec, html_sec)


def notificar_atualizacao_turma(
    turma: "TurmaTreinamento",
    diff: Dict[str, Any],
    instrutor_antigo: "Instrutor" | None,
    *,
    notificar_secretaria: bool = True,
) -> None:
    """Notifica secretaria e instrutores sobre alterações em uma turma."""
    if not diff:
        return

    treinamento = getattr(turma, "treinamento", None)
    nome_treinamento = getattr(treinamento, "nome", "")

    turma_ctx = build_turma_context(turma)

    dados_novos = _montar_dados_turma_email(turma)
    dados_antigos = _aplicar_diff_em_dados_antigos(dados_novos, diff)

    emails_secretaria = listar_emails_secretaria()
    if notificar_secretaria and emails_secretaria:
        send_turma_alterada_email(dados_antigos, dados_novos)
        time_module.sleep(RATE_LIMIT_DELAY)

    instrutor_atual = getattr(turma, "instrutor", None)

    # ``instrutor_antigo`` pode ser uma instância ou apenas o ID.
    instrutor_antigo_obj = instrutor_antigo
    if instrutor_antigo_obj and not getattr(
        instrutor_antigo_obj, "email", None
    ):
        try:  # tenta carregar o instrutor a partir do ID
            from conecta_senai.models.instrutor import Instrutor  # lazy import
            from conecta_senai.models import db

            instrutor_antigo_obj = db.session.get(
                Instrutor, instrutor_antigo_obj
            )
        except Exception:  # pragma: no cover - fallback silencioso
            instrutor_antigo_obj = None

    antigo_id = getattr(instrutor_antigo_obj, "id", None)
    atual_id = getattr(instrutor_atual, "id", None)

    if antigo_id and antigo_id != atual_id:
        if getattr(instrutor_antigo_obj, "email", None):
            turma_ctx = SimpleNamespace(
                treinamento=SimpleNamespace(
                    nome=getattr(treinamento, "nome", ""),
                    codigo=getattr(treinamento, "codigo", ""),
                    carga_horaria=getattr(treinamento, "carga_horaria", None),
                    tem_pratica=getattr(treinamento, "tem_pratica", False),
                ),
                data_inicio=getattr(turma, "data_inicio", None),
                data_termino=getattr(turma, "data_fim", None),
                horario=getattr(turma, "horario", ""),
                local=getattr(turma, "local_realizacao", ""),
                teoria_online=getattr(turma, "teoria_online", False),
                local_pratica=getattr(turma, "local_pratica", None),
            )

            html_rem = render_email_template(
                "instrutor_removido.html.j2",
                instrutor_nome=getattr(instrutor_antigo_obj, "nome", ""),
                turma=turma_ctx,
            )
            subject_rem = f"Remanejamento de Turma - {nome_treinamento}"
            send_email(instrutor_antigo_obj.email, subject_rem, html_rem)
            time_module.sleep(RATE_LIMIT_DELAY)

    if (
        atual_id
        and antigo_id != atual_id
        and getattr(instrutor_atual, "email", None)
    ):
        send_nova_turma_instrutor_email(turma, instrutor_atual)
        time_module.sleep(RATE_LIMIT_DELAY)
    elif (
        atual_id
        and antigo_id == atual_id
        and getattr(instrutor_atual, "email", None)
    ):
        subject = (
            "Alteração de Agendamento de Turma: "
            f"{dados_novos.get('treinamento_nome')}"
        )
        html_body = render_template(
            "email/turma_alterada_secretaria.html.j2",
            dados_antigos=dados_antigos,
            dados_novos=dados_novos,
        )
        send_email(instrutor_atual.email, subject, html_body)
        time_module.sleep(RATE_LIMIT_DELAY)


class EmailService:
    """Serviço de envio de e-mails com suporte a anexos."""

    def _send_mail(
        self,
        subject: str,
        recipients: Iterable[str],
        template: str,
        context: Dict[str, Any],
        attachment_path: str | None = None,
    ) -> None:
        """Renderiza o template e envia o e-mail.

        Se ``attachment_path`` for fornecido e existir, o arquivo será anexado
        ao e-mail.
        """

        template_obj = current_app.jinja_env.get_or_select_template(template)
        html = template_obj.render(**context)

        attachments: List[Dict[str, Any]] = []
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            file_name = os.path.basename(attachment_path)
            attachments.append({"filename": file_name, "content": encoded})
            current_app.logger.info(f"Anexando '{file_name}' ao e-mail.")

        send_email(
            to=list(recipients),
            subject=subject,
            html=html,
            attachments=attachments,
        )

    def send_email(
        self,
        to: Address,
        subject: str,
        template: str,
        **context: Any,
    ) -> None:
        """Interface simples para envio de e-mails usando templates."""
        recipients = [to] if isinstance(to, str) else list(to)
        self._send_mail(
            subject=subject,
            recipients=recipients,
            template=template,
            context=context,
        )

    def send_convocacao_email(self, user: Any, turma: Any) -> None:
        """Envia e-mail de convocação com anexo quando necessário."""

        subject = (
            f"Convocação: {turma.treinamento.nome} — "
            f"{turma.data_inicio.strftime('%d/%m/%Y')}"
        )

        attachment: str | None = None
        if getattr(turma, "teoria_online", False):
            attachment = os.path.join(
                current_app.static_folder,
                "docs",
                "Tutorial de Acesso e Navegação - Aluno Anglo.pdf",
            )

        self._send_mail(
            subject=subject,
            recipients=[user.email],
            template="email/convocacao.html.j2",
            context={"user": user, "turma": turma},
            attachment_path=attachment,
        )
