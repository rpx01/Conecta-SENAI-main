# Arquitetura do Conecta SENAI

Este documento apresenta uma visão de alto nível da aplicação Conecta SENAI e das responsabilidades de cada camada.

## Visão geral
A aplicação segue a arquitetura tradicional de projetos Flask estruturados em pacotes. A função `create_app` localizada em `conecta_senai/__init__.py` é responsável por:

1. Configurar observabilidade (logging estruturado, integração com Sentry e OpenTelemetry).
2. Carregar a configuração de ambiente (classe Dev/Prod/Test).
3. Inicializar extensões compartilhadas (`SQLAlchemy`, `Flask-Migrate`, `JWTManager`, `Limiter`, `CSRFProtect`).
4. Conectar-se ao Redis e preparar parâmetros de segurança.
5. Registrar blueprints e comandos CLI.
6. Configurar documentação Swagger e rotas públicas (`/health`, entrega de arquivos estáticos).
7. Iniciar o scheduler do APScheduler quando habilitado.

## Camadas principais

### Configuração (`conecta_senai/config`)
- `base.py` define a classe `BaseConfig` e utilitários como `env_bool`.
- `dev.py`, `prod.py` e `test.py` herdam de `BaseConfig` e customizam parâmetros.
- `redis.py` encapsula a inicialização do cliente Redis, expondo `init_redis` e `redis_conn` para uso em autenticação e invalidação de tokens.

### Extensões (`conecta_senai/extensions.py`)
Reúne instâncias globais de extensões Flask (SQLAlchemy, Migrate, JWT e Limiter) para evitar ciclos de importação. Outros módulos utilizam essas instâncias para declarar modelos ou aplicar rate limiting.

### Modelos (`conecta_senai/models`)
Modelos ORM do SQLAlchemy que representam entidades como usuários, recursos de laboratório, treinamentos e notícias. Os relacionamentos entre entidades estão centralizados nessa camada. Cada arquivo contém docstrings explicando atributos e comportamentos específicos.

### Repositórios e Serviços
- `repositories/` expõe classes e funções responsáveis por consultas e mutações específicas (ex.: `UserRepository`).
- `services/` implementa regras de negócio (envio de e-mails, criação de agendamentos, cálculos de rateio etc.). Eles utilizam os modelos e repositórios para manter o domínio organizado.

### Schemas (`conecta_senai/schemas`)
Agrupa validações de entrada/saída usando Marshmallow ou Pydantic. As rotas importam esses schemas para garantir que a API responda com estruturas consistentes.

### Rotas (`conecta_senai/routes`)
Cada subpacote corresponde a um domínio funcional:
- `routes/laboratorios` – gestão de laboratórios, agendamentos e logs.
- `routes/treinamentos` – gerenciamento de treinamentos, turmas e integração com e-mail.
- `routes/ocupacao` – visibilidade da ocupação de salas e instrutores.
- `routes/suporte_ti` – abertura e acompanhamento de chamados.
- `routes/notificacao` e `routes/noticias` – comunicação institucional.
- `routes/user` – autenticação baseada em JWT, cadastro e administração de usuários.

As rotas dependem dos serviços para executar regras de negócio e utilizam utilitários de auditoria para registrar ações sensíveis.

### Autenticação (`conecta_senai/auth`)
- `decorators.py` contém verificações de login e privilégios de administrador.
- `routes.py` e `reset_routes.py` implementam as telas HTML de login/registro e o fluxo de recuperação de senha.

### Tarefas (`conecta_senai/tasks`)
O módulo `scheduler.py` instancia e registra jobs no APScheduler. Os jobs propriamente ditos estão em `tasks/jobs/`, separados por domínio (notícias, notificações, convocação). Cada job chama funções de serviço, mantendo regras de negócio isoladas.

### Utilitários (`conecta_senai/utils`)
Inclui funções de auditoria (`log_action`), tratamento de erros (`handle_internal_error`), geração/validação de tokens de recuperação e helpers de caminhos (`ensure_path_is_safe`).

## Fluxo de dados
1. **Requisição HTTP** chega ao Flask e passa pelo middleware `request_id` para anexar um identificador de correlação.
2. **Blueprint** correspondente trata a requisição, validando entrada via schemas.
3. **Serviços** executam regras de negócio e invocam repositórios para persistência.
4. **Modelos** interagem com o banco via SQLAlchemy.
5. **Respostas** podem acionar **tarefas agendadas** (por exemplo, envio de e-mail) ou criar registros de auditoria.
6. Logs estruturados e métricas são enviados ao provedor configurado (Sentry/OTEL).

## Dependências externas
- **Banco relacional**: PostgreSQL (produção) ou SQLite (desenvolvimento/testes).
- **Redis**: cache, rate limiting e blacklist de tokens JWT.
- **Resend**: envio de e-mails transacionais.
- **Sentry**: monitoramento de erros.
- **reCAPTCHA**: proteção contra automações em formulários públicos.

## Como estender
- Novos domínios devem criar blueprints em `conecta_senai/routes/<dominio>` acompanhados de schemas, serviços e repositórios.
- Para novas tarefas recorrentes, adicione funções em `tasks/jobs/` e registre-as em `tasks/scheduler.py`.
- Quando precisar de novos modelos, declare-os em `conecta_senai/models` e crie migrações com Alembic.

Essa organização visa facilitar a manutenção e promover separação clara de responsabilidades, permitindo que novas equipes entendam rapidamente o fluxo da aplicação.
