document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    carregarHistoricoPassado(); // Nome da função alterado para clareza
});

async function carregarHistoricoPassado() {
    try {
        // A rota /treinamentos/historico agora retorna apenas turmas passadas
        const turmas = await chamarAPI('/treinamentos/historico');
        const tbody = document.getElementById('turmasTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';
        if (turmas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum histórico de turmas encerradas encontrado.</td></tr>';
            return;
        }

        for (const t of turmas) {
            const tr = document.createElement('tr');
            // Botão de Ações simplificado, apenas para ver inscrições
            const botoesAcoes = `
                <a class="btn btn-sm btn-outline-info me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}" title="Ver Inscrições"><i class="bi bi-people"></i></a>
            `;

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
