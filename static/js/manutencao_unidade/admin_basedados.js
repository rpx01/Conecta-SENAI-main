/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, showToast, sanitizeHTML */

(function () {
    const tabelaAreas = document.querySelector('#tabelaAreas tbody');
    const tabelaTipos = document.querySelector('#tabelaTipos tbody');
    const totalAreas = document.getElementById('totalAreas');
    const totalTipos = document.getElementById('totalTipos');
    const formArea = document.getElementById('formArea');
    const formTipo = document.getElementById('formTipo');
    const inputNovaArea = document.getElementById('novaArea');
    const inputNovoTipo = document.getElementById('novoTipo');
    const modalEl = document.getElementById('modalEditarRegistro');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    const inputNomeRegistro = document.getElementById('nomeRegistro');
    const inputRegistroId = document.getElementById('registroId');
    const inputRegistroTipo = document.getElementById('registroTipo');
    const btnSalvarEdicao = document.getElementById('btnSalvarEdicao');

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await Promise.all([carregarAreas(), carregarTipos()]);
    }

    function atualizarNomeUsuario() {
        const usuario = getUsuarioLogado();
        if (usuario) {
            const span = document.getElementById('userName');
            if (span) {
                span.textContent = usuario.nome;
            }
        }
    }

    async function carregarAreas() {
        try {
            const areas = await chamarAPI('/suporte_ti/admin/areas');
            renderizarTabela(tabelaAreas, areas, 'area');
            atualizarTotal(totalAreas, areas?.length || 0);
        } catch (error) {
            console.error(error);
        }
    }

    async function carregarTipos() {
        try {
            const tipos = await chamarAPI('/suporte_ti/admin/tipos_equipamento');
            renderizarTabela(tabelaTipos, tipos, 'tipo');
            atualizarTotal(totalTipos, tipos?.length || 0);
        } catch (error) {
            console.error(error);
        }
    }

    function atualizarTotal(elemento, total) {
        if (!elemento) return;
        elemento.textContent = `${total} item${total === 1 ? '' : 's'}`;
    }

    function renderizarTabela(tabela, itens, tipo) {
        if (!tabela) return;
        tabela.innerHTML = '';
        if (!Array.isArray(itens) || itens.length === 0) {
            const linha = document.createElement('tr');
            linha.innerHTML = `<td colspan="2" class="text-center text-muted py-3">Nenhum ${tipo === 'area' ? 'área' : 'tipo'} cadastrado.</td>`;
            tabela.appendChild(linha);
            return;
        }
        itens.forEach((item) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sanitizeHTML(item.nome)}</td>
                <td class="text-end">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" data-id="${item.id}" data-tipo="${tipo}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${item.id}" data-tipo="${tipo}"><i class="bi bi-trash"></i></button>
                    </div>
                </td>
            `;
            const [btnEditar, btnExcluir] = tr.querySelectorAll('button');
            if (btnEditar) {
                btnEditar.addEventListener('click', () => abrirModalEdicao(item.id, item.nome, tipo));
            }
            if (btnExcluir) {
                btnExcluir.addEventListener('click', () => excluirRegistro(item.id, tipo));
            }
            tabela.appendChild(tr);
        });
    }

    function limparFormulario(input) {
        if (input) {
            input.value = '';
            input.focus();
        }
    }

    async function criarRegistro(tipo) {
        const input = tipo === 'area' ? inputNovaArea : inputNovoTipo;
        const valor = (input?.value || '').trim();
        if (!valor) {
            showToast('Informe um nome antes de adicionar.', 'warning');
            return;
        }
        const endpoint = tipo === 'area' ? '/suporte_ti/admin/areas' : '/suporte_ti/admin/tipos_equipamento';
        try {
            await chamarAPI(endpoint, 'POST', { nome: valor });
            showToast('Registro criado com sucesso!', 'success');
            limparFormulario(input);
            await (tipo === 'area' ? carregarAreas() : carregarTipos());
        } catch (error) {
            console.error(error);
            const mensagem = error?.payload?.erro || error.message || 'Erro ao criar registro.';
            showToast(Array.isArray(mensagem) ? mensagem.join(' ') : mensagem, 'danger');
        }
    }

    function abrirModalEdicao(id, nome, tipo) {
        if (!modal) return;
        inputRegistroId.value = id;
        inputNomeRegistro.value = nome;
        inputRegistroTipo.value = tipo;
        modal.show();
    }

    async function salvarEdicao() {
        const id = inputRegistroId.value;
        const tipo = inputRegistroTipo.value;
        const nome = inputNomeRegistro.value.trim();
        if (!nome) {
            showToast('Informe um nome válido.', 'warning');
            return;
        }
        const endpoint = tipo === 'area' ? `/suporte_ti/admin/areas/${id}` : `/suporte_ti/admin/tipos_equipamento/${id}`;
        try {
            await chamarAPI(endpoint, 'PUT', { nome });
            showToast('Registro atualizado com sucesso!', 'success');
            modal?.hide();
            await (tipo === 'area' ? carregarAreas() : carregarTipos());
        } catch (error) {
            console.error(error);
            const mensagem = error?.payload?.erro || error.message || 'Erro ao atualizar registro.';
            showToast(Array.isArray(mensagem) ? mensagem.join(' ') : mensagem, 'danger');
        }
    }

    async function excluirRegistro(id, tipo) {
        if (!window.confirm('Deseja realmente excluir este registro?')) {
            return;
        }
        const endpoint = tipo === 'area' ? `/suporte_ti/admin/areas/${id}` : `/suporte_ti/admin/tipos_equipamento/${id}`;
        try {
            await chamarAPI(endpoint, 'DELETE');
            showToast('Registro excluído com sucesso!', 'success');
            await (tipo === 'area' ? carregarAreas() : carregarTipos());
        } catch (error) {
            console.error(error);
            const mensagem = error?.payload?.erro || error.message || 'Erro ao excluir registro.';
            showToast(Array.isArray(mensagem) ? mensagem.join(' ') : mensagem, 'danger');
        }
    }

    if (formArea) {
        formArea.addEventListener('submit', (event) => {
            event.preventDefault();
            criarRegistro('area');
        });
    }

    if (formTipo) {
        formTipo.addEventListener('submit', (event) => {
            event.preventDefault();
            criarRegistro('tipo');
        });
    }

    if (btnSalvarEdicao) {
        btnSalvarEdicao.addEventListener('click', salvarEdicao);
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
