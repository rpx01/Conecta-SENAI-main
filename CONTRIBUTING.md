# Guia de Contribuição

Obrigado por colaborar com o Conecta SENAI! Este documento descreve como preparar o ambiente de desenvolvimento, padrões de código e o fluxo sugerido para Pull Requests.

## Pré-requisitos
- Python 3.11+
- Redis disponível localmente (ou em contêiner) para suportar cache e rate limiting
- Banco relacional (PostgreSQL recomendado; SQLite funciona para testes)
- Conta no Sentry ou serviço equivalente caso deseje validar a telemetria

## Preparação do ambiente
1. Crie um virtualenv e instale as dependências Python via `pip install -r requirements.txt`.
2. Exporte as variáveis de ambiente obrigatórias (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`). Veja [README.md](README.md) para a lista completa.
3. Aplique as migrações do banco: `flask --app conecta_senai.main db upgrade`.
4. Execute a aplicação: `flask --app conecta_senai.main run`.

## Padrões de código
- **Estilo:** siga PEP8. O projeto utiliza `black` e `isort` como referência. Indente com 4 espaços.
- **Docstrings:** toda função, classe e módulo deve conter docstring em português descrevendo propósito, parâmetros e retorno quando aplicável.
- **Nomenclatura:** use `snake_case` para funções e variáveis; `PascalCase` para classes.
- **Imports:** prefira imports absolutos (`from conecta_senai...`). Agrupe-os por módulos padrão, terceiros e internos.
- **Banco de dados:** utilize os modelos definidos em `conecta_senai/models` e as operações utilitárias existentes em `repositories/` ou `services/` antes de criar novas consultas ad-hoc.

## Testes
- Execute `pytest` antes de enviar seu PR.
- Ao adicionar novos recursos, escreva testes cobrindo fluxos felizes e de falha.
- Utilize fixtures já existentes em `tests/conftest.py` e respeite a camada de serviços para isolar regras de negócio.

## Fluxo de contribuição
1. Crie um branch a partir de `main` com nome descritivo (`feature/...`, `bugfix/...`).
2. Faça commits pequenos e coesos. Inclua mensagens claras (imperativo no presente: "Adiciona rota X").
3. Abra o Pull Request preenchendo os detalhes: motivação, mudanças realizadas e como validar.
4. Aguarde revisão. Responda aos comentários e realize ajustes adicionais no mesmo branch.
5. Após aprovação, aguarde a automação de CI concluir com sucesso antes do merge.

## Boas práticas adicionais
- Evite duplicação de código: verifique se já existe serviço, schema ou utilitário com funcionalidade similar.
- Mantenha as traduções e mensagens de log em português para consistência.
- Para tarefas agendadas, centralize a lógica em `conecta_senai/tasks` e registre novos jobs no scheduler.

Obrigado por contribuir! Em caso de dúvidas, abra uma issue descrevendo o contexto para que possamos orientar a melhor abordagem.
