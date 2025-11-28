
document.addEventListener('DOMContentLoaded', async () => {
    // Garante que o usuário está autenticado antes de prosseguir
    if (!verificarAutenticacao()) return;

    // --- VARIÁVEIS DE ESTADO E ELEMENTOS DO DOM ---
    let laboratorios = [];
    let labSelecionadoId = null;
    let dataSelecionada = new Date();
    let miniCalendar;
    let agendamentoParaExcluirId = null; // Guarda o ID do agendamento a ser excluído

    const loadingEl = document.getElementById('loading-page');
    const contentEl = document.getElementById('agenda-content');
    const emptyStateEl = document.getElementById('empty-state-container');
    const seletorContainer = document.getElementById('seletor-laboratorios');
    const agendaContainer = document.getElementById('detalhes-dia-container');
    const diaDestaqueEl = document.getElementById('dia-destaque');
    const dataExtensoEl = document.getElementById('data-extenso-destaque');
    const miniCalendarEl = document.getElementById('mini-calendario');
    const navAnteriorBtn = document.getElementById('nav-anterior');
    const navHojeBtn = document.getElementById('nav-hoje');
    const navSeguinteBtn = document.getElementById('nav-seguinte');
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmarExclusaoModal'));
    const detalhesModal = new bootstrap.Modal(document.getElementById('detalhesReservaModal'));
    const detalhesContent = document.getElementById('detalhesReservaContent');

    // --- FUNÇÃO DE INICIALIZAÇÃO ---
    const inicializarPagina = async () => {
        contentEl.classList.add('d-none');
        emptyStateEl.classList.add('d-none');
        loadingEl.classList.remove('d-none');

        await carregarLaboratorios();
        
        if (laboratorios && laboratorios.length > 0) {
            inicializarMiniCalendario();
            adicionarListeners();
            
            const primeiroLabIcon = document.querySelector('.lab-icon');
            if(primeiroLabIcon) {
                labSelecionadoId = primeiroLabIcon.dataset.id;
                primeiroLabIcon.classList.add('active');
            }
            
            await atualizarVisualizacaoCompleta(dataSelecionada);
            
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');
            
            setTimeout(() => miniCalendar.updateSize(), 50);
        } else {
            loadingEl.classList.add('d-none');
            emptyStateEl.classList.remove('d-none');
        }
    };

    // --- FUNÇÕES DE LÓGICA ---

    const carregarLaboratorios = async () => {
        try {
            laboratorios = await chamarAPI('/laboratorios');
            if (seletorContainer) {
                seletorContainer.innerHTML = laboratorios.map(lab => {
                    const iconClass = (lab.classe_icone && lab.classe_icone.startsWith('bi-')) ? lab.classe_icone : 'bi-box-seam';
                    return `<div class="lab-icon" data-id="${lab.id}" title="${escapeHTML(lab.nome)}"><i class="bi ${iconClass}"></i><span>${escapeHTML(lab.nome)}</span></div>`;
                }).join('');
            }
        } catch (error) {
            showToast('Não foi possível carregar laboratórios.', 'danger');
        }
    };

    const inicializarMiniCalendario = () => {
        miniCalendar = new FullCalendar.Calendar(miniCalendarEl, {
            initialDate: dataSelecionada, locale: 'pt-br', initialView: 'dayGridMonth',
            headerToolbar: { left: 'prev', center: 'title', right: 'next' },
            buttonText: { today: 'Hoje' },
            dateClick: (info) => atualizarVisualizacaoCompleta(info.date),
        });
        miniCalendar.render();
    };
    
    const atualizarVisualizacaoCompleta = async (novaData) => {
        dataSelecionada = novaData;
        diaDestaqueEl.textContent = dataSelecionada.getDate().toString().padStart(2, '0');
        dataExtensoEl.textContent = dataSelecionada.toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long' });
        if (miniCalendar) miniCalendar.gotoDate(dataSelecionada);
        await carregarAgendaDiaria();
    };

    const carregarAgendaDiaria = async () => {
        if (!labSelecionadoId) return;
        agendaContainer.innerHTML = `<div class="text-center p-5"><div class="spinner-border spinner-border-sm"></div></div>`;
        try {
            const dataFormatada = dataSelecionada.toISOString().split('T')[0];
            const dados = await chamarAPI(`/agendamentos/agenda-diaria?laboratorio_id=${labSelecionadoId}&data=${dataFormatada}`);
            
            // Verificação para garantir que os dados estão no formato correto
            if (dados && dados.agendamentos_por_turno) {
                renderizarDetalhesDia(dados.agendamentos_por_turno);
            } else {
                throw new Error("Formato de dados da agenda inválido.");
            }
        } catch (error) {
            console.error("Erro detalhado ao carregar agenda:", error);
            showToast('Não foi possível carregar agenda diária.', 'danger');
            agendaContainer.innerHTML = '<p class="text-danger text-center">Não foi possível carregar os agendamentos.</p>';
        }
    };
    
    const renderizarDetalhesDia = (agendamentosPorTurno) => {
        const dataFormatada = dataSelecionada.toISOString().split('T')[0];
        const usuario = getUsuarioLogado();
        agendaContainer.innerHTML = ['Manhã', 'Tarde', 'Noite'].map(turno => {
            const dadosTurno = agendamentosPorTurno[turno] || { agendamentos: [], horarios_disponiveis: [] };
            return `
            <div class="card turno-card">
                <div class="card-header">> ${turno.toUpperCase()}</div>
                <div class="card-body">
                    ${dadosTurno.agendamentos.length > 0 ? `<h6><i class="bi bi-calendar-x-fill"></i> Horários Ocupados</h6>` + dadosTurno.agendamentos.map(ag => {
                        const podeGerenciar = isAdmin() || (usuario && ag.usuario_id === usuario.id);
                        return `
                        <div class="agendamento-item" data-id="${ag.id}">
                            <div class="agendamento-info">
                                <strong>${escapeHTML(ag.turma_nome)}</strong><br>
                                <span class="text-muted small"><i class="bi bi-clock-fill"></i> ${calcularIntervaloDeTempo(ag.horarios)}</span>
                            </div>
                            ${podeGerenciar ? `<div class="agendamento-acoes btn-group">
                                <a href="/laboratorios/agendamento.html?id=${ag.id}" class="btn btn-sm btn-outline-primary" title="Editar"><i class="bi bi-pencil"></i></a>
                                <button class="btn btn-sm btn-outline-danger btn-excluir" data-id="${ag.id}" title="Excluir"><i class="bi bi-trash"></i></button>
                            </div>` : ''}
                        </div>`;
                    }).join('') : ''
                    }
                    ${dadosTurno.horarios_disponiveis.length > 0 ? `
                    <h6 class="${dadosTurno.agendamentos.length > 0 ? 'mt-4' : ''}"><i class="bi bi-calendar-check-fill"></i> Horários Disponíveis</h6>
                    ${dadosTurno.horarios_disponiveis.map(h => `<span class="badge bg-light text-dark border me-1 mb-1">${h}</span>`).join('')}
                    ` : ''}
                </div>
                <div class="card-footer text-end">
                    <a href="/laboratorios/agendamento.html?lab_id=${labSelecionadoId}&data=${dataFormatada}&turno=${turno}" class="btn btn-primary btn-sm"><i class="bi bi-plus"></i> Novo Agendamento</a>
                </div>
            </div>`;
        }).join('');
    };

    function adicionarListeners() {
        seletorContainer.addEventListener('click', (e) => {
            const icon = e.target.closest('.lab-icon');
            if (icon && !icon.classList.contains('active')) {
                document.querySelectorAll('.lab-icon').forEach(i => i.classList.remove('active'));
                icon.classList.add('active');
                labSelecionadoId = icon.dataset.id;
                carregarAgendaDiaria();
            }
        });


        // ** DELEGAÇÃO DE EVENTOS PARA EXCLUSÃO E DETALHES **
        agendaContainer.addEventListener('click', (e) => {
            const btnExcluir = e.target.closest('.btn-excluir');
            if (btnExcluir) {
                agendamentoParaExcluirId = btnExcluir.dataset.id;
                confirmacaoModal.show();
                return;
            }

            const item = e.target.closest('.agendamento-item');
            if (item && !e.target.closest('.agendamento-acoes')) {
                const id = item.dataset.id;
                if (id) mostrarDetalhesReserva(id);
            }
        });

        document.getElementById('btnConfirmarExclusao').addEventListener('click', executarExclusao);
    }

    const calcularIntervaloDeTempo = (horariosJSON) => {
        try {
            const listaHorarios = Array.isArray(horariosJSON) ? horariosJSON : JSON.parse(horariosJSON || '[]');
            if (!listaHorarios || listaHorarios.length === 0) return '';
            const tempos = listaHorarios.flatMap(h => h.split(' - '));
            return `${tempos[0]} - ${tempos[tempos.length - 1]}`;
        } catch(e) { return ''; }
    };

    const mostrarDetalhesReserva = async (id) => {
        try {
            const dados = await chamarAPI(`/agendamentos/${id}/detalhes`);
            const intervalo = calcularIntervaloDeTempo(dados.horarios);
            detalhesContent.innerHTML = `
                <p><strong>Reservado por:</strong> ${escapeHTML(dados.usuario_nome || '')}</p>
                <p><strong>Data:</strong> ${formatarData(dados.data)}</p>
                <p><strong>Horário:</strong> ${intervalo}</p>
                <p><strong>Local:</strong> ${escapeHTML(dados.laboratorio)} - ${escapeHTML(dados.turno)}</p>
                ${dados.observacoes ? `<p><strong>Observações:</strong> ${escapeHTML(dados.observacoes)}</p>` : ''}
            `;
            detalhesModal.show();
        } catch (error) {
            showToast('Não foi possível carregar detalhes da reserva', 'danger');
        }
    };
    
    const executarExclusao = async () => {
        if (!agendamentoParaExcluirId) return;

        try {
            await chamarAPI(`/agendamentos/${agendamentoParaExcluirId}`, 'DELETE');
            showToast('Agendamento excluído com sucesso!', 'success');
            await carregarAgendaDiaria();
        } catch (error) {
            showToast(`Não foi possível excluir agendamento: ${error.message}`, 'danger');
        } finally {
            agendamentoParaExcluirId = null;
            confirmacaoModal.hide();
        }
    };

    inicializarPagina();
});
