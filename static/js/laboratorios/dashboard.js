const rootStyle = getComputedStyle(document.documentElement);

async function carregarKpis() {
    try {
        const dados = await chamarAPI('/dashboard/laboratorios/kpis');
        document.getElementById('totalLabsAtivos').textContent = dados.total_laboratorios_ativos;
        document.getElementById('totalTurmasAtivas').textContent = dados.total_turmas_ativas;
        document.getElementById('agendamentosHoje').textContent = dados.agendamentos_hoje;
        document.getElementById('agendamentosSemana').textContent = dados.agendamentos_semana;
    } catch (error) {
        console.error('Erro ao carregar KPIs:', error);
    }
}

async function carregarProximosAgendamentos() {
    const container = document.getElementById('proximosAgendamentosContainer');
    if (!container) return;
    container.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>';
    try {
        const agendamentos = await chamarAPI('/dashboard/laboratorios/proximos');
        if (agendamentos.length === 0) {
            container.innerHTML = '<p class="text-muted mb-0">Nenhum agendamento encontrado.</p>';
            return;
        }
        let html = '<div class="list-group list-group-flush">';
        agendamentos.forEach(a => {
            html += `<div class="list-group-item d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${escapeHTML(a.laboratorio)} - ${escapeHTML(a.turma)}</h6>
                            <small class="text-muted">${escapeHTML(a.turno)}</small>
                        </div>
                        <small>${formatarData(a.data)}</small>
                    </div>`;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<p class="text-danger mb-0">Erro ao carregar dados.</p>';
        console.error('Erro ao carregar próximos agendamentos:', error);
    }
}

async function carregarLabsMaisUtilizados() {
    try {
        const dados = await chamarAPI('/dashboard/laboratorios/mais-utilizados');
        const ctx = document.getElementById('graficoLabsMaisUtilizados');
        if (!ctx) return;
        const labels = dados.map(d => d.laboratorio);
        const valores = dados.map(d => d.total);
        new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: [{ data: valores, backgroundColor: rootStyle.getPropertyValue('--primary-color').trim() }] },
            options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });
    } catch (error) {
        console.error('Erro ao carregar laboratórios mais utilizados:', error);
    }
}

async function carregarTendenciaMensal() {
    try {
        const dados = await chamarAPI('/dashboard/laboratorios/tendencia-mensal');
        const ctx = document.getElementById('graficoTendenciaMensal');
        if (!ctx) return;
        const labels = dados.map(d => d.mes);
        const valores = dados.map(d => d.total);
        new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{ label: 'Agendamentos', data: valores, borderColor: rootStyle.getPropertyValue('--primary-color').trim(), tension: 0.3 }]
            },
            options: { scales: { y: { beginAtZero: true } } }
        });
    } catch (error) {
        console.error('Erro ao carregar tendência mensal:', error);
    }
}
