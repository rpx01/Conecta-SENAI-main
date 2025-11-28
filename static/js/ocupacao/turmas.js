// Gerenciamento de turmas utilizando função genérica de tabela

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    let listaTurmas = [];

    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    const turmaModal = new bootstrap.Modal(document.getElementById('turmaModal'));
    let turmaParaExcluir = null;

    document.getElementById('turmaModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('turmaForm').reset();
        document.getElementById('turmaId').value = '';
        document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Salvar turma';
    });

    function renderizarLinhaTurma(turma) {
        return `
            <tr>
                <td>${turma.id}</td>
                <td>${escapeHTML(turma.nome)}</td>
                <td>${formatarData(turma.data_criacao)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarTurma(${turma.id}, '${escapeHTML(turma.nome)}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao(${turma.id}, '${escapeHTML(turma.nome)}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    async function carregarTurmas() {
        listaTurmas = await preencherTabela('turmasTable', '/turmas', renderizarLinhaTurma);
        aplicarFiltros();
    }

    function atualizarTabela(lista) {
        const tbody = document.getElementById('turmasTableBody');
        tbody.innerHTML = '';
        if (!lista || lista.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">Nenhuma turma encontrada.</td></tr>`;
            return;
        }
        lista.forEach(t => {
            tbody.insertAdjacentHTML('beforeend', renderizarLinhaTurma(t));
        });
    }

    function aplicarFiltros() {
        const termo = (document.getElementById('filtroBusca').value || '').toLowerCase();
        const filtradas = listaTurmas.filter(t => t.nome.toLowerCase().includes(termo));
        atualizarTabela(filtradas);
    }

    function limparFiltros() {
        document.getElementById('filtroBusca').value = '';
        atualizarTabela(listaTurmas);
    }

    document.getElementById('turmaForm').addEventListener('submit', function(e) {
        e.preventDefault();
        salvarTurma();
    });

    const btnFiltrar = document.getElementById('btnAplicarFiltros');
    const btnLimpar = document.getElementById('btnLimparFiltros');
    const inputBusca = document.getElementById('filtroBusca');
    if (btnFiltrar) btnFiltrar.addEventListener('click', aplicarFiltros);
    if (btnLimpar) btnLimpar.addEventListener('click', limparFiltros);
    if (inputBusca) {
        inputBusca.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') aplicarFiltros();
        });
    }

    document.getElementById('btnConfirmarExclusao').addEventListener('click', function() {
        if (turmaParaExcluir !== null) {
            excluirTurma(turmaParaExcluir);
        }
        confirmacaoModal.hide();
    });

    async function salvarTurma() {
        const btn = document.getElementById('btnSalvarTurma');
        const spinner = btn ? btn.querySelector('.spinner-border') : null;
        if (btn && spinner) {
            btn.disabled = true;
            spinner.classList.remove('d-none');
        }
        const id = document.getElementById('turmaId').value;
        const nome = document.getElementById('nomeTurma').value;

        if (!nome) {
            showToast('Por favor, informe o nome da turma.', 'warning');
            return;
        }

        try {
            if (id) {
                await chamarAPI(`/turmas/${id}`, 'PUT', { nome });
                showToast('Turma atualizada com sucesso!', 'success');
            } else {
                await chamarAPI('/turmas', 'POST', { nome });
                showToast('Turma cadastrada com sucesso!', 'success');
            }

            document.getElementById('turmaForm').reset();
            document.getElementById('turmaId').value = '';
            document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Salvar turma';
            turmaModal.hide();
            carregarTurmas();
        } catch (error) {
            showToast(`Não foi possível salvar a turma: ${error.message}`, 'danger');
        } finally {
            if (btn && spinner) {
                btn.disabled = false;
                spinner.classList.add('d-none');
            }
        }
    }

    window.editarTurma = function(id, nome) {
        document.getElementById('turmaId').value = id;
        document.getElementById('nomeTurma').value = nome;
        document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-check-circle me-2"></i>Atualizar turma';
        turmaModal.show();
        document.getElementById('nomeTurma').focus();
    };

    window.novaTurma = function() {
        document.getElementById('turmaForm').reset();
        document.getElementById('turmaId').value = '';
        document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Salvar turma';
        turmaModal.show();
    };

    window.confirmarExclusao = function(id, nome) {
        turmaParaExcluir = id;
        document.getElementById('confirmacaoModalBody').innerHTML = `
            <p>Tem certeza que deseja excluir a turma "${escapeHTML(nome)}"?</p>
            <p class="text-danger">Esta ação não pode ser desfeita.</p>
        `;
        confirmacaoModal.show();
    };

    async function excluirTurma(id) {
        try {
            await chamarAPI(`/turmas/${id}`, 'DELETE');
            showToast('Turma excluída com sucesso!', 'success');
            carregarTurmas();
        } catch (error) {
            showToast(`Não foi possível excluir a turma: ${error.message}`, 'danger');
        }
    }

    carregarTurmas();
});
