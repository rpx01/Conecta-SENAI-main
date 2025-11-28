// Funções para administração de treinamentos e turmas

// Armazena a lista de treinamentos e instrutores para não ter que recarregar
let catalogoDeTreinamentos = [];
let listaDeInstrutores = [];
let listaDeLocaisRealizacao = [];
let turmaParaExcluirId = null;
let turmaParaConvocarId = null;
let confirmacaoModal;

// Função para limpar e abrir o modal de Treinamento (Catálogo)
function novoTreinamento() {
    document.getElementById('treinamentoForm').reset();
    document.getElementById('treinamentoId').value = '';
    document.getElementById('tipoTrein').value = 'Inicial';
    new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
}

// Carrega o catálogo de treinamentos na tabela
async function carregarCatalogo() {
    try {
        const lista = await chamarAPI('/treinamentos/catalogo');
        catalogoDeTreinamentos = lista; // Armazena para uso no modal de turmas
        const tbody = document.getElementById('catalogoTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum treinamento cadastrado.</td></tr>';
            return;
        }
        for (const t of lista) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.id}</td>
                <td>${escapeHTML(t.nome)}</td>
                <td>${escapeHTML(t.codigo)}</td>
                <td>${escapeHTML(t.tipo || '')}</td>
                <td>${t.carga_horaria || ''}</td>
                <td>${t.capacidade_maxima || ''}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarTreinamento(${t.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="excluirTreinamento(${t.id})"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}


// Salva um treinamento (novo ou existente)
async function salvarTreinamento() {
    const id = document.getElementById('treinamentoId').value;
    const body = {
        nome: document.getElementById('nomeTrein').value,
        codigo: document.getElementById('codigoTrein').value,
        tipo: document.getElementById('tipoTrein').value,
        conteudo_programatico: document.getElementById('conteudoTrein').value,
        carga_horaria: parseInt(document.getElementById('cargaTrein').value) || null,
        capacidade_maxima: parseInt(document.getElementById('capacidadeTrein').value) || null,
        tem_pratica: document.getElementById('temPratica').checked,
        links_materiais: document.getElementById('linksTrein').value ? document.getElementById('linksTrein').value.split('\n') : null
    };
    try {
        const endpoint = id ? `/treinamentos/catalogo/${id}` : '/treinamentos/catalogo';
        const method = id ? 'PUT' : 'POST';
        await chamarAPI(endpoint, method, body);
        bootstrap.Modal.getInstance(document.getElementById('treinamentoModal')).hide();
        carregarCatalogo();
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

// Preenche o modal de treinamento para edição
async function editarTreinamento(id) {
    try {
        const t = await chamarAPI(`/treinamentos/catalogo/${id}`);
        document.getElementById('treinamentoId').value = t.id;
        document.getElementById('nomeTrein').value = t.nome;
        document.getElementById('codigoTrein').value = t.codigo;
        document.getElementById('tipoTrein').value = t.tipo || 'Inicial';
        document.getElementById('conteudoTrein').value = t.conteudo_programatico || '';
        document.getElementById('cargaTrein').value = t.carga_horaria || '';
        document.getElementById('capacidadeTrein').value = t.capacidade_maxima || '';
        document.getElementById('temPratica').checked = t.tem_pratica;
        document.getElementById('linksTrein').value = (t.links_materiais || []).join('\n');
        new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
    } catch(e) {
        showToast(`Não foi possível carregar dados para edição: ${e.message}`, 'danger');
    }
}

// Exclui um treinamento do catálogo
async function excluirTreinamento(id) {
    if (!confirm('Excluir treinamento?')) return;
    try {
        await chamarAPI(`/treinamentos/catalogo/${id}`, 'DELETE');
        carregarCatalogo();
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

/**
 * Abre o modal de inscrição para administradores.
 * @param {number} turmaId - O ID da turma onde o participante será inscrito.
 */
function abrirModalInscricaoAdmin(turmaId) {
    const modalEl = document.getElementById('adminInscricaoModal');
    if (!modalEl) {
        console.error('O modal de inscrição não foi encontrado na página.');
        return;
    }
    document.getElementById('adminInscricaoForm').reset();
    document.getElementById('adminTurmaId').value = turmaId;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
}

/**
 * Envia os dados do formulário de inscrição do administrador para o servidor.
 */
async function enviarInscricaoAdmin() {
    const btn = document.getElementById('btnEnviarAdminInscricao');

    await executarAcaoComFeedback(btn, async () => {
        const turmaId = document.getElementById('adminTurmaId').value;
        const body = {
            nome: document.getElementById('adminNome').value,
            email: document.getElementById('adminEmail').value,
            cpf: document.getElementById('adminCpf').value,
            data_nascimento: document.getElementById('adminDataNascimento').value || null,
            empresa: document.getElementById('adminEmpresa').value || null
        };

        try {
            await chamarAPI(`/treinamentos/turmas/${turmaId}/inscricoes/admin`, 'POST', body);
            showToast('Participante inscrito com sucesso!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('adminInscricaoModal'));
            modal.hide();
            if (document.getElementById('inscricoesTableBody')) {
                await carregarInscricoes(turmaId);
            }
        } catch (e) {
            showToast(e.message, 'danger');
            throw e;
        }
    });
}

// Carrega a lista de turmas na tabela, agora com lógica para desativar botões.
async function carregarTurmas() {
    try {
        const turmas = await chamarAPI('/treinamentos/agendadas');
        const tbody = document.getElementById('turmasTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (turmas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma turma cadastrada.</td></tr>';
            return;
        }

        for (const t of turmas) {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${t.turma_id}</td>
                <td>${escapeHTML(t.treinamento.nome)}</td>
                <td>${escapeHTML(t.horario || 'N/D')}</td>
                <td>${formatarData(t.data_inicio)}</td>
                <td>${formatarData(t.data_fim)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning me-1" onclick="convocarTodosDaTurma(${t.turma_id})" title="Convocar Todos">
                        <i class="bi bi-broadcast"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="abrirModalInscricaoAdmin(${t.turma_id})" title="Adicionar Participante">
                        <i class="bi bi-person-plus"></i>
                    </button>
                    <a class="btn btn-sm btn-outline-info me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}" title="Ver Inscrições"><i class="bi bi-people"></i></a>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarTurma(${t.turma_id})" title="Editar Turma"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusaoTurma(${t.turma_id})" title="Excluir Turma"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

// Convoca todos os participantes de uma turma
function convocarTodosDaTurma(turmaId) {
    turmaParaConvocarId = turmaId;
    const modalEl = document.getElementById('confirmacaoConvocarModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

async function executarConvocacao() {
    if (!turmaParaConvocarId) return;
    const modalEl = document.getElementById('confirmacaoConvocarModal');
    const modal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;

    try {
        await chamarAPI(`/treinamentos/turmas/${turmaParaConvocarId}/convocar-todos`, 'POST');
        showToast('Todos os participantes foram convocados com sucesso!', 'success');
    } catch (e) {
        showToast(`Não foi possível convocar: ${e.message}`, 'danger');
    } finally {
        if (modal) {
            modal.hide();
        }
        turmaParaConvocarId = null;
    }
}

function confirmarExclusaoTurma(id) {
    turmaParaExcluirId = id;
    const modalEl = document.getElementById('confirmacaoExcluirModal');
    if (modalEl) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }
}

async function executarExclusao() {
    if (!turmaParaExcluirId) return;
    const modalEl = document.getElementById('confirmacaoExcluirModal');
    const modal = modalEl ? bootstrap.Modal.getOrCreateInstance(modalEl) : null;

    try {
        await chamarAPI(`/treinamentos/turmas/${turmaParaExcluirId}`, 'DELETE');
        showToast('Turma excluída com sucesso!', 'success');
        carregarTurmas();
    } catch (e) {
        showToast(`Não foi possível excluir: ${e.message}`, 'danger');
    } finally {
        if (modal) {
            modal.hide();
        }
        turmaParaExcluirId = null;
    }
}


// Carrega instrutores para o select
async function carregarInstrutores() {
    if (listaDeInstrutores.length > 0) return; // Evita recarregar
    try {
        listaDeInstrutores = await chamarAPI('/instrutores');
    } catch(e) {
        console.error("Falha ao carregar instrutores", e);
    }
}

// Carrega locais de realização para o select
async function carregarLocaisRealizacao() {
    if (listaDeLocaisRealizacao.length > 0) return; // Evita recarregar
    try {
        listaDeLocaisRealizacao = await chamarAPI('/treinamentos/locais-realizacao');
    } catch(e) {
        console.error("Falha ao carregar locais de realização", e);
        showToast('Não foi possível carregar os locais de realização.', 'danger');
    }
}

/**
 * Função centralizada para abrir o modal de turma, seja para criar ou editar.
 * @param {number|null} id - O ID da turma para editar, ou null para criar uma nova.
 */
async function abrirModalTurma(id = null) {
    const form = document.getElementById('turmaForm');
    form.reset();
    document.getElementById('turmaId').value = id || '';
    document.getElementById('teoriaOnline').checked = false;

    // Popula o select de treinamentos
    const selectTrein = document.getElementById('turmaTreinamentoId');
    selectTrein.innerHTML = '<option value="">Selecione um treinamento...</option>';
    if (catalogoDeTreinamentos.length === 0) {
        await carregarCatalogo();
    }
    catalogoDeTreinamentos.forEach(t => {
        selectTrein.innerHTML += `<option value="${t.id}">${escapeHTML(t.nome)}</option>`;
    });

    // Popula o select de instrutores
    const selectInstrutor = document.getElementById('instrutorId');
    selectInstrutor.innerHTML = '<option value="">Selecione um instrutor...</option>';
    if (listaDeInstrutores.length === 0) {
        await carregarInstrutores();
    }
    listaDeInstrutores.forEach(i => {
        selectInstrutor.innerHTML += `<option value="${i.id}">${escapeHTML(i.nome)}</option>`;
    });

    // Popula o select de locais de realização
    const selectLocal = document.getElementById('localRealizacao');
    selectLocal.innerHTML = '<option value="">Selecione...</option>';
    if (listaDeLocaisRealizacao.length === 0) {
        await carregarLocaisRealizacao();
    }
    listaDeLocaisRealizacao.forEach(local => {
        selectLocal.innerHTML += `<option value="${escapeHTML(local.nome)}">${escapeHTML(local.nome)}</option>`;
    });

    // Se for edição, busca os dados da turma
    if (id) {
        try {
            const t = await chamarAPI(`/treinamentos/turmas/${id}`);
            selectTrein.value = t.treinamento_id;
            document.getElementById('dataInicio').value = t.data_inicio ? t.data_inicio.split('T')[0] : '';

            // Dispara o evento de change para atualizar a carga horária e data mínima
            selectTrein.dispatchEvent(new Event('change'));

            document.getElementById('dataFim').value = t.data_fim ? t.data_fim.split('T')[0] : '';
            document.getElementById('localRealizacao').value = t.local_realizacao || '';
            document.getElementById('instrutorId').value = t.instrutor_id || '';
            document.getElementById('horario').value = t.horario || '';
            document.getElementById('teoriaOnline').checked = !!t.teoria_online;

        } catch(e) {
            showToast(`Não foi possível carregar dados da turma: ${e.message}`, 'danger');
            return; // Não abre o modal se houver erro
        }
    } else {
        // Se for novo
        document.getElementById('cargaHoraria').value = '';
        document.getElementById('dataFim').min = ''; // Limpa a restrição
        document.getElementById('teoriaOnline').checked = false;
    }

    new bootstrap.Modal(document.getElementById('turmaModal')).show();
}

// (NOVA FUNÇÃO) - Chamada pelo botão "NOVA TURMA"
function novaTurma() {
    abrirModalTurma(null);
}

// (FUNÇÃO CORRIGIDA) - Chamada pelo botão de editar
function editarTurma(id) {
    abrirModalTurma(id);
}

// Salva a turma (nova ou existente)
async function salvarTurma() {
    const id = document.getElementById('turmaId').value;
    const body = {
        treinamento_id: parseInt(document.getElementById('turmaTreinamentoId').value),
        data_inicio: document.getElementById('dataInicio').value,
        data_fim: document.getElementById('dataFim').value,
        local_realizacao: document.getElementById('localRealizacao').value,
        horario: document.getElementById('horario').value,
        instrutor_id: parseInt(document.getElementById('instrutorId').value) || null
    };
    const teoriaOnline = document.getElementById('teoriaOnline')?.checked ?? false;
    body.teoria_online = teoriaOnline;

    if (!body.treinamento_id || !body.data_inicio || !body.data_fim) {
        showToast("Por favor, preencha todos os campos obrigatórios.", "warning");
        return;
    }

    try {
        const endpoint = id ? `/treinamentos/turmas/${id}` : '/treinamentos/turmas';
        const method = id ? 'PUT' : 'POST';
        await chamarAPI(endpoint, method, body);
        bootstrap.Modal.getInstance(document.getElementById('turmaModal')).hide();
        carregarTurmas();
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

// NOVA FUNÇÃO: Atualiza a data de término mínima
function atualizarDataMinimaTermino() {
    const selectTreinamento = document.getElementById('turmaTreinamentoId');
    const dataInicioInput = document.getElementById('dataInicio');
    const dataFimInput = document.getElementById('dataFim');

    const selectedId = parseInt(selectTreinamento.value);
    const dataInicio = dataInicioInput.value;

    if (!selectedId || !dataInicio) {
        dataFimInput.min = '';
        return;
    }

    const treinamento = catalogoDeTreinamentos.find(t => t.id === selectedId);
    if (treinamento && treinamento.carga_horaria > 0) {
        const diasMinimos = Math.ceil(treinamento.carga_horaria / 8);

        const dataInicioObj = new Date(dataInicio + 'T00:00:00-03:00');
        const dataFimMinimaObj = new Date(dataInicioObj);
        dataFimMinimaObj.setDate(dataInicioObj.getDate() + diasMinimos - 1);

        const dataFimMinimaStr = dataFimMinimaObj.toISOString().split('T')[0];

        dataFimInput.min = dataFimMinimaStr;

        if (dataFimInput.value && dataFimInput.value < dataFimMinimaStr) {
            dataFimInput.value = dataFimMinimaStr;
        }
    } else {
        dataFimInput.min = dataInicio;
    }
}

/**
 * Carrega os dados da turma selecionada e preenche o cabeçalho da página.
 * Retorna true se o treinamento possuir parte prática.
 */
async function carregarDetalhesDaTurma(turmaId) {
    try {
        const dados = await chamarAPI(`/treinamentos/turmas/${turmaId}`);
        const treinamento = dados.treinamento || {};
        const instrutor = dados.instrutor || {};

        document.getElementById('infoNomeTreinamento').textContent = treinamento.nome || 'Não informado';
        document.getElementById('infoInstrutor').textContent = instrutor.nome || 'Não informado';
        document.getElementById('infoPeriodo').textContent = `${formatarData(dados.data_inicio)} a ${formatarData(dados.data_fim)}`;
        document.getElementById('infoDuracao').textContent = treinamento.carga_horaria ? `${treinamento.carga_horaria} horas` : '-';
        document.getElementById('infoHorario').textContent = dados.horario || '-';
        document.getElementById('infoLocal').textContent = dados.local_realizacao || '-';
        document.getElementById('infoConteudo').textContent = treinamento.conteudo_programatico || 'Nenhum conteúdo programático informado.';

        const temPratica = treinamento.tem_pratica === true;
        const thPratica = document.getElementById('thPresencaPratica');
        if (thPratica) {
            thPratica.style.display = temPratica ? '' : 'none';
        }
        return temPratica;
    } catch (e) {
        showToast(`Não foi possível carregar detalhes da turma: ${e.message}`, 'danger');
        return false;
    }
}

// Carrega as inscrições de uma turma específica
async function carregarInscricoes(turmaId) {
    const temPratica = await carregarDetalhesDaTurma(turmaId);
    try {
        const inscricoes = await chamarAPI(`/treinamentos/turmas/${turmaId}/inscricoes`);
        const tbody = document.getElementById('inscricoesTableBody');
        tbody.innerHTML = '';
        if (inscricoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">Nenhuma inscrição.</td></tr>';
            return;
        }

        for (const i of inscricoes) {
            const tr = document.createElement('tr');
            tr.dataset.id = i.id;

            const statusAprovado = i.status_aprovacao === 'Aprovado' ? 'selected' : '';
            const statusReprovado = i.status_aprovacao === 'Reprovado' ? 'selected' : '';

            const cpfFormatado = i.cpf
                ? (window.FormValidation?.maskers?.cpf?.(i.cpf) ?? i.cpf)
                : '';

            const tdPraticaHtml = temPratica ? `
                <td class="text-center" data-col="presenca_pratica">
                    <input class="form-check-input presenca-pratica-check" type="checkbox" ${i.presenca_pratica ? 'checked' : ''}>
                </td>` : '';

            const acoesHtml = `
                <td>
                    <button class="btn btn-sm btn-secondary me-1 btn-convocar" title="Convocar" data-inscricao-id="${i.id}">
                        <i class="bi bi-envelope"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusaoParticipante(${i.id}, '${escapeHTML(i.nome)}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            
            tr.innerHTML = `
                <td>${escapeHTML(i.nome)}</td>
                <td>${escapeHTML(cpfFormatado)}</td>
                <td>${i.empresa || ''}</td>
                <td class="text-center" data-col="presenca_teoria">
                    <input class="form-check-input presenca-teoria-check" type="checkbox" ${i.presenca_teoria ? 'checked' : ''}>
                </td>
                ${tdPraticaHtml}
                <td data-col="nota_teoria">
                    <input type="number" class="form-control form-control-sm nota-teoria-input" value="${i.nota_teoria !== null ? i.nota_teoria : ''}" min="0" max="100" step="0.1">
                </td>
                <td data-col="nota_pratica">
                    <input type="number" class="form-control form-control-sm nota-pratica-input" value="${i.nota_pratica !== null ? i.nota_pratica : ''}" min="0" max="100" step="0.1">
                </td>
                <td data-col="status">
                    <select class="form-select form-select-sm status-aprovacao-select">
                        <option value="">Selecione...</option>
                        <option value="Aprovado" ${statusAprovado}>Aprovado</option>
                        <option value="Reprovado" ${statusReprovado}>Reprovado</option>
                    </select>
                </td>
                ${acoesHtml}
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

// Função para confirmar e executar a exclusão do participante
function confirmarExclusaoParticipante(inscricaoId, nome) {
    if (confirm(`Tem a certeza de que deseja remover o participante "${nome}" da turma?`)) {
        executarExclusaoParticipante(inscricaoId);
    }
}

// Função que chama a API para excluir
async function executarExclusaoParticipante(inscricaoId) {
    try {
        await chamarAPI(`/treinamentos/inscricoes/${inscricaoId}`, 'DELETE');
        showToast('Participante removido com sucesso!', 'success');

        const linhaParaRemover = document.querySelector(`#inscricoesTableBody tr[data-id='${inscricaoId}']`);
        if (linhaParaRemover) {
            linhaParaRemover.remove();
        }
    } catch (e) {
        showToast(`Não foi possível remover participante: ${e.message}`, 'danger');
    }
}

// Salva notas, status e presença de todas as inscrições
async function salvarAlteracoesInscricoes() {
    const btn = document.getElementById('btnSalvarAlteracoes');
    if (!btn) return;

    await executarAcaoComFeedback(btn, async () => {
        const linhas = document.querySelectorAll('#inscricoesTableBody tr');
        const promessas = [];

        linhas.forEach(linha => {
            const id = linha.dataset.id;
            if (!id) return;

            const checkTeoria = linha.querySelector('.presenca-teoria-check');
            const checkPratica = linha.querySelector('.presenca-pratica-check');

            const body = {
                nota_teoria: linha.querySelector('.nota-teoria-input').value,
                nota_pratica: linha.querySelector('.nota-pratica-input').value,
                status_aprovacao: linha.querySelector('.status-aprovacao-select').value,
                presenca_teoria: checkTeoria ? checkTeoria.checked : false,
                presenca_pratica: checkPratica ? checkPratica.checked : false
            };

            promessas.push(chamarAPI(`/treinamentos/inscricoes/${id}/avaliar`, 'PUT', body));
        });

        try {
            await Promise.all(promessas);
            showToast('Todas as alterações foram salvas com sucesso!', 'success');
        } catch (e) {
            console.error("Não foi possível salvar alterações:", e);
            throw e;
        }
    });
}


// Envia convocação por e-mail ao clicar no botão correspondente
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-convocar');
    if (!btn) return;
    const id = btn.getAttribute('data-inscricao-id');
    btn.disabled = true;
    try {
        await chamarAPI(`/inscricoes/${id}/convocar`, 'POST');
        showToast('Convocação enviada por e-mail.', 'success');
    } catch (err) {
        console.error(err);
        showToast('Falha ao enviar a convocação.', 'danger');
    } finally {
        btn.disabled = false;
    }
});

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    const modalEl = document.getElementById('confirmacaoExcluirModal');
    if (modalEl) {
        confirmacaoModal = new bootstrap.Modal(modalEl);
        document.getElementById('btnConfirmarExclusao').addEventListener('click', executarExclusao);
    }
    if (document.getElementById('catalogoTableBody')) {
        carregarCatalogo();
    }
    if (document.getElementById('turmasTableBody')) {
        carregarTurmas();
    }

    const btnEnviarAdmin = document.getElementById('btnEnviarAdminInscricao');
    if (btnEnviarAdmin) {
        btnEnviarAdmin.addEventListener('click', enviarInscricaoAdmin);
    }

    const formTreinamento = document.getElementById('treinamentoForm');
    if (formTreinamento) {
        formTreinamento.addEventListener('submit', (e) => {
            e.preventDefault();
            salvarTreinamento();
        });
    }

    const btnSalvar = document.getElementById('btnSalvarAlteracoes');
    if (btnSalvar) {
        btnSalvar.addEventListener('click', salvarAlteracoesInscricoes);
    }

    // Lógica para o novo modal de exportação
    const exportarModalEl = document.getElementById('exportarModal');
    if (exportarModalEl) {
        const exportarModal = new bootstrap.Modal(exportarModalEl);
        const btnAbrirModal = document.getElementById('btnExportarInscricoes');
        const btnPDF = document.getElementById('btnExportarPDF');
        const btnXLSX = document.getElementById('btnExportarXLSX');
        const params = new URLSearchParams(window.location.search);
        const turmaId = params.get('turma');

        if (btnAbrirModal) {
            btnAbrirModal.addEventListener('click', () => {
                exportarModal.show();
            });
        }

        const handleExport = async (formato, btn) => {
            if (!turmaId) {
                showToast('ID da turma não encontrado.', 'danger');
                return;
            }
            const endpoint = `/treinamentos/turmas/${turmaId}/inscricoes/export`;
            const nomeArquivo = `inscricoes_turma_${turmaId}`;

            await executarAcaoComFeedback(btn, async () => {
                await exportarDados(endpoint, formato, nomeArquivo);
            });
            exportarModal.hide();
        };

        if (btnPDF) {
            btnPDF.addEventListener('click', () => handleExport('pdf', btnPDF));
        }

        if (btnXLSX) {
            btnXLSX.addEventListener('click', () => handleExport('xlsx', btnXLSX));
        }
    }

    const btnConfirmarConvocacao = document.getElementById('btnConfirmarConvocacao');
    if (btnConfirmarConvocacao) {
        btnConfirmarConvocacao.addEventListener('click', executarConvocacao);
    }

    // Listener para o select de treinamento no modal de turma
    const selectTreinamento = document.getElementById('turmaTreinamentoId');
    const dataInicioInput = document.getElementById('dataInicio');

    if (selectTreinamento) {
        selectTreinamento.addEventListener('change', () => {
            const cargaHorariaInput = document.getElementById('cargaHoraria');
            const selectedId = parseInt(selectTreinamento.value);
            const treinamento = catalogoDeTreinamentos.find(t => t.id === selectedId);

            cargaHorariaInput.value = (treinamento && treinamento.carga_horaria) ? treinamento.carga_horaria : '';
            atualizarDataMinimaTermino();
        });
    }

    if (dataInicioInput) {
        dataInicioInput.addEventListener('change', atualizarDataMinimaTermino);
    }
});
