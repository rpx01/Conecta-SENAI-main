// Funções para o dashboard de salas

// Variáveis globais
let estatisticasGerais = {};
let proximasOcupacoes = [];
let relatorioMensal = {};
let salasAtivasCache = null;
let salasAtivasPromise = null;

const rootStyle = getComputedStyle(document.documentElement);
const coresOcorrencia = {
    'aula_regular': rootStyle.getPropertyValue('--success-color').trim(),
    'evento_especial': rootStyle.getPropertyValue('--warning-color').trim(),
    'reuniao': rootStyle.getPropertyValue('--info-color').trim(),
    'manutencao': rootStyle.getPropertyValue('--danger-color').trim(),
    'reserva_especial': '#9C27B0'
};

async function obterSalasAtivas() {
    if (salasAtivasCache) {
        return salasAtivasCache;
    }

    if (!salasAtivasPromise) {
        salasAtivasPromise = (async () => {
            const response = await fetch(`${API_URL}/salas?status=ativa`, {
            });

            if (!response.ok) {
                throw new Error('Falha ao carregar salas ativas');
            }

            const salas = await response.json();
            salasAtivasCache = salas;
            return salas;
        })().catch(error => {
            salasAtivasPromise = null;
            throw error;
        });
    }

    return salasAtivasPromise;
}

// Carrega indicadores de salas por mês
function setTextContentIfExists(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function setHrefIfExists(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.href = value;
    }
}

async function carregarIndicadoresMensais() {
    try {
        const salas = await obterSalasAtivas();
        const totalSalas = salas.length;

        async function obterDados(mesOffset) {
            const ref = new Date();
            ref.setMonth(ref.getMonth() + mesOffset, 1);
            const inicio = new Date(ref.getFullYear(), ref.getMonth(), 1);
            const fim = new Date(ref.getFullYear(), ref.getMonth() + 1, 0);
            const iniStr = inicio.toISOString().split('T')[0];
            const fimStr = fim.toISOString().split('T')[0];
            const resp = await fetch(`${API_URL}/ocupacoes?data_inicio=${iniStr}&data_fim=${fimStr}&status=confirmado`, {
            });
            const ocup = resp.ok ? await resp.json() : [];
            const salasOcupadas = new Set(ocup.map(o => o.sala_id)).size;
            return { iniStr, totalSalas, salasOcupadas };
        }

        const anterior = await obterDados(-1);
        const atual = await obterDados(0);
        const seguinte = await obterDados(1);

        function preencher(prefixo, dados, linkEl) {
            setTextContentIfExists(`totalSalasMes${prefixo}`, dados.totalSalas);
            setTextContentIfExists(`salasOcupadasMes${prefixo}`, dados.salasOcupadas);
            setTextContentIfExists(`salasLivresMes${prefixo}`, dados.totalSalas - dados.salasOcupadas);
            setHrefIfExists(linkEl, `/ocupacao/calendario.html?mes=${dados.iniStr.substring(0,7)}`);
        }

        preencher('Anterior', anterior, 'linkMesAnterior');
        preencher('Atual', atual, 'linkMesAtual');
        preencher('Seguinte', seguinte, 'linkMesSeguinte');
    } catch (error) {
        console.error('Erro ao carregar indicadores mensais:', error);
        showToast('Não conseguimos carregar os indicadores. Tente novamente mais tarde.', 'danger');
    }
}

// Carrega estatísticas gerais
async function carregarEstatisticasGerais() {
    try {
        // Carrega total de salas ativas
        try {
            const salas = await obterSalasAtivas();
            document.getElementById('totalSalasAtivas').textContent = salas.length;
        } catch (error) {
            console.error('Erro ao carregar salas ativas:', error);
        }
        
        // Carrega total de instrutores ativos
        const responseInstrutores = await fetch(`${API_URL}/instrutores?status=ativo`, {
            headers: {
            }
        });
        
        if (responseInstrutores.ok) {
            const instrutores = await responseInstrutores.json();
            document.getElementById('totalInstrutoresAtivos').textContent = instrutores.length;
        }
        
        // Carrega ocupações de hoje
        const hoje = new Date().toISOString().split('T')[0];
        const responseHoje = await fetch(`${API_URL}/ocupacoes?data_inicio=${hoje}&data_fim=${hoje}&status=confirmado`, {
            headers: {
            }
        });
        
        if (responseHoje.ok) {
            const ocupacoesHoje = await responseHoje.json();
            document.getElementById('ocupacoesHoje').textContent = ocupacoesHoje.length;
        }
        
        // Carrega ocupações desta semana
        const inicioSemana = getInicioSemana();
        const fimSemana = getFimSemana();
        const responseSemana = await fetch(`${API_URL}/ocupacoes?data_inicio=${inicioSemana}&data_fim=${fimSemana}&status=confirmado`, {
            headers: {
            }
        });
        
        if (responseSemana.ok) {
            const ocupacoesSemana = await responseSemana.json();
            document.getElementById('ocupacoesSemana').textContent = ocupacoesSemana.length;
        }
        
    } catch (error) {
        console.error('Erro ao carregar estatísticas gerais:', error);
        showToast('Não conseguimos carregar as estatísticas. Tente novamente.', 'danger');
    }
}

// Carrega próximas ocupações
async function carregarProximasOcupacoes() {
    try {
        const hoje = new Date().toISOString().split('T')[0];
        const proximaSemana = new Date();
        proximaSemana.setDate(proximaSemana.getDate() + 7);
        const fimPeriodo = proximaSemana.toISOString().split('T')[0];
        
        const response = await fetch(`${API_URL}/ocupacoes?data_inicio=${hoje}&data_fim=${fimPeriodo}&status=confirmado`, {
            headers: {
            }
        });
        
        if (response.ok) {
            proximasOcupacoes = await response.json();
            
            // Ordena por data e horário
            proximasOcupacoes.sort((a, b) => {
                const dataA = new Date(`${a.data}T${a.horario_inicio}`);
                const dataB = new Date(`${b.data}T${b.horario_inicio}`);
                return dataA - dataB;
            });
            
            renderizarProximasOcupacoes();
        }
    } catch (error) {
        console.error('Erro ao carregar próximas ocupações:', error);
        showToast('Não conseguimos carregar as próximas ocupações. Tente novamente.', 'danger');
    } finally {
        document.getElementById('loadingProximasOcupacoes').style.display = 'none';
    }
}

// Renderiza próximas ocupações
function renderizarProximasOcupacoes() {
    const container = document.getElementById('proximasOcupacoes');
    
    if (proximasOcupacoes.length === 0) {
        document.getElementById('nenhumaProximaOcupacao').style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    
    // Mostra apenas as próximas 5 ocupações
    const ocupacoesLimitadas = proximasOcupacoes.slice(0, 5);
    
    ocupacoesLimitadas.forEach(ocupacao => {
        const item = document.createElement('div');
        item.className = `ocupacao-item ${ocupacao.tipo_ocupacao}`;

        const dataFormatada = formatarDataCurta(ocupacao.data);
        const isHoje = ocupacao.data === new Date().toISOString().split('T')[0];

        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${escapeHTML(ocupacao.curso_evento)}</h6>
                    <small class="text-muted">
                        <i class="bi bi-building me-1"></i>${escapeHTML(ocupacao.sala_nome || 'Sala não informada')}
                    </small>
                    ${ocupacao.instrutor_nome ? `
                        <br><small class="text-muted">
                            <i class="bi bi-person-badge me-1"></i>${escapeHTML(ocupacao.instrutor_nome)}
                        </small>
                    ` : ''}
                </div>
                <div class="text-end">
                    <small class="fw-bold ${isHoje ? 'text-primary' : ''}">
                        ${isHoje ? 'HOJE' : escapeHTML(dataFormatada)}
                    </small>
                    <br>
                    <small class="text-muted">
                        ${escapeHTML(ocupacao.horario_inicio)} - ${escapeHTML(ocupacao.horario_fim)}
                    </small>
                </div>
            </div>
        `;

        container.appendChild(item);
    });
    
    document.getElementById('proximasOcupacoes').style.display = 'block';
}

// Carrega relatório mensal
async function carregarRelatorioMensal() {
    try {
        // Calcula primeiro e último dia do mês atual
        const hoje = new Date();
        const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);
        const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0);
        
        const dataInicio = primeiroDia.toISOString().split('T')[0];
        const dataFim = ultimoDia.toISOString().split('T')[0];
        
        // Verifica se é admin para acessar relatório
        if (isAdmin()) {
            const response = await fetch(`${API_URL}/ocupacoes/relatorio?data_inicio=${dataInicio}&data_fim=${dataFim}`, {
                headers: {
                }
            });
            
            if (response.ok) {
                relatorioMensal = await response.json();
                renderizarSalasMaisUtilizadas();
                renderizarOcupacoesPorTipo();
            }
        } else {
            // Para usuários não-admin, carrega dados básicos
            await carregarDadosBasicos(dataInicio, dataFim);
        }
    } catch (error) {
        console.error('Erro ao carregar relatório mensal:', error);
        showToast('Não conseguimos carregar o relatório mensal. Tente novamente.', 'danger');
    } finally {
        document.getElementById('loadingSalasMaisUtilizadas').style.display = 'none';
        document.getElementById('loadingOcupacoesPorTipo').style.display = 'none';
    }
}

// Carrega dados básicos para usuários não-admin
async function carregarDadosBasicos(dataInicio, dataFim) {
    try {
        // Carrega ocupações do usuário no período
        const response = await fetch(`${API_URL}/ocupacoes?data_inicio=${dataInicio}&data_fim=${dataFim}`, {
            headers: {
            }
        });
        
        if (response.ok) {
            const ocupacoes = await response.json();
            
            // Processa dados para exibição
            const salasMaisUtilizadas = processarSalasMaisUtilizadas(ocupacoes);
            const ocupacoesPorTipo = processarOcupacoesPorTipo(ocupacoes);
            
            renderizarSalasMaisUtilizadasBasico(salasMaisUtilizadas);
            renderizarOcupacoesPorTipoBasico(ocupacoesPorTipo);
        }
    } catch (error) {
        console.error('Erro ao carregar dados básicos:', error);
        showToast('Não conseguimos carregar os dados solicitados.', 'danger');
    }
}

// Processa salas mais utilizadas para usuários não-admin
function processarSalasMaisUtilizadas(ocupacoes) {
    const contadorSalas = {};
    
    ocupacoes.forEach(ocupacao => {
        const salaNome = ocupacao.sala_nome || 'Sala não informada';
        contadorSalas[salaNome] = (contadorSalas[salaNome] || 0) + 1;
    });
    
    return Object.entries(contadorSalas)
        .map(([sala, total]) => ({ sala, total_ocupacoes: total }))
        .sort((a, b) => b.total_ocupacoes - a.total_ocupacoes)
        .slice(0, 5);
}

// Processa ocupações por tipo para usuários não-admin
function processarOcupacoesPorTipo(ocupacoes) {
    const contadorTipos = {};
    
    ocupacoes.forEach(ocupacao => {
        const tipo = ocupacao.tipo_ocupacao || 'Não especificado';
        contadorTipos[tipo] = (contadorTipos[tipo] || 0) + 1;
    });
    
    return Object.entries(contadorTipos)
        .map(([tipo, total]) => ({ tipo, total }));
}

// Renderiza salas mais utilizadas
function renderizarSalasMaisUtilizadas() {
    const container = document.getElementById('salasMaisUtilizadas');
    
    if (!relatorioMensal.salas_mais_utilizadas || relatorioMensal.salas_mais_utilizadas.length === 0) {
        document.getElementById('nenhumaSalaMaisUtilizada').style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    
    relatorioMensal.salas_mais_utilizadas.forEach((item, index) => {
        const porcentagem = Math.round((item.total_ocupacoes / relatorioMensal.salas_mais_utilizadas[0].total_ocupacoes) * 100);
        
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-medium">${item.sala}</span>
                <span class="badge bg-primary">${item.total_ocupacoes}</span>
            </div>
            <div class="progress" style="height: 8px;">
                <div class="progress-bar" role="progressbar" style="width: ${porcentagem}%" aria-valuenow="${porcentagem}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        container.appendChild(div);
    });
    
    document.getElementById('salasMaisUtilizadas').style.display = 'block';
}

// Renderiza salas mais utilizadas (versão básica)
function renderizarSalasMaisUtilizadasBasico(salas) {
    const container = document.getElementById('salasMaisUtilizadas');
    
    if (salas.length === 0) {
        document.getElementById('nenhumaSalaMaisUtilizada').style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    
    salas.forEach((item, index) => {
        const porcentagem = Math.round((item.total_ocupacoes / salas[0].total_ocupacoes) * 100);
        
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-medium">${item.sala}</span>
                <span class="badge bg-primary">${item.total_ocupacoes}</span>
            </div>
            <div class="progress" style="height: 8px;">
                <div class="progress-bar" role="progressbar" style="width: ${porcentagem}%" aria-valuenow="${porcentagem}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        container.appendChild(div);
    });
    
    document.getElementById('salasMaisUtilizadas').style.display = 'block';
}

// Renderiza ocupações por tipo
function renderizarOcupacoesPorTipo() {
    const container = document.getElementById('ocupacoesPorTipo');
    
    if (!relatorioMensal.ocupacoes_por_tipo || relatorioMensal.ocupacoes_por_tipo.length === 0) {
        document.getElementById('nenhumaOcupacaoPorTipo').style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    
    const nomes = {
        'aula_regular': 'Aula Regular',
        'evento_especial': 'Evento Especial',
        'reuniao': 'Reunião',
        'manutencao': 'Manutenção',
        'reserva_especial': 'Reserva Especial'
    };
    
    const total = relatorioMensal.ocupacoes_por_tipo.reduce((sum, item) => sum + item.total, 0);
    
    relatorioMensal.ocupacoes_por_tipo.forEach(item => {
        const porcentagem = Math.round((item.total / total) * 100);
        const cor = coresOcorrencia[item.tipo] || rootStyle.getPropertyValue('--muted-color').trim();
        const nome = nomes[item.tipo] || item.tipo;
        
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-medium">
                    <span class="badge me-2" style="background-color: ${cor}; width: 12px; height: 12px; border-radius: 50%; display: inline-block;"></span>
                    ${nome}
                </span>
                <span class="text-muted">${item.total} (${porcentagem}%)</span>
            </div>
            <div class="progress" style="height: 8px;">
                <div class="progress-bar" role="progressbar" style="width: ${porcentagem}%; background-color: ${cor};" aria-valuenow="${porcentagem}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        container.appendChild(div);
    });
    
    document.getElementById('ocupacoesPorTipo').style.display = 'block';
}

// Renderiza ocupações por tipo (versão básica)
function renderizarOcupacoesPorTipoBasico(tipos) {
    const container = document.getElementById('ocupacoesPorTipo');
    
    if (tipos.length === 0) {
        document.getElementById('nenhumaOcupacaoPorTipo').style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    
    const nomes = {
        'aula_regular': 'Aula Regular',
        'evento_especial': 'Evento Especial',
        'reuniao': 'Reunião',
        'manutencao': 'Manutenção',
        'reserva_especial': 'Reserva Especial'
    };
    
    const total = tipos.reduce((sum, item) => sum + item.total, 0);
    
    tipos.forEach(item => {
        const porcentagem = Math.round((item.total / total) * 100);
        const cor = coresOcorrencia[item.tipo] || rootStyle.getPropertyValue('--muted-color').trim();
        const nome = nomes[item.tipo] || item.tipo;
        
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="fw-medium">
                    <span class="badge me-2" style="background-color: ${cor}; width: 12px; height: 12px; border-radius: 50%; display: inline-block;"></span>
                    ${nome}
                </span>
                <span class="text-muted">${item.total} (${porcentagem}%)</span>
            </div>
            <div class="progress" style="height: 8px;">
                <div class="progress-bar" role="progressbar" style="width: ${porcentagem}%; background-color: ${cor};" aria-valuenow="${porcentagem}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        container.appendChild(div);
    });
    
    document.getElementById('ocupacoesPorTipo').style.display = 'block';
}

// Funções auxiliares
function getInicioSemana() {
    const hoje = new Date();
    const dia = hoje.getDay();
    const diff = hoje.getDate() - dia + (dia === 0 ? -6 : 1); // Ajusta para segunda-feira
    const inicioSemana = new Date(hoje.setDate(diff));
    return inicioSemana.toISOString().split('T')[0];
}

function getFimSemana() {
    const hoje = new Date();
    const dia = hoje.getDay();
    const diff = hoje.getDate() - dia + (dia === 0 ? 0 : 7); // Ajusta para domingo
    const fimSemana = new Date(hoje.setDate(diff));
    return fimSemana.toISOString().split('T')[0];
}

function formatarDataCurta(dataStr) {
    const data = new Date(dataStr + 'T00:00:00');
    return data.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit'
    });
}

// Carrega tendência mensal de ocupações e renderiza gráfico
async function carregarTendenciaMensal() {
    if (!isAdmin()) return;
    try {
        const ano = new Date().getFullYear();
        const response = await fetch(`${API_URL}/ocupacoes/tendencia?ano=${ano}`, {
        });
        if (response.ok) {
            const dados = await response.json();
            renderizarGraficoTendencia(dados);
        }
    } catch (error) {
        console.error('Erro ao carregar tendência mensal:', error);
        showToast('Não conseguimos carregar a tendência mensal. Tente novamente.', 'danger');
    }
}

function renderizarGraficoTendencia(dados) {
    const ctx = document.getElementById('graficoTendenciaMensal');
    if (!ctx) return;

    const labels = dados.map(d => d.mes);
    const valores = dados.map(d => d.total);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ocupações',
                data: valores,
                borderColor: rootStyle.getPropertyValue('--primary-color').trim(),
                tension: 0.3
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

