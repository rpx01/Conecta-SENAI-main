function formatarDataHora(dataISO) {
    if (!dataISO) return '';
    const entrada = dataISO.endsWith('Z') || dataISO.includes('+') ? dataISO : `${dataISO}Z`;
    const data = new Date(entrada);
    return data.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    const tabelaBody = document.querySelector('#tabelaLogs tbody');

    async function carregarLogs() {
        const params = new URLSearchParams();
        const usuario = document.getElementById('filtroUsuario').value.trim();
        const data = document.getElementById('filtroData').value;
        const tipo = document.getElementById('filtroTipo').value;
        if (usuario) params.append('usuario', usuario);
        if (data) params.append('data', data);
        if (tipo) params.append('tipo', tipo);
        const logs = await chamarAPI(`/logs-agenda?${params.toString()}`, 'GET');
        atualizarTabela(logs);
    }

    function atualizarTabela(logs) {
        tabelaBody.innerHTML = '';
        if (!logs || logs.length === 0) {
            tabelaBody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum registro encontrado.</td></tr>';
            return;
        }
        logs.forEach(l => {
            const row = `<tr>
                <td>${escapeHTML(formatarDataHora(l.timestamp))}</td>
                <td>${escapeHTML(l.tipo_acao)}</td>
                <td>${escapeHTML(l.usuario)}</td>
                <td>${escapeHTML(l.laboratorio || '')}</td>
                <td>${escapeHTML(l.turno || '')}</td>
                <td>${l.data_agendamento ? escapeHTML(formatarData(l.data_agendamento)) : ''}</td>
                <td>${l.intervalo_horarios ? escapeHTML(l.intervalo_horarios) : ''}</td>
            </tr>`;
            tabelaBody.insertAdjacentHTML('beforeend', row);
        });
    }

    document.getElementById('btnAplicarFiltros').addEventListener('click', carregarLogs);
    document.getElementById('btnLimparFiltros').addEventListener('click', () => {
        document.getElementById('filtroUsuario').value = '';
        document.getElementById('filtroData').value = '';
        document.getElementById('filtroTipo').value = '';
        carregarLogs();
    });

    document.getElementById('btnExportarCsv').addEventListener('click', () => {
        exportarDados('/logs-agenda/export', 'csv', 'logs_agenda');
    });

    carregarLogs();
});
