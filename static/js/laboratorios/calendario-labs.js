// CÓDIGO COMPLETO E ADAPTADO PARA O FICHEIRO calendario-labs.js

document.addEventListener('DOMContentLoaded', function() {
    // Garante que o usuário está autenticado
    if (!verificarAutenticacao()) return;
    
    // Atualiza o nome do usuário na navbar
    const usuario = getUsuarioLogado();
    if(usuario) {
        const userNameElement = document.getElementById('userName') || document.getElementById('nomeUsuarioNav');
        if(userNameElement) userNameElement.textContent = usuario.nome;
    }
    
    // Carrega os dados para os filtros e depois inicializa o calendário
    carregarLaboratoriosParaFiltro();
    configurarFiltros();
    inicializarCalendario();
});

let calendar; // Variável global para o calendário

function inicializarCalendario() {
    const calendarEl = document.getElementById('calendario');
    if (!calendarEl) {
        console.error("Elemento do calendário não encontrado!");
        return;
    }
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,day'
        },
        buttonText: { today: 'Hoje', month: 'Mês', week: 'Semana', day: 'Dia' },
        height: 'auto',

        dayCellContent: function(arg) {
            const dateStr = arg.date.toISOString().slice(0, 10);
            return {
                html: `<div class="fc-daygrid-day-number">${arg.dayNumberText}</div>
                       <div class="day-pills-container" data-date="${dateStr}"></div>`
            };
        },

        // Evento que dispara sempre que a visualização do calendário é alterada
        datesSet: function(dateInfo) {
            aplicarFiltrosCalendario();
        },
        
        dateClick: function(info) {
            // abrir modal de resumo aqui
        }
    });
    
    calendar.render();
    document.getElementById('loadingCalendario').style.display = 'none';
    document.getElementById('calendario').style.display = 'block';
}

async function carregarLaboratoriosParaFiltro() {
    try {
        const laboratorios = await chamarAPI('/laboratorios');
        const select = document.getElementById('filtroLaboratorio');
        if (!select) return;
        select.innerHTML = '<option value="">Todos os laboratórios</option>';
        laboratorios.forEach(lab => {
            select.innerHTML += `<option value="${lab.nome}">${lab.nome}</option>`;
        });
    } catch (error) {
        console.error('Não foi possível carregar laboratórios:', error);
    }
}

function configurarFiltros() {
    const form = document.getElementById('filtrosForm') || document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            aplicarFiltrosCalendario();
        });
    }
}

async function aplicarFiltrosCalendario() {
    if (!calendar) return;

    const loadingEl = document.getElementById('loadingCalendario');
    if(loadingEl) loadingEl.style.display = 'block';

    try {
        const params = new URLSearchParams({
            data_inicio: calendar.view.activeStart.toISOString().slice(0, 10),
            data_fim: calendar.view.activeEnd.toISOString().slice(0, 10),
        });

        // Adaptação para os filtros de Agendamento
        const laboratorio = document.getElementById('filtroLaboratorio').value;
        const turno = document.getElementById('filtroTurno').value;
        if (laboratorio) params.append('laboratorio', laboratorio);
        if (turno) params.append('turno', turno);

        // Chamada à API correta
        const data = await chamarAPI(`/agendamentos/resumo-calendario?${params.toString()}`);
        
        if (data && data.resumo) {
            renderizarPillulas(data.resumo, data.total_recursos);
        }
        
    } catch (error) {
        console.error("Não foi possível aplicar filtros e buscar resumo:", error);
        showToast("Não foi possível carregar os dados do calendário.", "danger");
    } finally {
        if(loadingEl) loadingEl.style.display = 'none';
    }
}

function renderizarPillulas(resumo, totalRecursos) {
    document.querySelectorAll('.day-pills-container').forEach(container => {
        const dataStr = container.getAttribute('data-date');
        const diaResumo = resumo ? resumo[dataStr] : null;
        let html = '';

        if (totalRecursos > 0) {
            ['Manhã', 'Tarde', 'Noite'].forEach(turno => {
                const ocupados = diaResumo && diaResumo[turno] ? diaResumo[turno].ocupados : 0;
                
                let statusClass = 'turno-livre'; // Padrão é livre
                if (ocupados > 0) {
                    statusClass = ocupados >= totalRecursos ? 'turno-cheio' : 'turno-parcial';
                }
                
                html += `<div class="pill-turno ${statusClass}">${turno}: ${ocupados}/${totalRecursos}</div>`;
            });
        }
        container.innerHTML = html;
    });
}
