// Gestão de usuários com paginação
/* global bootstrap, chamarAPI, showToast, verificarAutenticacao, verificarPermissaoAdmin, escapeHTML */

function obterConfiguracaoTipoUsuario(tipo) {
    switch (tipo) {
        case 'admin':
            return { classe: 'bg-danger', rotulo: 'Administrador' };
        case 'secretaria':
            return { classe: 'bg-secondary', rotulo: 'Secretaria' };
        default:
            return { classe: 'bg-primary', rotulo: 'Comum' };
    }
}

function criarLinhaUsuario(usuario = {}) {
    const idNumerico = Number.parseInt(usuario.id, 10);
    const possuiIdValido = !Number.isNaN(idNumerico);
    const valorId = possuiIdValido ? idNumerico : '';
    const idParaAcao = possuiIdValido ? idNumerico : 'null';
    const nomeEscapado = escapeHTML(usuario.nome ?? '');
    const emailEscapado = escapeHTML(usuario.email ?? '');
    const { classe, rotulo } = obterConfiguracaoTipoUsuario(usuario.tipo);

    return `
        <tr>
            <td>${valorId}</td>
            <td>${nomeEscapado}</td>
            <td>${emailEscapado}</td>
            <td>
                <span class="badge ${classe}">
                    ${rotulo}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editarUsuario(${idParaAcao})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao(${idParaAcao})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

if (typeof window !== 'undefined') {
    window.__usuariosAdmin = window.__usuariosAdmin || {};
    window.__usuariosAdmin.criarLinhaUsuario = criarLinhaUsuario;
}

document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    const usuarioModal = new bootstrap.Modal(document.getElementById('usuarioModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let usuarioIdParaExcluir = null;
    let paginaAtual = 1;
    const porPagina = 10;
    const paginacaoEl = document.getElementById('paginacaoUsuarios');
    const filtroNomeEl = document.getElementById('filtroNome');
    const filtroEmailEl = document.getElementById('filtroEmail');
    const filtroTipoEl = document.getElementById('filtroTipo');
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    const btnLimparFiltros = document.getElementById('btnLimparFiltros');
    const filtrosCollapseEl = document.getElementById('filtrosCollapse');
    const filtrosToggleIcon = document.getElementById('filtrosToggleIcon');

    let filtrosAtuais = {
        nome: '',
        email: '',
        tipo: '',
    };

    if (filtrosCollapseEl && filtrosToggleIcon) {
        filtrosCollapseEl.addEventListener('show.bs.collapse', () => {
            filtrosToggleIcon.classList.remove('bi-chevron-down');
            filtrosToggleIcon.classList.add('bi-chevron-up');
        });

        filtrosCollapseEl.addEventListener('hide.bs.collapse', () => {
            filtrosToggleIcon.classList.remove('bi-chevron-up');
            filtrosToggleIcon.classList.add('bi-chevron-down');
        });
    }

    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', () => {
            filtrosAtuais = {
                nome: filtroNomeEl ? filtroNomeEl.value.trim() : '',
                email: filtroEmailEl ? filtroEmailEl.value.trim() : '',
                tipo: filtroTipoEl ? filtroTipoEl.value : '',
            };
            paginaAtual = 1;
            carregarUsuarios();
        });
    }

    if (btnLimparFiltros) {
        btnLimparFiltros.addEventListener('click', () => {
            if (filtroNomeEl) filtroNomeEl.value = '';
            if (filtroEmailEl) filtroEmailEl.value = '';
            if (filtroTipoEl) filtroTipoEl.value = '';
            filtrosAtuais = {
                nome: '',
                email: '',
                tipo: '',
            };
            paginaAtual = 1;
            carregarUsuarios();
        });
    }

    carregarUsuarios();

    document.getElementById('btnSalvarUsuario').addEventListener('click', salvarUsuario);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', async function() {
        if (usuarioIdParaExcluir) {
            try {
                await chamarAPI(`/usuarios/${usuarioIdParaExcluir}`, 'DELETE');
                confirmacaoModal.hide();
                showToast('Usuário excluído com sucesso!', 'success');
                carregarUsuarios(paginaAtual);
            } catch (error) {
                showToast(`Não foi possível excluir usuário: ${error.message}`, 'danger');
            }
        }
    });

    async function carregarUsuarios(page = 1) {
        try {
            const params = criarParametrosConsulta({ page, perPage: porPagina });
            const resp = await chamarAPI(`/usuarios?${params.toString()}`);
            const usuarios = resp.items;

            atualizarTabela(usuarios);

            if (!usuarios || usuarios.length === 0) {
                paginacaoEl.innerHTML = '';
                return;
            }

            paginaAtual = typeof resp.page === 'number' ? resp.page : page;
            atualizarPaginacao(resp.pages ?? 1);
        } catch (error) {
            document.getElementById('usuariosTableBody').innerHTML = '<tr><td colspan="5" class="text-center text-danger">Não foi possível carregar usuários.</td></tr>';
            console.error('Não foi possível carregar usuários:', error);
        }
    }

    function atualizarTabela(usuarios) {
        const tableBody = document.getElementById('usuariosTableBody');
        if (!usuarios || usuarios.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum usuário encontrado.</td></tr>';
            return;
        }

        tableBody.innerHTML = usuarios.map(criarLinhaUsuario).join('');
    }

    function criarParametrosConsulta({ page, perPage }) {
        const params = new URLSearchParams({
            page,
            per_page: perPage,
        });

        if (filtrosAtuais.nome) {
            params.append('nome', filtrosAtuais.nome);
        }

        if (filtrosAtuais.email) {
            params.append('email', filtrosAtuais.email);
        }

        if (filtrosAtuais.tipo) {
            params.append('tipo', filtrosAtuais.tipo);
        }

        return params;
    }

    function atualizarPaginacao(totalPaginas) {
        paginacaoEl.innerHTML = '';
        const total = Math.max(Number.parseInt(totalPaginas, 10) || 1, 1);
        paginaAtual = Math.min(Math.max(paginaAtual, 1), total);
        const criarItem = (label, page, disabled = false, active = false) => {
            return `<li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${page}">${label}</a>
                    </li>`;
        };
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Anterior', paginaAtual - 1, paginaAtual <= 1));
        for (let i = 1; i <= total; i++) {
            paginacaoEl.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === paginaAtual));
        }
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Próxima', paginaAtual + 1, paginaAtual >= total));

        Array.from(paginacaoEl.querySelectorAll('a[data-page]')).forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const alvo = Number.parseInt(link.getAttribute('data-page'), 10);
                if (!Number.isNaN(alvo)) {
                    carregarUsuarios(alvo);
                }
            });
        });
    }

    async function salvarUsuario() {
        const usuarioId = document.getElementById('usuarioId').value;
        const nome = document.getElementById('nome').value;
        const email = document.getElementById('email').value;
        const senha = document.getElementById('senha').value;
        const tipo = document.getElementById('tipo').value;

        if (!nome || !email || (!usuarioId && !senha)) {
            showToast('Preencha todos os campos obrigatórios', 'warning');
            return;
        }

        try {
            const dadosUsuario = { nome, email, tipo };
            if (senha) {
                dadosUsuario.senha = senha;
            }

            if (usuarioId) {
                await chamarAPI(`/usuarios/${usuarioId}`, 'PUT', dadosUsuario);
                showToast('Usuário atualizado com sucesso!', 'success');
            } else {
                await chamarAPI('/usuarios', 'POST', dadosUsuario);
                showToast('Usuário criado com sucesso!', 'success');
            }

            usuarioModal.hide();
            carregarUsuarios(paginaAtual);

            document.getElementById('usuarioForm').reset();
            document.getElementById('usuarioId').value = '';
        } catch (error) {
            showToast(`Não foi possível salvar usuário: ${error.message}`, 'danger');
        }
    }

    window.editarUsuario = async function(id) {
        try {
            const usuario = await chamarAPI(`/usuarios/${id}`);
            document.getElementById('usuarioId').value = usuario.id;
            document.getElementById('nome').value = usuario.nome;
            document.getElementById('email').value = usuario.email;
            document.getElementById('senha').value = '';
            document.getElementById('tipo').value = usuario.tipo;
            document.getElementById('usuarioModalLabel').textContent = 'Editar Usuário';
            document.getElementById('senhaHelp').style.display = 'block';
            usuarioModal.show();
        } catch (error) {
            showToast(`Não foi possível carregar dados do usuário: ${error.message}`, 'danger');
        }
    };

    window.confirmarExclusao = function(id) {
        usuarioIdParaExcluir = id;
        confirmacaoModal.show();
    };

    document.getElementById('usuarioModal').addEventListener('hidden.bs.modal', function() {
        document.getElementById('usuarioForm').reset();
        document.getElementById('usuarioId').value = '';
        document.getElementById('usuarioModalLabel').textContent = 'Novo Usuário';
        document.getElementById('senhaHelp').style.display = 'none';
    });
});

