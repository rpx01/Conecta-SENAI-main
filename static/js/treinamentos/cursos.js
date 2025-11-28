// src/static/js/treinamentos.js

// Armazena os dados do usuário logado e suas inscrições
let dadosUsuarioLogado = null;
let minhasInscricoesIds = new Set();
let contadoresIntervals = [];
let cacheMeusCursos = []; // Cache para os dados dos cursos do usuário

/**
 * Aplica a máscara de CPF (nnn.nnn.nnn-nn) a um campo de input.
 * @param {HTMLInputElement} input - O elemento do campo de CPF.
 */
function mascaraCpf(input) {
    let value = input.value.replace(/\D/g, '');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    input.value = value;
}

/**
 * Valida um CPF e atualiza a classe do input para feedback visual.
 * @param {HTMLInputElement} input - O elemento do campo de CPF.
 */
function validarCPF(input) {
    let cpf = input.value.replace(/\D/g, '');
    if (cpf.length !== 11 || /^(\d)\1+$/.test(cpf)) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        return;
    }
    let soma = 0, resto;
    for (let i = 1; i <= 9; i++) soma += parseInt(cpf.substring(i - 1, i)) * (11 - i);
    resto = (soma * 10) % 11;
    if (resto == 10 || resto == 11) resto = 0;
    if (resto != parseInt(cpf.substring(9, 10))) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        return;
    }
    soma = 0;
    for (let i = 1; i <= 10; i++) soma += parseInt(cpf.substring(i - 1, i)) * (12 - i);
    resto = (soma * 10) % 11;
    if (resto == 10 || resto == 11) resto = 0;
    if (resto != parseInt(cpf.substring(10, 11))) {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
        return;
    }
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
}

/**
 * Listener que é executado quando o conteúdo da página termina de carregar.
 */
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('cursos-disponiveis-cards-container')) {
        carregarTreinamentos();
    }
    if (document.getElementById('cursos-em-andamento')) {
        carregarMeusCursos();
    }

    // Listener para o botão de submissão do formulário de inscrição
    const btnEnviar = document.getElementById('btnEnviarInscricao');
    if (btnEnviar) {
        btnEnviar.addEventListener('click', () => {
            const isExterno = document.getElementById('inscreverOutroCheck').checked;
            if (isExterno) {
                enviarInscricaoExterna();
            } else {
                enviarInscricaoPropria();
            }
        });
    }

    // Listener para o checkbox de "inscrever outro"
    const checkInscreverOutro = document.getElementById('inscreverOutroCheck');
    if (checkInscreverOutro) {
        checkInscreverOutro.addEventListener('change', (e) => {
            toggleFormularioExterno(e.target.checked);
        });
    }

    // Listener para o botão de inscrição própria no modal de seleção
    const btnParaMim = document.getElementById('btnInscreverParaMim');
    if (btnParaMim) {
        btnParaMim.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();

            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;
            document.getElementById('inscreverOutroCheck').checked = false;
            toggleFormularioExterno(false); 

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }

    // Listener para o botão de inscrição de terceiros no modal de seleção
    const btnParaOutro = document.getElementById('btnInscreverParaOutro');
    if (btnParaOutro) {
        btnParaOutro.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();
            
            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;
            document.getElementById('inscreverOutroCheck').checked = true;
            toggleFormularioExterno(true);

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }

    // Listener para campo de CPF
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', () => {
            mascaraCpf(cpfInput);
            if (cpfInput.value.length === 14) {
                validarCPF(cpfInput);
            } else {
                cpfInput.classList.remove('is-valid', 'is-invalid');
            }
        });
    }
});

/**
 * Calcula a data limite para inscrições, considerando um dia útil
 * anterior à data de início do treinamento.
 * @param {string} dataInicioStr - Data de início em formato ISO (YYYY-MM-DD).
 * @returns {string} Data de encerramento das inscrições em formato ISO.
 */
function calcularDataLimiteInscricao(dataInicioStr) {
    const data = new Date(dataInicioStr);
    if (isNaN(data)) return dataInicioStr;

    data.setDate(data.getDate() - 1);
    while (data.getDay() === 0 || data.getDay() === 6) {
        data.setDate(data.getDate() - 1);
    }

    return data.toISOString().split('T')[0];
}

function buildBadges(turma) {
    const teoriaOnline = turma.teoria_online === true || turma.treinamento?.teoria_online === true;
    const teoriaLabel = `Teoria: ${teoriaOnline ? 'Online' : 'Presencial'}`;
    const teoriaClasses = ['badge', 'badge-teoria', teoriaOnline ? 'badge-teoria-online' : 'badge-teoria-presencial'].join(' ');
    const teoriaBadge = `<span class="${teoriaClasses}">${teoriaLabel}</span>`;

    const hasPratica = turma.treinamento?.tem_pratica === true || turma.has_pratica === true;
    if (!hasPratica) {
        return teoriaBadge;
    }

    const praticaOnline = turma.pratica_online === true || turma.treinamento?.pratica_online === true;
    const praticaLabel = `Prática: ${praticaOnline ? 'Online' : 'Presencial'}`;
    const praticaClasses = ['badge', 'badge-pratica', praticaOnline ? 'badge-pratica-online' : 'badge-pratica-presencial'].join(' ');
    const praticaBadge = `<span class="${praticaClasses}">${praticaLabel}</span>`;

    return teoriaBadge + praticaBadge;
}

/**
 * Carrega a lista de turmas disponíveis, verificando se o usuário já está inscrito.
 */
async function carregarTreinamentos() {
    const container = document.getElementById('cursos-disponiveis-cards-container');
    if (!container) return;

    container.innerHTML = `<div class="text-center w-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>`;

    try {
        const [minhasInscricoes, turmas] = await Promise.all([
            chamarAPI('/treinamentos/minhas'),
            chamarAPI('/treinamentos/agendadas')
        ]);

        minhasInscricoesIds = new Set(minhasInscricoes.map(i => i.turma_id));
        container.innerHTML = '';

        if (turmas.length === 0) {
            container.innerHTML = '<p class="text-center w-100">Nenhum curso disponível no momento.</p>';
            return;
        }

        turmas.forEach(t => {
            const isInscrito = minhasInscricoesIds.has(t.turma_id);
            const botaoHtml = `<button class="btn ${isInscrito ? 'btn-success' : 'btn-primary'}" onclick="abrirModalInscricao(${t.turma_id})">${isInscrito ? '<i class="bi bi-check-circle-fill"></i> INSCRITO' : 'INSCREVER-SE'}</button>`;
            const dataEncerramento = calcularDataLimiteInscricao(t.data_inicio);

            const cardHtml = `
            <div class="col">
                <div class="card h-100 curso-card-disponivel">
                    <div class="card-body">
                        <h5 class="card-title d-flex justify-content-between align-items-start">
                            ${escapeHTML(t.treinamento.nome)}
                            <div class="badges">${buildBadges(t)}</div>
                        </h5>
                        <hr>
                        <div class="curso-info-item">
                            <i class="bi bi-calendar-range"></i>
                            <span><b>Período:</b> ${formatarData(t.data_inicio)} a ${formatarData(t.data_fim)}</span>
                        </div>
                         <div class="curso-info-item">
                            <i class="bi bi-clock-fill"></i>
                            <span><b>Horário:</b> ${escapeHTML(t.horario || 'A definir')}</span>
                        </div>               
                        <div class="curso-info-item">
                            <i class="bi bi-person-workspace"></i>
                            <span><b>Instrutor:</b> ${escapeHTML(t.instrutor_nome || 'A definir')}</span>
                        </div>
                        <div class="curso-info-item">
                            <i class="bi bi-hourglass-split"></i>
                            <span><b>Carga Horária:</b> ${t.treinamento.carga_horaria ? `${t.treinamento.carga_horaria} horas` : 'N/D'}</span>
                        </div>
                        <div class="curso-info-item">
                            <i class="bi bi-geo-alt-fill"></i>
                            <span><b>Local:</b> ${escapeHTML(t.local_realizacao || 'A definir')}</span>
                        </div>
                    </div>
                    <div class="card-footer bg-light">
                        <div class="d-flex justify-content-between align-items-center">
                            ${botaoHtml}
                            <div class="text-end">
                                <small class="text-muted d-block">Inscrições encerram em:</small>
                                <span class="countdown-timer" id="countdown-${t.turma_id}" data-fim="${dataEncerramento}"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
            container.insertAdjacentHTML('beforeend', cardHtml);
        });

        iniciarContadores();

    } catch (e) {
        showToast(e.message, 'danger');
        container.innerHTML = '<p class="text-center text-danger w-100">Falha ao carregar os cursos.</p>';
    }
}

function iniciarContadores() {
    contadoresIntervals.forEach(clearInterval);
    contadoresIntervals = [];

    document.querySelectorAll('.countdown-timer').forEach(timerEl => {
        const fim = timerEl.dataset.fim;
        if (!fim) {
            timerEl.textContent = 'Data inválida';
            return;
        }
        let dataFim = new Date(fim);
        if (isNaN(dataFim.getTime())) {
            timerEl.textContent = 'Data inválida';
            return;
        }
        dataFim.setHours(23, 59, 59, 999);

        const intervalId = setInterval(() => {
            const agora = new Date();
            const diferenca = dataFim - agora;

            if (diferenca <= 0) {
                clearInterval(intervalId);
                timerEl.textContent = 'Inscrições encerradas';
                const cardFooter = timerEl.closest('.card-footer');
                if (cardFooter) {
                    const btn = cardFooter.querySelector('.btn');
                    if (btn && !btn.textContent.includes('INSCRITO')) {
                        btn.disabled = true;
                        btn.innerHTML = 'ENCERRADO';
                    }
                }
                return;
            }

            const dias = Math.floor(diferenca / (1000 * 60 * 60 * 24));
            const horas = Math.floor((diferenca % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

            timerEl.textContent = `${dias}d e ${horas}h`;
        }, 1000);
        contadoresIntervals.push(intervalId);
    });
}

/**
 * Carrega e distribui os cursos do usuário por status.
 */
async function carregarMeusCursos() {
    const containers = {
        andamento: document.getElementById('cursos-em-andamento'),
        breve: document.getElementById('cursos-em-breve'),
        concluidos: document.getElementById('cursos-concluidos')
    };

    if (!containers.andamento) return;

    Object.values(containers).forEach(c => c.innerHTML = `<div class="text-center w-100"><div class="spinner-border text-primary" role="status"></div></div>`);

    try {
        const cursos = await chamarAPI('/treinamentos/minhas');
        cacheMeusCursos = cursos; 

        Object.values(containers).forEach(c => c.innerHTML = '');

        const hoje = new Date();
        hoje.setHours(0, 0, 0, 0);

        const grupos = {
            andamento: [],
            breve: [],
            concluidos: []
        };

        cursos.forEach(c => {
            const dataInicio = new Date(c.data_inicio);
            const dataFim = new Date(c.data_fim);
            dataFim.setHours(23, 59, 59, 999);

            if (hoje > dataFim) {
                grupos.concluidos.push(c);
            } else if (hoje >= dataInicio) {
                grupos.andamento.push(c);
            } else {
                grupos.breve.push(c);
            }
        });

        renderizarGrupoCursos(grupos.andamento, containers.andamento, 'em-andamento', 'Em Andamento');
        renderizarGrupoCursos(grupos.breve, containers.breve, 'futuro', 'Em Breve');
        renderizarGrupoCursos(grupos.concluidos, containers.concluidos, 'concluido', 'Concluído');

    } catch (e) {
        showToast(e.message, 'danger');
        Object.values(containers).forEach(c => c.innerHTML = '<p class="text-center text-danger">Falha ao carregar seus cursos.</p>');
    }
}

/**
 * Renderiza um grupo de cursos em seu respectivo container.
 */
function renderizarGrupoCursos(cursos, container, statusClass, statusText) {
    if (cursos.length === 0) {
        container.innerHTML = `<div class="col-12"><p class="text-center text-muted">Nenhum curso nesta categoria.</p></div>`;
        return;
    }
    
    cursos.forEach(c => {
        const hoje = new Date();
        const dataInicio = new Date(c.data_inicio);
        const dataFim = new Date(c.data_fim);
        let progresso = 0;

        if (statusClass === 'concluido') {
            progresso = 100;
        } else if (statusClass === 'em-andamento') {
            const totalDias = (dataFim - dataInicio) / (1000 * 3600 * 24) || 1;
            const diasPassados = (hoje - dataInicio) / (1000 * 3600 * 24);
            progresso = Math.min(100, Math.round((diasPassados / totalDias) * 100));
        }

        const cardHtml = `
            <div class="col-md-6 mb-4">
                <div class="card curso-card status-${statusClass}" onclick="abrirModalDetalhes(${c.turma_id})">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">${escapeHTML(c.treinamento.nome)}</h5>
                            <span class="selo-status status-${statusClass}">${statusText}</span>
                        </div>
                        <span class="badge bg-secondary mt-2">Teoria: ${c.teoria_online ? 'Online' : 'Presencial'}</span>
                        <p class="card-text mt-2"><small class="text-muted">De ${formatarData(c.data_inicio)} a ${formatarData(c.data_fim)}</small></p>
                        <div class="progress mt-3" style="height: 10px;"><div class="progress-bar" role="progressbar" style="width: ${progresso}%;"></div></div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', cardHtml);
    });
}

/**
 * Abre o modal com os detalhes completos do curso.
 */
function abrirModalDetalhes(turmaId) {
    const curso = cacheMeusCursos.find(c => c.turma_id === turmaId);
    if (!curso) return;

    document.getElementById('modalNomeTreinamento').textContent = curso.treinamento.nome;
    document.getElementById('modalPeriodo').textContent = `${formatarData(curso.data_inicio)} a ${formatarData(curso.data_fim)}`;
    document.getElementById('modalHorario').textContent = curso.horario || 'Não definido';
    document.getElementById('modalInstrutor').textContent = curso.instrutor_nome || 'A definir';
    document.getElementById('modalLocal').textContent = curso.local_realizacao || 'A definir';
    document.getElementById('modalConteudo').textContent = curso.treinamento.conteudo_programatico || 'Nenhum conteúdo programático informado.';

    const linksContainer = document.getElementById('modalLinks');
    linksContainer.innerHTML = '';
    if (curso.treinamento.links_materiais && curso.treinamento.links_materiais.length > 0) {
        curso.treinamento.links_materiais.forEach(link => {
            const li = `<li class="list-group-item"><a href="${escapeHTML(link)}" target="_blank"><i class="bi bi-link-45deg"></i> Material de Apoio</a></li>`;
            linksContainer.insertAdjacentHTML('beforeend', li);
        });
    } else {
        linksContainer.innerHTML = '<li class="list-group-item">Nenhum material disponível.</li>';
    }

    const modal = new bootstrap.Modal(document.getElementById('cursoDetalhesModal'));
    modal.show();
}


/**
 * Abre o modal de seleção de tipo de inscrição.
 */
async function abrirModalInscricao(turmaId) {
    const btnParaMim = document.getElementById('btnInscreverParaMim');
    if (btnParaMim) {
        btnParaMim.disabled = minhasInscricoesIds.has(turmaId);
    }

    const selecaoModalEl = document.getElementById('selecaoInscricaoModal');
    selecaoModalEl.dataset.turmaId = turmaId;
    const modal = new bootstrap.Modal(selecaoModalEl);
    modal.show();
}

/**
 * Alterna a visibilidade e o estado do formulário de inscrição.
 */
function toggleFormularioExterno(isExterno) {
    const form = document.getElementById('inscricaoForm');
    const inputs = form.querySelectorAll('input:not([type=hidden]):not([type=checkbox])');

    inputs.forEach(input => {
        input.value = '';
        input.readOnly = isExterno ? false : true;
    });

    document.getElementById('inscreverOutroCheck').checked = isExterno;

    if (isExterno) {
        document.getElementById('dataNascimento').type = 'date';
        // Habilita a edição de todos os campos para inscrição de terceiros
        inputs.forEach(input => input.readOnly = false);
        document.getElementById('nome').focus();
    } else {
        if (!dadosUsuarioLogado) {
            dadosUsuarioLogado = getUsuarioLogado();
        }

        if (dadosUsuarioLogado) {
            // Preenche todos os campos com os dados do usuário logado
            document.getElementById('nome').value = dadosUsuarioLogado.nome || '';
            document.getElementById('email').value = dadosUsuarioLogado.email || '';
            document.getElementById('cpf').value = dadosUsuarioLogado.cpf || '';
            document.getElementById('dataNascimento').value = dadosUsuarioLogado.data_nascimento || '';
            document.getElementById('empresa').value = dadosUsuarioLogado.empresa || '';

            // Mantém os campos principais como somente leitura
            document.getElementById('nome').readOnly = true;
            document.getElementById('email').readOnly = true;

            // Permite a edição dos campos complementares caso não estejam preenchidos
            document.getElementById('cpf').readOnly = !!dadosUsuarioLogado.cpf;
            document.getElementById('dataNascimento').readOnly = !!dadosUsuarioLogado.data_nascimento;
            document.getElementById('empresa').readOnly = !!dadosUsuarioLogado.empresa;
        }
        document.getElementById('dataNascimento').type = 'date';
        // Foco no primeiro campo editável, se houver
        if (!dadosUsuarioLogado.cpf) {
             document.getElementById('cpf').focus();
        } else if (!dadosUsuarioLogado.data_nascimento) {
             document.getElementById('dataNascimento').focus();
        }
    }
}

/**
 * Envia a requisição para inscrever o próprio usuário.
 */
async function enviarInscricaoPropria() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('dataNascimento').value || null,
        empresa: document.getElementById('empresa').value || null,
    };

    if (!body.nome || !body.email || !body.cpf) {
        showToast('Nome, Email e CPF são obrigatórios.', 'warning');
        return;
    }

    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST', body);
        showToast('Inscrição realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
        
        await carregarTreinamentos();
        if (document.getElementById('listaMeusCursos')) {
            carregarMeusCursos();
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

/**
 * Envia a requisição para inscrever um participante externo.
 */
async function enviarInscricaoExterna() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('dataNascimento').value || null,
        empresa: document.getElementById('empresa').value || null,
    };

    if (!body.nome || !body.email || !body.cpf) {
        showToast('Nome, Email e CPF são obrigatórios.', 'warning');
        return;
    }

    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes/externo`, 'POST', body);
        showToast('Inscrição para o participante externo realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
    } catch (e) {
        showToast(e.message, 'danger');
    }
}
