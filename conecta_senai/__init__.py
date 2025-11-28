"""Fábrica principal da aplicação Flask Conecta SENAI."""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Tuple

from flasgger import Swagger
from flask import Flask, abort, render_template, send_from_directory
from flask_wtf.csrf import CSRFProtect
from jinja2 import TemplateNotFound
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except ImportError:  # pragma: no cover - sentry opcional em desenvolvimento
    sentry_sdk = None  # type: ignore[assignment]
    FlaskIntegration = None  # type: ignore[assignment]

from conecta_senai.auth import auth_bp, auth_reset_bp
from conecta_senai.cli import register_cli
from conecta_senai.config import DevConfig, ProdConfig, TestConfig
from conecta_senai.config.redis import init_redis
from conecta_senai.extensions import db, jwt, limiter, migrate
from conecta_senai.logging_conf import setup_logging
from conecta_senai.middlewares.request_id import request_id_bp
from conecta_senai.repositories.user_repository import UserRepository
from conecta_senai.routes.inscricoes_treinamento import bp as inscricoes_treinamento_bp
from conecta_senai.routes.laboratorios import agendamento_bp, laboratorio_bp
from conecta_senai.routes.noticias import api_noticias_bp
from conecta_senai.routes.notificacao import notificacao_bp
from conecta_senai.routes.ocupacao import instrutor_bp, ocupacao_bp, sala_bp
from conecta_senai.routes.rateio import rateio_bp
from conecta_senai.routes.suporte_ti import (
    suporte_ti_admin_bp,
    suporte_ti_paginas_publicas_bp,
    suporte_ti_public_bp,
    suporte_ti_visitante_bp,
)
from conecta_senai.routes.treinamentos import treinamento_bp, turma_bp
from conecta_senai.routes.treinamentos.basedados import (
    locais_realizacao_bp as treinamentos_locais_realizacao_bp,
    secretaria_bp as treinamentos_basedados_bp,
    horarios_bp as treinamentos_horarios_bp,
)
from conecta_senai.routes.user import user_bp
from conecta_senai.tasks import start_scheduler
from conecta_senai.telemetry import instrument
from conecta_senai.utils.paths import ensure_path_is_safe

EMAIL_RE = re.compile(r"[^@]+@[^@]+")
CSRF = CSRFProtect()
OBSERVABILITY_CONFIGURED = False
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"


def _setup_observability() -> None:
    """Inicializa logging e Sentry com filtros de dados sensíveis."""

    global OBSERVABILITY_CONFIGURED
    if OBSERVABILITY_CONFIGURED:
        return

    setup_logging()

    def before_send(event, hint):
        request = event.get("request", {})
        for section in ("headers", "data"):
            payload = request.get(section)
            if isinstance(payload, dict):
                cleaned = {}
                for key, value in payload.items():
                    if isinstance(value, str) and (
                        EMAIL_RE.fullmatch(value) or "token" in key.lower()
                    ):
                        cleaned[key] = "[Filtered]"
                    else:
                        cleaned[key] = value
                request[section] = cleaned
        return event

    if sentry_sdk and FlaskIntegration:
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("APP_ENV"),
            release=os.getenv("APP_RELEASE"),
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
            before_send=before_send,
        )
    OBSERVABILITY_CONFIGURED = True


def _configure_database(app: Flask) -> None:
    """Configura SQLAlchemy e a migração de banco."""

    migrations_dir = str(PROJECT_ROOT / "migrations")
    db.init_app(app)
    migrate.init_app(app, db, directory=migrations_dir)


def _configure_security(app: Flask) -> None:
    """Ajusta parâmetros relacionados a segurança e cookies."""

    secret_key = (os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "").strip()
    if not secret_key or secret_key.lower() == "changeme":
        raise RuntimeError(
            "SECRET_KEY environment variable must be set to a secure value for JWT signing"
        )
    app.config["SECRET_KEY"] = secret_key

    app.config.update(
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=not app.config.get("DEBUG", False),
        WTF_CSRF_TIME_LIMIT=3600,
    )

    cookie_secure_env = os.getenv("COOKIE_SECURE")
    if cookie_secure_env is None:
        cookie_secure = not app.config.get("DEBUG", False)
    else:
        cookie_secure = cookie_secure_env.lower() in ("true", "1", "t")

    cookie_samesite = os.getenv("COOKIE_SAMESITE", "Strict" if cookie_secure else "Lax")
    app.config["COOKIE_SECURE"] = cookie_secure
    app.config["COOKIE_SAMESITE"] = cookie_samesite

    app.config["WTF_CSRF_CHECK_DEFAULT"] = False
    CSRF.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)


def _configure_flask(app: Flask) -> None:
    """Registra blueprints, CLI e integrações diversas."""

    app.register_blueprint(request_id_bp)
    instrument(app)

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(agendamento_bp, url_prefix="/api")
    app.register_blueprint(notificacao_bp, url_prefix="/api")
    app.register_blueprint(laboratorio_bp, url_prefix="/api")
    app.register_blueprint(turma_bp, url_prefix="/api")
    app.register_blueprint(sala_bp, url_prefix="/api")
    app.register_blueprint(instrutor_bp, url_prefix="/api")
    app.register_blueprint(ocupacao_bp, url_prefix="/api")
    app.register_blueprint(rateio_bp, url_prefix="/api")
    app.register_blueprint(treinamento_bp, url_prefix="/api")
    app.register_blueprint(api_noticias_bp, url_prefix="/api")
    app.register_blueprint(treinamentos_horarios_bp, url_prefix="/api/horarios")
    app.register_blueprint(
        treinamentos_basedados_bp, url_prefix="/api/treinamentos/secretaria"
    )
    app.register_blueprint(
        treinamentos_locais_realizacao_bp,
        url_prefix="/api/treinamentos/locais-realizacao",
    )
    app.register_blueprint(suporte_ti_paginas_publicas_bp)
    app.register_blueprint(suporte_ti_visitante_bp)
    app.register_blueprint(suporte_ti_public_bp)
    app.register_blueprint(suporte_ti_admin_bp)
    app.register_blueprint(inscricoes_treinamento_bp)
    app.register_blueprint(auth_reset_bp)
    app.register_blueprint(auth_bp)

    register_cli(app)


def _configure_swagger(app: Flask) -> None:
    """Habilita a documentação Swagger/Flasgger."""

    swagger_template = {
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "nome": {"type": "string"},
                        "email": {"type": "string"},
                        "tipo": {"type": "string"},
                    },
                },
                "UserCreate": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "email": {"type": "string"},
                        "senha": {"type": "string"},
                        "tipo": {"type": "string"},
                    },
                    "required": ["nome", "email", "senha"],
                },
                "Notification": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "mensagem": {"type": "string"},
                        "lida": {"type": "boolean"},
                        "criada_em": {"type": "string", "format": "date-time"},
                    },
                },
            }
        }
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs",
    }

    app.config["SWAGGER"] = {
        "title": "Conecta SENAI API",
        "uiversion": 3,
    }
    Swagger(app, config=swagger_config, template=swagger_template)


def _configure_database_url(app: Flask) -> None:
    """Normaliza a URL do banco de dados a partir das variáveis de ambiente."""

    db_uri = os.getenv("DATABASE_URL", "sqlite:///agenda_laboratorio.db").strip()
    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _configure_recaptcha(app: Flask) -> None:
    """Carrega as chaves do reCAPTCHA a partir do ambiente."""

    recaptcha_site_key = (
        os.getenv("RECAPTCHA_SITE_KEY") or os.getenv("SITE_KEY") or ""
    ).strip()
    recaptcha_secret_key = (
        os.getenv("RECAPTCHA_SECRET_KEY") or os.getenv("CAPTCHA_SECRET_KEY") or ""
    ).strip()

    app.config["RECAPTCHA_SITE_KEY"] = recaptcha_site_key or None
    app.config["RECAPTCHA_SECRET_KEY"] = recaptcha_secret_key or None
    app.config["RECAPTCHA_THRESHOLD"] = float(os.getenv("RECAPTCHA_THRESHOLD", "0.5"))


def _register_default_routes(app: Flask) -> None:
    """Define rotas básicas de saúde e entrega de arquivos estáticos."""

    @app.route("/")
    def index():
        return render_template("admin/login.html")

    @app.route("/static/<path:filename>")
    def static_files(filename: str):
        return app.send_static_file(filename)

    @app.route("/<path:path>")
    def static_file(path: str):
        if path.endswith(".html"):
            template_path = Path(path)
            if not ensure_path_is_safe(template_path):
                abort(404)
            try:
                normalized_template = str(template_path).replace("\\", "/")
                return render_template(normalized_template)
            except TemplateNotFound:
                app.logger.warning("Template HTML não encontrado: %s", path)
                abort(404)
        return app.send_static_file(path)

    @app.route("/favicon.ico")
    @app.route("/admin/favicon.ico")
    def favicon():
        static_img_dir = Path(app.static_folder or STATIC_DIR) / "img"
        try:
            return send_from_directory(str(static_img_dir), "senai-logo.png", mimetype="image/png")
        except FileNotFoundError:
            return "", 204

    @app.route("/health")
    def health_check() -> Tuple[str, int]:
        return "OK", 200

    @app.route("/debug-sentry")
    def debug_sentry():
        1 / 0


def create_admin(app: Flask) -> None:
    """Cria o usuário administrador padrão de forma idempotente."""

    from conecta_senai.models.user import User
    from sqlalchemy.exc import SQLAlchemyError

    with app.app_context():
        try:
            admin_email = os.environ.get("ADMIN_EMAIL")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            admin_username = os.environ.get("ADMIN_USERNAME")
            if not admin_email or not admin_password:
                logging.error(
                    "ADMIN_EMAIL e ADMIN_PASSWORD precisam estar definidos para criar o usuário administrador"
                )
                return

            if admin_email in {"admin@example.com", "<definir_em_producao>"} or admin_password in {
                "senha-segura",
                "<definir_em_producao>",
            }:
                logging.error(
                    "ADMIN_EMAIL e ADMIN_PASSWORD não podem usar os valores padrão"
                )
                return

            admin_username = admin_username or admin_email.split("@")[0]

            admin = UserRepository.get_by_email(admin_email)
            if not admin:
                admin = User(
                    nome="Administrador",
                    email=admin_email,
                    senha=admin_password,
                    tipo="admin",
                    username=admin_username,
                )
                UserRepository.add(admin)
                logging.info("Usuário administrador criado com sucesso!")
            else:
                logging.info("Usuário administrador já existe.")
        except SQLAlchemyError as exc:
            UserRepository.rollback()
            logging.error("Erro ao criar usuário administrador: %s", exc)


def create_default_recursos(app: Flask) -> None:
    """Garante que recursos padrão existam no banco de dados."""

    from conecta_senai.models.recurso import Recurso

    with app.app_context():
        padrao = [
            "tv",
            "projetor",
            "quadro_branco",
            "climatizacao",
            "computadores",
            "wifi",
            "bancadas",
            "armarios",
            "tomadas",
        ]
        for nome in padrao:
            if not Recurso.query.filter_by(nome=nome).first():
                db.session.add(Recurso(nome=nome))
        db.session.commit()


def create_app() -> Flask:
    """Fábrica de aplicação usada pelo Flask."""

    _setup_observability()

    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder=str(STATIC_DIR),
        template_folder=str(TEMPLATES_DIR),
    )

    env = os.getenv("FLASK_ENV", "development").lower()
    config_map = {
        "production": ProdConfig,
        "testing": TestConfig,
    }
    config_class = config_map.get(env, DevConfig)
    app.config.from_object(config_class)
    logging.getLogger().setLevel(app.config.get("LOG_LEVEL", logging.INFO))

    _configure_database_url(app)
    _configure_database(app)

    init_redis(app)

    _configure_security(app)
    _configure_flask(app)
    _configure_swagger(app)
    _configure_recaptcha(app)
    _register_default_routes(app)

    scheduler_env = os.getenv("SCHEDULER_ENABLED")
    scheduler_enabled = False
    if not app.config.get("TESTING", False):
        if scheduler_env is None:
            scheduler_enabled = True
        else:
            scheduler_enabled = scheduler_env.strip().lower() in {
                "1",
                "true",
                "t",
                "on",
                "yes",
            }

    app.config["SCHEDULER_ENABLED"] = scheduler_enabled

    if scheduler_enabled:
        start_scheduler(app)
    else:
        motivo = (
            "modo de teste"
            if app.config.get("TESTING", False)
            else f"SCHEDULER_ENABLED={scheduler_env or '0'}"
        )
        app.logger.info(
            "Scheduler de tarefas desativado (%s). Defina SCHEDULER_ENABLED=1 para habilitar.",
            motivo,
        )

    return app


__all__ = ["create_app", "create_admin", "create_default_recursos"]
