document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    carregarLogs();
});

async function carregarLogs() {
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">Carregando...</td></tr>';

    try {
        const logs = await chamarAPI('/treinamentos/logs');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum log encontrado.</td></tr>';
            return;
        }

        tbody.innerHTML = ''; // Limpa a tabela
        logs.forEach(log => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${formatarData(log.timestamp)}</td>
                <td>${escapeHTML(log.usuario)}</td>
                <td><span class="badge bg-secondary">${escapeHTML(log.acao)}</span></td>
                <td>${escapeHTML(log.info)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Erro ao carregar logs: ${e.message}</td></tr>`;
    }
}
