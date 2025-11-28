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
    const paginacaoEl = document.getElementById('paginacaoLogs');
    let paginaAtual = 1;
    const porPagina = 10;

    async function carregarLogs(page = 1) {
        const params = new URLSearchParams();
        const usuario = document.getElementById('filtroUsuario').value.trim();
        const instrutor = document.getElementById('filtroInstrutor').value.trim();
        const data = document.getElementById('filtroData').value;
        const tipo = document.getElementById('filtroTipo').value;
        if (usuario) params.append('usuario', usuario);
        if (instrutor) params.append('instrutor', instrutor);
        if (data) params.append('data', data);
        if (tipo) params.append('tipo', tipo);
        params.append('page', page);
        params.append('per_page', porPagina);
        const resp = await chamarAPI(`/logs-rateio?${params.toString()}`, 'GET');
        paginaAtual = resp.page;
        atualizarTabela(resp.items);
        atualizarPaginacao(resp.page, resp.pages);
    }

    function atualizarTabela(logs) {
        tabelaBody.innerHTML = '';
        if (!logs || logs.length === 0) {
            tabelaBody.innerHTML = '<tr><td colspan="10" class="text-center">Nenhum registro encontrado.</td></tr>';
            return;
        }
        logs.forEach(l => {
            const row = `<tr>
                <td>${escapeHTML(formatarDataHora(l.timestamp))}</td>
                <td>${escapeHTML(l.acao)}</td>
                <td>${escapeHTML(l.usuario)}</td>
                <td>${escapeHTML(l.instrutor)}</td>
                <td>${escapeHTML(l.filial)}</td>
                <td>${escapeHTML(l.uo)}</td>
                <td>${escapeHTML(l.cr)}</td>
                <td>${escapeHTML(l.classe_valor)}</td>
                <td>${l.percentual != null ? escapeHTML(l.percentual.toFixed(2) + '%') : ''}</td>
                <td>${escapeHTML(l.observacao || '')}</td>
            </tr>`;
            tabelaBody.insertAdjacentHTML('beforeend', row);
        });
    }

    function atualizarPaginacao(pagina, totalPaginas) {
        paginacaoEl.innerHTML = '';
        const criarItem = (label, paginaAlvo, disabled = false, active = false) => {
            return `<li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${paginaAlvo}">${label}</a>
                    </li>`;
        };
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Anterior', pagina - 1, pagina <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginacaoEl.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === pagina));
        }
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Próxima', pagina + 1, pagina >= totalPaginas));

        Array.from(paginacaoEl.querySelectorAll('a[data-page]')).forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const alvo = parseInt(link.getAttribute('data-page'));
                if (!isNaN(alvo) && alvo >= 1) {
                    carregarLogs(alvo);
                }
            });
        });
    }

    document.getElementById('btnAplicarFiltros').addEventListener('click', () => carregarLogs());
    document.getElementById('btnLimparFiltros').addEventListener('click', () => {
        document.getElementById('filtroUsuario').value = '';
        document.getElementById('filtroInstrutor').value = '';
        document.getElementById('filtroData').value = '';
        document.getElementById('filtroTipo').value = '';
        carregarLogs();
    });

    document.getElementById('btnExportarCsv').addEventListener('click', () => {
        exportarDados('/logs-rateio/export', 'csv', 'logs_rateio');
    });

    carregarLogs();
});
