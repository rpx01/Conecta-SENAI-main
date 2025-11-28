// Lógica para calendário híbrido (visão mensal e semanal)
let activeView = 'mensal';
let currentDate = new Date();
let calendar; // FullCalendar instance

document.addEventListener('DOMContentLoaded', () => {
    const viewMensalRadio = document.getElementById('view-mensal');
    const viewSemanalRadio = document.getElementById('view-semanal');
    const navAnterior = document.getElementById('nav-anterior');
    const navSeguinte = document.getElementById('nav-seguinte');
    const navHoje = document.getElementById('nav-hoje');

    if(viewMensalRadio && viewSemanalRadio) {
        viewMensalRadio.addEventListener('change', () => {
            if(viewMensalRadio.checked) mudarVisao('mensal');
        });
        viewSemanalRadio.addEventListener('change', () => {
            if(viewSemanalRadio.checked) mudarVisao('semanal');
        });
    }

    if(navAnterior) navAnterior.addEventListener('click', () => navegar(-1));
    if(navSeguinte) navSeguinte.addEventListener('click', () => navegar(1));
    if(navHoje) navHoje.addEventListener('click', () => {
        currentDate = new Date();
        renderActiveView();
    });

    renderActiveView();
});

function mudarVisao(view) {
    activeView = view;
    document.getElementById('visao-mensal-container').style.display = view === 'mensal' ? '' : 'none';
    document.getElementById('visao-semanal-container').style.display = view === 'semanal' ? '' : 'none';
    renderActiveView();
}

function navegar(delta) {
    if(activeView === 'mensal') {
        currentDate.setMonth(currentDate.getMonth() + delta);
    } else {
        currentDate.setDate(currentDate.getDate() + (7 * delta));
    }
    renderActiveView();
}

function renderActiveView() {
    atualizarPeriodoHeader();
    if(activeView === 'mensal') {
        renderizarVisaoMensal();
    } else {
        renderizarVisaoSemanal();
    }
}

function atualizarPeriodoHeader() {
    const formatter = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' });
    const header = document.getElementById('periodo-header');
    if(activeView === 'mensal') {
        header.textContent = formatter.format(currentDate);
    } else {
        const inicio = new Date(currentDate);
        inicio.setDate(inicio.getDate() - inicio.getDay() + 1);
        const fim = new Date(inicio);
        fim.setDate(inicio.getDate() + 6);
        header.textContent = `${inicio.toLocaleDateString('pt-BR')} - ${fim.toLocaleDateString('pt-BR')}`;
    }
}

async function renderizarVisaoMensal() {
    mostrarLoading(true);
    const inicio = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const fim = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    try {
        const params = new URLSearchParams({
            data_inicio: inicio.toISOString().slice(0,10),
            data_fim: fim.toISOString().slice(0,10)
        });
        const resumo = await fetch(`/api/agendamentos/resumo-calendario?${params.toString()}`)
            .then(r => r.json());
        construirCalendarioMensal(inicio, resumo);
    } catch(e) {
        console.error('Erro ao carregar visão mensal', e);
    } finally {
        mostrarLoading(false);
    }
}

function construirCalendarioMensal(inicio, dados) {
    const container = document.getElementById('visao-mensal-container');
    if(!container) return;
    container.innerHTML = '<div id="calendario-mensal"></div>';

    if(calendar) calendar.destroy();
    calendar = new FullCalendar.Calendar(document.getElementById('calendario-mensal'), {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        initialDate: inicio,
        headerToolbar: false,
        dayCellContent: function(arg) {
            const dateStr = arg.date.toISOString().slice(0,10);
            const resumoDia = dados && dados.resumo ? dados.resumo[dateStr] : null;
            let html = `<div class="fc-daygrid-day-number">${arg.dayNumberText}</div>`;
            html += `<div class="day-pills-container">`;
            ['Manhã','Tarde','Noite'].forEach(turno => {
                const ocupados = resumoDia && resumoDia[turno] ? resumoDia[turno].ocupados : 0;
                const total = dados.total_recursos || 0;
                let statusClass = 'turno-livre';
                if(ocupados > 0) statusClass = ocupados >= total ? 'turno-cheio' : 'turno-parcial';
                html += `<div class="pill-turno ${statusClass}">${turno}: ${ocupados}/${total}</div>`;
            });
            html += `</div>`;
            return { html };
        }
    });
    calendar.render();
}

async function renderizarVisaoSemanal() {
    mostrarLoading(true);
    const inicio = new Date(currentDate);
    inicio.setDate(inicio.getDate() - inicio.getDay() + 1);
    try {
        const params = new URLSearchParams({ data_ref: inicio.toISOString().slice(0,10) });
        const data = await fetch(`/api/agendamentos/visao-semanal?${params.toString()}`)
            .then(r => r.json());
        construirTabelaSemanal(inicio, data);
    } catch(e) {
        console.error('Erro ao carregar visão semanal', e);
    } finally {
        mostrarLoading(false);
    }
}

function construirTabelaSemanal(inicio, dados) {
    const container = document.getElementById('visao-semanal-container');
    if(!container) return;
    const dias = [];
    for(let i=0;i<7;i++) {
        const d = new Date(inicio);
        d.setDate(inicio.getDate()+i);
        dias.push(d);
    }
    let html = '<table class="table table-bordered small"><caption class="visually-hidden">Visão semanal de ocupação dos laboratórios</caption><thead class="table-primary"><tr><th scope="col">Laboratório</th>';
    dias.forEach(d => {
        html += `<th scope="col">${d.toLocaleDateString('pt-BR')}</th>`;
    });
    html += '</tr></thead><tbody>';
    for(const lab in dados) {
        html += `<tr><th scope="row">${lab}</th>`;
        dias.forEach(d => {
            const diaStr = d.toISOString().slice(0,10);
            const info = (dados[lab] && dados[lab][diaStr]) || {};
            html += '<td>';
            ['Manhã','Tarde','Noite'].forEach(turno => {
                const lista = info[turno] || [];
                if(lista.length) {
                    lista.forEach(ag => {
                        const t = ag.turma || '';
                        html += `<div class="bg-primary text-white rounded px-1 mb-1">${t}</div>`;
                    });
                } else {
                    html += '<button class="btn btn-sm btn-light">+</button>';
                }
            });
            html += '</td>';
        });
        html += '</tr>';
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function mostrarLoading(show) {
    const el = document.getElementById('loading-view');
    if(el) el.style.display = show ? 'block' : 'none';
}
