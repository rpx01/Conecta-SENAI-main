# Conecta SENAI

Conecta SENAI é um sistema de agenda e gestão acadêmica desenvolvido em Flask + SQLAlchemy. A aplicação integra o controle de laboratórios, salas e treinamentos, gerenciamento de notícias internas e o suporte de TI, oferecendo um painel unificado para equipes administrativas e docentes.

## Arquitetura e organização do repositório
A base de código Python encontra-se no pacote `conecta_senai/`. Os principais diretórios são:

```
conecta_senai/
├── __init__.py           # create_app e rotinas de bootstrap
├── auth/                 # Autenticação, autorização e blueprints relacionadas
├── cli/                  # Comandos CLI registrados na aplicação
├── config/               # Configurações e integrações (Redis, classes Dev/Prod/Test)
├── extensions.py         # Instâncias globais de extensões Flask
├── models/               # Modelos ORM do SQLAlchemy
├── repositories/         # Camada de acesso a dados
├── routes/               # Blueprints agrupadas por domínio (ocupação, treinamentos, etc.)
├── schemas/              # Schemas Marshmallow/Pydantic
├── services/             # Regras de negócio e integrações externas
├── tasks/                # Scheduler do APScheduler e jobs recorrentes
└── utils/                # Funções auxiliares (tokens, auditoria, paths)
```

Os recursos de interface estão na raiz do repositório:

- `templates/` – templates Jinja2 usados pelo painel administrativo.
- `static/` – CSS, JavaScript e ativos estáticos.
- `migrations/` – scripts Alembic para evolução do esquema de banco.
- `docs/` – documentação adicional (design system, arquitetura e guias).
- `tests/` – suíte de testes automatizados com Pytest.

## Requisitos
- Python 3.11+
- Redis (para cache, rate limit e blacklist de tokens)
- Banco PostgreSQL ou SQLite (para desenvolvimento)
- Node.js (opcional, apenas para build dos ativos front-end quando necessário)

## Configuração de ambiente
1. **Clonar o projeto e criar um virtualenv**
   ```bash
   git clone https://github.com/<OWNER>/<REPO>.git
   cd Conecta-SENAI
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

2. **Instalar dependências**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configurar variáveis de ambiente**
   Crie um arquivo `.env` (ou exporte diretamente no shell) contendo os parâmetros abaixo:

   | Variável | Descrição |
   | --- | --- |
   | `SECRET_KEY` | Chave secreta utilizada na assinatura de JWTs e CSRF. Obrigatória. |
   | `DATABASE_URL` | URL de conexão com o banco. Ex.: `postgresql://user:pass@host/db`. |
   | `REDIS_URL` | URI do Redis para cache e rate limiting. Ex.: `redis://localhost:6379/0`. |
   | `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_USERNAME` | Credenciais usadas pelo script de criação do usuário administrador. |
   | `SENTRY_DSN`, `APP_ENV`, `APP_RELEASE` | Configuração de observabilidade e monitoramento. |
   | `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_THRESHOLD` | Proteções reCAPTCHA utilizadas nas rotas públicas. |
   | `RESEND_API_KEY`, `RESEND_FROM`, `RESEND_REPLY_TO` | Parametrização do envio de e-mails via Resend. |
   | `FRONTEND_BASE_URL`, `APP_BASE_URL` | URLs base para geração de links em notificações. |
   | `COOKIE_SECURE`, `COOKIE_SAMESITE` | Ajustes finos para cookies (opcionais). |
   | `SCHEDULER_ENABLED` | Define se o APScheduler deve iniciar (`1`/`true`). |

   Outros parâmetros opcionais encontram-se documentados em `conecta_senai/config/base.py`.

4. **Aplicar migrações e executar o servidor**
   ```bash
   flask --app conecta_senai.main db upgrade
   flask --app conecta_senai.main run
   ```

   A aplicação ficará disponível em `http://127.0.0.1:5000`.

## Executando tarefas recorrentes
O scheduler baseado em APScheduler é ativado automaticamente quando `SCHEDULER_ENABLED=1`. Para ambientes de desenvolvimento onde o scheduler não deve rodar, basta omitir a variável ou defini-la como `0`.

## Testes e qualidade
Execute a suíte de testes via Pytest:
```bash
pytest
```

Outras ferramentas, como lint e mypy, podem ser adicionadas conforme as políticas do time. Antes de abrir um Pull Request, assegure-se de executar os testes e revisar os logs.

## Observabilidade
- Logs estruturados em JSON são definidos em `conecta_senai/logging_conf.py`.
- A telemetria OTEL é habilitada pela função `instrument` em `conecta_senai/telemetry.py`.
- O endpoint `/health` expõe um teste de vida simples.
- Use `/debug-sentry` para validar a integração com o Sentry (gera uma exceção forçada).

## Documentação complementar
- [docs/architecture.md](docs/architecture.md) – visão geral da arquitetura e fluxo de dados.
- [CONTRIBUTING.md](CONTRIBUTING.md) – convenções de contribuição, código e revisão.
- [docs/design-system.md](docs/design-system.md) – diretrizes visuais utilizadas pelos templates.

Para histórico de alterações consulte o [CHANGELOG.md](CHANGELOG.md).
