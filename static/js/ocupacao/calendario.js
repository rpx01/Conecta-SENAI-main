let calendar;
let ocupacoesData = [];
let salasData = [];
let instrutoresData = [];
let tiposOcupacao = [];
let resumoOcupacoes = {};
let diaResumoAtual = null;

const rootStyle = getComputedStyle(document.documentElement);

function getFiltroElements(nome) {
    const baseId = `filtro${nome}`;
    return [
        document.getElementById(baseId),
        document.getElementById(`${baseId}Mobile`)
    ].filter(Boolean);
}

function getFiltroValue(nome) {
    const [elemento] = getFiltroElements(nome);
    return elemento ? elemento.value : '';
}

function setFiltroValue(nome, valor) {
    const valorNormalizado = valor ?? '';
    getFiltroElements(nome).forEach(el => {
        el.dataset.selectedValue = valorNormalizado;
        el.value = valorNormalizado;
        if (el.value !== valorNormalizado) {
            
            el.dataset.selectedValue = valorNormalizado;
        }
    });
}

function popularSelectComOpcoes(selects, opcoes, opcaoPadrao) {
    selects.forEach(select => {
        const valorDesejado = select.dataset.selectedValue ?? select.value ?? '';
        select.innerHTML = '';

        if (opcaoPadrao) {
            const optionDefault = document.createElement('option');
            optionDefault.value = opcaoPadrao.value;
            optionDefault.textContent = opcaoPadrao.label;
            select.appendChild(optionDefault);
        }

        opcoes.forEach(opcao => {
            const optionEl = document.createElement('option');
            optionEl.value = opcao.value;
            optionEl.textContent = opcao.label;
            select.appendChild(optionEl);
        });

        if (valorDesejado) {
            select.value = valorDesejado;
            if (select.value !== valorDesejado) {
                select.value = opcaoPadrao ? opcaoPadrao.value : '';
            }
        }

        select.dataset.selectedValue = select.value;
    });
}

function slugifyTurno(turno) {
    return turno
        .toLowerCase()
        .normalize('NFD')
        .replace(/\p{Diacritic}/gu, '');
}

function inicializarCalendario() {
    const calendarEl = document.getElementById('calendario');
    
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            day: 'Dia'
        },
        height: 'auto',
        eventDisplay: 'block',
        dayMaxEvents: 3,
        moreLinkText: function(num) {
            return `+${num} mais`;
        },
        eventClick: function(info) {
            mostrarDetalhesOcupacao(info.event.extendedProps);
        },
        dateClick: function(info) {
            mostrarResumoDia(info.dateStr);
        },
        datesSet: function(info) {
            carregarResumoPeriodo(info.startStr, info.endStr);
        },
        events: function(fetchInfo, successCallback, failureCallback) {
            carregarOcupacoes(fetchInfo.startStr, fetchInfo.endStr)
                .then(eventos => successCallback(eventos))
                .catch(error => {
                    console.error('Erro ao carregar eventos:', error);
                    failureCallback(error);
                });
        }
    });
    
    calendar.render();
    
    document.getElementById('loadingCalendario').style.display = 'none';
    document.getElementById('calendario').style.display = 'block';
}

async function carregarOcupacoes(dataInicio, dataFim) {
    try {
        
        const params = new URLSearchParams({
            data_inicio: dataInicio.split('T')[0],
            data_fim: dataFim.split('T')[0]
        });
        
        const salaId = getFiltroValue('Sala');
        const instrutorId = getFiltroValue('Instrutor');
        const turno = getFiltroValue('Turno');
        
        if (salaId) params.append('sala_id', salaId);
        if (instrutorId) params.append('instrutor_id', instrutorId);
        if (turno) params.append('turno', turno);
        
        const response = await fetch(`${API_URL}/ocupacoes/calendario?${params.toString()}`, {
            headers: {},
            credentials: 'include'
        });
        
        if (response.ok) {
            const eventos = await response.json();
            ocupacoesData = eventos;
            return eventos.map(evento => ({
                id: evento.id,
                title: evento.title,
                start: evento.start,
                end: evento.end,
                className: getClasseTurno(evento.extendedProps.turno),
                extendedProps: evento.extendedProps
            }));
        } else {
            throw new Error('Erro ao carregar ocupações');
        }
    } catch (error) {
        console.error('Erro ao carregar ocupações:', error);
        return [];
    }
}

async function carregarResumoPeriodo(dataInicio, dataFim) {
    try {
        const params = new URLSearchParams({
            data_inicio: dataInicio.split('T')[0],
            data_fim: dataFim.split('T')[0]
        });

        const salaId = getFiltroValue('Sala');
        const instrutorId = getFiltroValue('Instrutor');
        const turno = getFiltroValue('Turno');

        if (salaId) params.append('sala_id', salaId);
        if (instrutorId) params.append('instrutor_id', instrutorId);
        if (turno) params.append('turno', turno);

        const response = await fetch(`${API_URL}/ocupacoes/resumo-periodo?${params.toString()}`, {
            headers: {},
            credentials: 'include'
        });

        if (response.ok) {
            resumoOcupacoes = await response.json();
            atualizarResumoNoCalendario();
        }
    } catch (error) {
        console.error('Erro ao carregar resumo:', error);
    }
}

function atualizarResumoNoCalendario() {
    document.querySelectorAll('.fc-daygrid-day').forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        cell.querySelectorAll('.pill-turno').forEach(e => e.remove());

        const resumoDia = resumoOcupacoes[dateStr];
        if (resumoDia) {
            const popoverParts = [];
            ['Manhã', 'Tarde', 'Noite'].forEach(turno => {
                const info = resumoDia[turno];
                if (!info) return;

                const div = document.createElement('div');
                div.classList.add('pill-turno');

                if (info.ocupadas === 0) {
                    div.classList.add('turno-livre');
                } else if (info.ocupadas === info.total_salas) {
                    div.classList.add('turno-cheio');
                } else {
                    div.classList.add('turno-parcial');
                }

                div.textContent = `${turno}: ${info.ocupadas}/${info.total_salas}`;
                cell.appendChild(div);

                const ocupadasNomes = info.salas_ocupadas.map(s => s.sala_nome).join(', ') || 'Nenhuma';
                const livresNomes = info.salas_livres.join(', ') || 'Nenhuma';
                popoverParts.push(
                    `<div><strong>${escapeHTML(turno)}</strong><br>` +
                    `Salas Ocupadas: ${escapeHTML(ocupadasNomes)}<br>` +
                    `Salas Livres: ${escapeHTML(livresNomes)}</div>`
                );
            });

            const popoverContent = popoverParts.join('<hr>');
            const existing = bootstrap.Popover.getInstance(cell);
            if (existing) existing.dispose();
            new bootstrap.Popover(cell, {
                html: true,
                trigger: 'hover focus',
                container: 'body',
                content: sanitizeHTML(popoverContent),
                placement: 'auto'
            });
        }
    });
}

function mostrarResumoDia(dataStr) {
    diaResumoAtual = dataStr;
    const resumoDia = resumoOcupacoes[dataStr];
    if (!resumoDia) return;

    const modalEl = document.getElementById('modalResumoDia');
    const modal = new bootstrap.Modal(modalEl);
    const container = document.getElementById('conteudoResumoDia');

    document.getElementById('modalResumoDiaLabel').textContent = '📊 Resumo de Ocupação – ' + formatarData(dataStr);
    container.innerHTML = '';

    ['Manhã', 'Tarde', 'Noite'].forEach(turno => {
        const info = resumoDia[turno];
        if (!info) return;

        const ocupacoesTurno = calendar.getEvents().filter(ev =>
            ev.extendedProps.data === dataStr && ev.extendedProps.turno === turno
        );

        const card = document.createElement('div');
        card.className = 'card mb-3';

        const header = document.createElement('div');
        header.className = 'card-header bg-light d-flex justify-content-between align-items-center';
        header.innerHTML = `
            <h6 class="mb-0">${escapeHTML(turno)}</h6>
            <span class="badge bg-secondary">${escapeHTML(info.ocupadas)} / ${escapeHTML(info.total_salas)} Salas</span>
        `;
        card.appendChild(header);

        const body = document.createElement('div');
        body.className = 'card-body';

        let htmlCorpo = '<div class="row">';

        htmlCorpo += '<div class="col-md-7">';
        htmlCorpo += '<h6><i class="bi bi-door-closed-fill text-danger"></i> Salas Ocupadas:</h6>';
        if (ocupacoesTurno.length) {
            htmlCorpo += '<ul class="list-group list-group-flush">';
            ocupacoesTurno.forEach(ev => {
                const props = ev.extendedProps;
                const instr = props.instrutor_nome ? `<br><small class="text-muted"><i class="bi bi-person"></i> ${escapeHTML(props.instrutor_nome)}</small>` : '';
                htmlCorpo += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${escapeHTML(props.sala_nome)}:</strong> ${escapeHTML(props.curso_evento)}
                            ${instr}
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary btn-editar-ocupacao" title="Editar" data-id="${ev.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger btn-excluir-ocupacao" title="Excluir" data-id="${ev.id}" data-nome="${escapeHTML(props.curso_evento)}" data-grupo-id="${props.grupo_ocupacao_id || ''}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </li>
                `;
            });
            htmlCorpo += '</ul>';
        } else {
            htmlCorpo += '<p class="fst-italic text-muted">Nenhuma sala ocupada neste turno.</p>';
        }
        htmlCorpo += '</div>';

        htmlCorpo += '<div class="col-md-5">';
        htmlCorpo += '<h6><i class="bi bi-door-open-fill text-success"></i> Salas Livres:</h6>';
        if (info.salas_livres.length) {
            info.salas_livres.forEach(salaNome => {
                htmlCorpo += `<span class="badge bg-light text-dark border me-1 mb-1">${escapeHTML(salaNome)}</span>`;
            });
        } else {
            htmlCorpo += '<p class="fst-italic text-muted">Todas as salas estão ocupadas.</p>';
        }
        htmlCorpo += '</div>';

        htmlCorpo += '</div>';

        body.innerHTML = sanitizeHTML(htmlCorpo);
        card.appendChild(body);
        container.appendChild(card);
    });

    container.querySelectorAll('.btn-editar-ocupacao').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const ocupacaoId = e.currentTarget.getAttribute('data-id');
            editarOcupacao(ocupacaoId);
        });
    });

    container.querySelectorAll('.btn-excluir-ocupacao').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const el = e.currentTarget;
            const ocupacaoId = el.getAttribute('data-id');
            const nome = el.getAttribute('data-nome');
            const grupoId = el.getAttribute('data-grupo-id');
            excluirOcupacao(ocupacaoId, nome, grupoId);
        });
    });

    modal.show();
}

async function carregarSalasParaFiltro() {
    try {
        const response = await fetch(`${API_URL}/salas?status=ativa`, {
            headers: {},
            credentials: 'include'
        });
        
        if (response.ok) {
            salasData = await response.json();
            
            const selects = getFiltroElements('Sala');
            popularSelectComOpcoes(
                selects,
                salasData.map(sala => ({ value: String(sala.id), label: sala.nome })),
                { value: '', label: 'Todas as salas' }
            );
        }
    } catch (error) {
        console.error('Erro ao carregar salas:', error);
    }
}

async function carregarInstrutoresParaFiltro() {
    try {
        const response = await fetch(`${API_URL}/instrutores?status=ativo`, {
            headers: {},
            credentials: 'include'
        });
        
        if (response.ok) {
            instrutoresData = await response.json();
            
            const selects = getFiltroElements('Instrutor');
            popularSelectComOpcoes(
                selects,
                instrutoresData.map(instrutor => ({ value: String(instrutor.id), label: instrutor.nome })),
                { value: '', label: 'Todos os instrutores' }
            );
        }
    } catch (error) {
        console.error('Erro ao carregar instrutores:', error);
    }
}

async function carregarTiposOcupacao() {
    try {
        const response = await fetch(`${API_URL}/ocupacoes/tipos`, {
            headers: {},
            credentials: 'include'
        });
        
        if (response.ok) {
            tiposOcupacao = await response.json();
        }
    } catch (error) {
        console.error('Erro ao carregar tipos de ocupação:', error);
    }
}

function aplicarFiltrosCalendario() {
    if (!calendar) return;

    calendar.refetchEvents();

    carregarResumoPeriodo(
        calendar.view.activeStart.toISOString().split('T')[0],
        calendar.view.activeEnd.toISOString().split('T')[0]
    );
}

function configurarFiltros() {
    const form = document.getElementById('filtrosForm');
    const formMobile = document.getElementById('filtrosMobileForm');

    if (form) {
        form.addEventListener('submit', e => {
            e.preventDefault();
            const salaValor = form.querySelector('#filtroSala')?.value ?? '';
            const instrutorValor = form.querySelector('#filtroInstrutor')?.value ?? '';
            const turnoValor = form.querySelector('#filtroTurno')?.value ?? '';

            setFiltroValue('Sala', salaValor);
            setFiltroValue('Instrutor', instrutorValor);
            setFiltroValue('Turno', turnoValor);

            aplicarFiltrosCalendario();
        });
    }

    if (formMobile) {
        formMobile.addEventListener('submit', e => {
            e.preventDefault();
            const salaValor = formMobile.querySelector('#filtroSalaMobile')?.value ?? '';
            const instrutorValor = formMobile.querySelector('#filtroInstrutorMobile')?.value ?? '';
            const turnoValor = formMobile.querySelector('#filtroTurnoMobile')?.value ?? '';

            setFiltroValue('Sala', salaValor);
            setFiltroValue('Instrutor', instrutorValor);
            setFiltroValue('Turno', turnoValor);

            aplicarFiltrosCalendario();
        });
    }
}

function aplicarFiltrosURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    const salaId = urlParams.get('sala_id');
    const instrutorId = urlParams.get('instrutor_id');
    const turnoParam = urlParams.get('turno');
    const mesParam = urlParams.get('mes');
    
    if (salaId) {
        setFiltroValue('Sala', salaId);
    }

    if (instrutorId) {
        setFiltroValue('Instrutor', instrutorId);
    }

    if (turnoParam) {
        setFiltroValue('Turno', turnoParam);
    }

    if (mesParam && calendar) {
        const dataMes = new Date(mesParam + '-01');
        calendar.gotoDate(dataMes);
    }

    if (salaId || instrutorId || turnoParam) {
        setTimeout(() => aplicarFiltrosCalendario(), 1000);
    }
}

function mostrarDetalhesOcupacao(ocupacao) {
    const modal = new bootstrap.Modal(document.getElementById('modalDetalhesOcupacao'));
    
    const content = document.getElementById('detalhesOcupacaoContent');
    const acoes = document.getElementById('acoesOcupacao');
    
    const tipoNome = tiposOcupacao.find(t => t.valor === ocupacao.tipo_ocupacao)?.nome || ocupacao.tipo_ocupacao;
    const salaNome = salasData.find(s => s.id === ocupacao.sala_id)?.nome || 'Sala não encontrada';
    const instrutorNome = ocupacao.instrutor_id ? 
        (instrutoresData.find(i => i.id === ocupacao.instrutor_id)?.nome || 'Instrutor não encontrado') : 
        'Nenhum instrutor';
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Curso/Evento</h6>
                <p class="mb-3">${ocupacao.curso_evento}</p>
                
                <h6>Tipo</h6>
                <p class="mb-3">
                    <span class="badge" style="background-color: ${getTipoCorPorValor(ocupacao.tipo_ocupacao)};">
                        ${tipoNome}
                    </span>
                </p>
                
                <h6>Status</h6>
                <p class="mb-3">
                    <span class="badge ${getStatusBadgeClass(ocupacao.status)}">
                        ${getStatusNome(ocupacao.status)}
                    </span>
                </p>
            </div>
            <div class="col-md-6">
                <h6>Data e Horário</h6>
                <p class="mb-3">
                    <i class="bi bi-calendar me-1"></i>
                    ${formatarData(ocupacao.data)}<br>
                    <i class="bi bi-clock me-1"></i>
                    ${ocupacao.horario_inicio} às ${ocupacao.horario_fim}
                </p>
                
                <h6>Sala</h6>
                <p class="mb-3">
                    <i class="bi bi-building me-1"></i>
                    ${salaNome}
                </p>
                
                <h6>Instrutor</h6>
                <p class="mb-3">
                    <i class="bi bi-person-badge me-1"></i>
                    ${instrutorNome}
                </p>
            </div>
        </div>
        
        ${ocupacao.observacoes ? `
            <div class="row">
                <div class="col-12">
                    <h6>Observações</h6>
                    <p class="mb-0">${ocupacao.observacoes}</p>
                </div>
            </div>
        ` : ''}
    `;
    
    const usuario = getUsuarioLogado();
    const podeEditar = isAdmin() || ocupacao.usuario_id === usuario.id;
    
    acoes.innerHTML = '';
    
    if (podeEditar) {
        const btnEditar = document.createElement('button');
        btnEditar.type = 'button';
        btnEditar.className = 'btn btn-primary me-2';
        btnEditar.innerHTML = '<i class="bi bi-pencil me-1"></i>Editar';
        btnEditar.addEventListener('click', () => editarOcupacao(ocupacao.id));

        const btnExcluir = document.createElement('button');
        btnExcluir.type = 'button';
        btnExcluir.className = 'btn btn-danger';
        btnExcluir.innerHTML = '<i class="bi bi-trash me-1"></i>Excluir';
        btnExcluir.addEventListener('click', () => excluirOcupacao(ocupacao.id, ocupacao.curso_evento, ocupacao.grupo_ocupacao_id || ''));

        acoes.appendChild(btnEditar);
        acoes.appendChild(btnExcluir);
    }
    
    modal.show();
}

function getTipoCorPorValor(valor) {
    const tipo = tiposOcupacao.find(t => t.valor === valor);
    return tipo ? tipo.cor : rootStyle.getPropertyValue('--muted-color').trim();
}

function getStatusBadgeClass(status) {
    const classes = {
        'confirmado': 'bg-success',
        'pendente': 'bg-warning',
        'cancelado': 'bg-danger'
    };
    return classes[status] || 'bg-secondary';
}

function getStatusNome(status) {
    const nomes = {
        'confirmado': 'Confirmado',
        'pendente': 'Pendente',
        'cancelado': 'Cancelado'
    };
    return nomes[status] || status;
}

function formatarData(dataStr) {
    const data = new Date(dataStr + 'T00:00:00');
    return data.toLocaleDateString('pt-BR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function editarOcupacao(id) {
    
    const detalhesEl = document.getElementById('modalDetalhesOcupacao');
    const detalhesModal = detalhesEl ? bootstrap.Modal.getInstance(detalhesEl) : null;
    if (detalhesModal) detalhesModal.hide();

    const resumoEl = document.getElementById('modalResumoDia');
    const resumoModal = resumoEl ? bootstrap.Modal.getInstance(resumoEl) : null;
    if (resumoModal) resumoModal.hide();

    window.location.href = `/ocupacao/agendamento.html?editar=${id}`;
}

function excluirOcupacaoResumo(id) {
    const evento = calendar.getEventById(id);
    if (!evento) return;
    const props = evento.extendedProps;
    excluirOcupacao(id, props.curso_evento, props.grupo_ocupacao_id || '');
}

function excluirOcupacao(id, nome, grupoId) {
    
    const detalhesEl = document.getElementById('modalDetalhesOcupacao');
    const detalhesModal = detalhesEl ? bootstrap.Modal.getInstance(detalhesEl) : null;
    if (detalhesModal) detalhesModal.hide();

    const resumoEl = document.getElementById('modalResumoDia');
    const resumoModal = resumoEl ? bootstrap.Modal.getInstance(resumoEl) : null;
    if (resumoModal) resumoModal.hide();

    document.getElementById('resumoOcupacaoExcluir').textContent = nome;
    const modalEl = document.getElementById('modalExcluirOcupacao');
    modalEl.setAttribute('data-ocupacao-id', id);
    modalEl.setAttribute('data-grupo-id', grupoId);
    
    const modalExcluir = new bootstrap.Modal(document.getElementById('modalExcluirOcupacao'));
    modalExcluir.show();
}

async function confirmarExclusaoOcupacao(modo) {
    try {
        const modalEl = document.getElementById('modalExcluirOcupacao');
        const ocupacaoId = modalEl.getAttribute('data-ocupacao-id');
        const grupoId = modalEl.getAttribute('data-grupo-id');
        const somenteDia = modo === 'dia';

        const url = somenteDia ?
            `${API_URL}/ocupacoes/${ocupacaoId}?somente_dia=true` :
            `${API_URL}/ocupacoes/${ocupacaoId}`;

        const response = await fetch(url, {
            method: 'DELETE',
            headers: {},
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Ocupação excluída com sucesso!', 'success');

            const modal = bootstrap.Modal.getInstance(document.getElementById('modalExcluirOcupacao'));
            modal.hide();

            const ev = calendar.getEventById(ocupacaoId);
            if (ev) ev.remove();
            calendar.refetchEvents();
            await carregarResumoPeriodo(
                calendar.view.activeStart.toISOString().split('T')[0],
                calendar.view.activeEnd.toISOString().split('T')[0]
            );
            if (diaResumoAtual) {
                mostrarResumoDia(diaResumoAtual);
            }
        } else {
            throw new Error(result.erro || 'Erro ao excluir ocupação');
        }
    } catch (error) {
        console.error('Erro ao excluir ocupação:', error);
        showToast(`Não foi possível excluir a ocupação: ${error.message}`, 'danger');
    }
}

function formatarDataCurta(dataStr) {
    const data = new Date(dataStr + 'T00:00:00');
    return data.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit'
    });
}

