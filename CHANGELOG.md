# Changelog

## [Unreleased]
### Added
- Botão para administradores retornarem à tela de seleção de sistema no menu do usuário.
- Limitação de taxa simples para as rotas `/api/login` e `/api/usuarios`.
- Swagger UI em `/docs` com anotações de esquemas de requisição e resposta.
- Seção de segurança no README destacando uso de JWT, rate limiting e troca de credenciais padrão.
### Changed
- Sidebar do Gerenciamento de Usuários atualizada para exibir apenas "Lista de Usuários" e "Meu Perfil".
- Removido carregamento automático do link "Laboratórios e Turmas" nesse módulo.
- Formulário de nova sala simplificado com opções fixas de localização e menos campos.
### Fixed
- Edição de ocupações recorrentes agora ignora o próprio grupo ao verificar disponibilidade.
- Corrigido erro de banco de dados ao listar treinamentos garantindo a existência da coluna `teoria_online` em `turmas_treinamento`.
- Formulário público de suporte passa a criar os campos `nome_solicitante`/`local_unidade` e libera `user_id` como nulo quando as
  migrações ainda não foram executadas.
