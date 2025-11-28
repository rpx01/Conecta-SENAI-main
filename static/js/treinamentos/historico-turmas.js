document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    carregarHistorico();

    const usuario = getUsuarioLogado();
    if (usuario) {
        document.getElementById('userName').textContent = usuario.nome;
    }

    const btnEnviarAdmin = document.getElementById('btnEnviarAdminInscricao');
    if (btnEnviarAdmin) {
        btnEnviarAdmin.addEventListener('click', enviarInscricaoAdmin);
    }
});

async function carregarHistorico() {
    try {
        const turmas = await chamarAPI('/treinamentos/turmas-ativas');
        const tbody = document.getElementById('turmasTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        if (turmas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum hist\\u00f3rico de turmas encontrado.</td></tr>';
            return;
        }

        const hoje = new Date().toISOString().split('T')[0];

        for (const t of turmas) {
            const tr = document.createElement('tr');
            let botoesAcoes = '';
            const dataInicio = t.data_inicio.split('T')[0];
            const dataFim = t.data_fim.split('T')[0];

            if (dataInicio <= hoje && dataFim >= hoje) {
                botoesAcoes = `
                    <button class="btn btn-sm btn-outline-success me-1" onclick="abrirModalInscricaoAdmin(${t.turma_id})" title="Adicionar Participante">
                        <i class="bi bi-person-plus"></i>
                    </button>
                    <a class="btn btn-sm btn-outline-info me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}" title="Ver Inscri\\u00e7\\u00f5es"><i class="bi bi-people"></i></a>
                `;
            } else if (dataFim < hoje) {
                botoesAcoes = `
                    <a class="btn btn-sm btn-outline-info me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}" title="Ver Inscri\\u00e7\\u00f5es"><i class="bi bi-people"></i></a>
                `;
            }

            tr.innerHTML = `
                <td>${t.turma_id}</td>
                <td>${escapeHTML(t.treinamento.nome)}</td>
                <td>${escapeHTML(t.horario || 'N/D')}</td>
                <td>${formatarData(t.data_inicio)}</td>
                <td>${formatarData(t.data_fim)}</td>
                <td>${botoesAcoes}</td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

function abrirModalInscricaoAdmin(turmaId) {
    const modalEl = document.getElementById('adminInscricaoModal');
    if (!modalEl) {
        console.error('O modal de inscri\\u00e7\\u00e3o n\\u00e3o foi encontrado na p\\u00e1gina.');
        return;
    }
    document.getElementById('adminInscricaoForm').reset();
    document.getElementById('adminTurmaId').value = turmaId;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
}

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
        } catch (e) {
            showToast(e.message, 'danger');
            throw e;
        }
    });
}

