"""Rotas de recuperação e redefinição de senha."""
import logging
import re
import time
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app,
    jsonify,
)
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import generate_csrf, validate_csrf, CSRFError

from conecta_senai.repositories.user_repository import UserRepository
from conecta_senai.utils.tokens import generate_reset_token, confirm_reset_token
from conecta_senai.services.email_service import send_email, render_email_template

auth_reset_bp = Blueprint('auth_reset', __name__)

PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,}$')


def _validate_password(password: str) -> bool:
    """Valida a senha segundo o padrão definido para o reset."""

    return bool(PASSWORD_RE.match(password))


@auth_reset_bp.get('/forgot')
def forgot_get():
    """Renderiza o formulário de recuperação de senha com um token CSRF."""

    csrf_token = generate_csrf()
    return render_template('admin/forgot_password.html', csrf_token=csrf_token)


@auth_reset_bp.post('/forgot')
def forgot_post():
    """Processa a solicitação de redefinição, enviando o e-mail com instruções."""

    time.sleep(1)
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        return jsonify({"ok": False, "message": "Token CSRF inválido."}), 400

    email = request.form.get('email', '').strip().lower()
    if email:
        try:
            validate_email(email)
            user = UserRepository.get_by_email(email)
        except EmailNotValidError:
            user = None
        if user:
            token = generate_reset_token(email)
            base = current_app.config.get('APP_BASE_URL')
            reset_url = f"{base}/reset?token={token}"
            try:
                html = render_email_template(
                    "reset_password.html.j2", reset_url=reset_url
                )
                text = render_email_template(
                    "reset_password.txt.j2", reset_url=reset_url
                )
                send_email(
                    to=user.email,
                    subject="Instruções para redefinir sua senha",
                    html=html,
                    text=text,
                    tags=[{"name": "category", "value": "password_reset"}],
                )
            except Exception:
                current_app.logger.exception("Falha ao enviar e-mail de reset")
                return jsonify({
                    "ok": False,
                    "message": (
                        "Estamos com instabilidade no envio de e-mails. "
                        "Tente novamente em alguns minutos."
                    ),
                }), 503
    return jsonify({
        "ok": True,
        "message": "Se o e-mail existir, enviaremos as instruções.",
    })


@auth_reset_bp.get('/reset')
def reset_get():
    """Exibe o formulário para definição de uma nova senha."""

    token = request.args.get('token', '')
    email = confirm_reset_token(token)
    if not email:
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))
    csrf_token = generate_csrf()
    return render_template(
        'admin/reset_password.html', token=token, csrf_token=csrf_token
    )


@auth_reset_bp.post('/reset')
def reset_post():
    """Valida o formulário de redefinição e atualiza a senha do usuário."""

    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        flash('Token CSRF inválido.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))

    token = request.form.get('token', '')
    email = confirm_reset_token(token)
    if not email:
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))

    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if password != confirm or not _validate_password(password):
        flash('Senha inválida. Verifique os requisitos.', 'error')
        return redirect(url_for('auth_reset.reset_get', token=token))

    user = UserRepository.get_by_email(email)
    if not user:
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))

    user.senha_hash = generate_password_hash(
        password, method='pbkdf2:sha256', salt_length=16
    )
    UserRepository.commit()
    logging.info(
        'Senha redefinida para usuário %s a partir do IP %s',
        user.id,
        request.remote_addr,
    )
    flash('Senha redefinida com sucesso. Faça login novamente.', 'success')
    return redirect('/admin/login.html')
