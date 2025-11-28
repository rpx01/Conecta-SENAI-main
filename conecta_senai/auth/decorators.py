"""Decoradores e utilidades de autenticação baseadas em JWT."""
from functools import wraps

"""Funcoes de autenticacao e autorizacao."""
from functools import wraps
from flask import request, jsonify, current_app, g
import jwt

from conecta_senai.config.redis import redis_conn

from conecta_senai.models import db
from conecta_senai.models.user import User


def verificar_autenticacao(req):
    """Verifica o token JWT no cabeçalho Authorization ou cookie."""
    auth_header = req.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = req.cookies.get('access_token')
    if not token:
        g.token_message = None
        return False, None
    try:
        dados = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256'],
        )
        jti = dados.get('jti')
        if jti and redis_conn.get(jti):
            g.token_message = "Token has been revoked"  # nosec B105
            return False, None
        user = db.session.get(User, dados.get('user_id'))
        if user:
            g.token_message = None
            return True, user
        g.token_message = None
        return False, None
    except jwt.ExpiredSignatureError:
        g.token_message = None
        return False, None
    except jwt.InvalidTokenError:
        g.token_message = None
        return False, None


def verificar_admin(user: User) -> bool:
    """Verifica se o usuário fornecido tem privilégios de administrador."""
    return user is not None and user.tipo in ['admin', 'secretaria']


def login_required(func):
    """Decorator que exige autenticação via JWT."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        autenticado, user = verificar_autenticacao(request)
        if not autenticado:
            msg = getattr(g, 'token_message', None)
            if msg:
                return jsonify({'erro': msg}), 401
            return jsonify({'erro': 'Não autenticado'}), 401
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """Decorator que exige usuário administrador."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        user = g.current_user
        if not verificar_admin(user):
            return jsonify({'erro': 'Permissão negada'}), 403
        return func(*args, **kwargs)

    return wrapper
