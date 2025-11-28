let ocupacoesData = [];
let tiposOcupacao = [];

function obterNomeTipoOcupacao(valor) {
    if (!valor) {
        return '-';
    }

    const tipoEncontrado = tiposOcupacao.find(tipo => tipo.valor === valor);
    if (tipoEncontrado) {
        return tipoEncontrado.nome;
    }

    return valor
        .toString()
        .replace(/_/g, ' ')
        .replace(/\b\w/g, letra => letra.toUpperCase());
}

function criarBadgeStatus(status) {
    const mapa = {
        confirmado: 'success',
        pendente: 'warning',
        cancelado: 'secondary'
    };

    const classe = mapa[status] || 'secondary';
    const nome = status
        ? status.charAt(0).toUpperCase() + status.slice(1)
        : 'Desconhecido';

    return `<span class="badge bg-${classe}">${escapeHTML(nome)}</span>`;
}

function formatarTurnoHorario(ocupacao) {
    const turno = ocupacao.turno ? escapeHTML(ocupacao.turno) : '';
    const inicio = ocupacao.horario_inicio ? formatarHorario(ocupacao.horario_inicio) : '';
    const fim = ocupacao.horario_fim ? formatarHorario(ocupacao.horario_fim) : '';

    let horario = '';
    if (inicio && fim) {
        horario = `${inicio} - ${fim}`;
    } else if (inicio || fim) {
        horario = inicio || fim;
    }

    if (turno && horario) {
        return `${turno} (${horario})`;
    }

    return turno || horario || '-';
}

async function carregarTiposOcupacaoFiltro() {
    try {
        const response = await fetch(`${API_URL}/ocupacoes/tipos`, {
            headers: {}
        });

        if (response.ok) {
            tiposOcupacao = await response.json();
            const select = document.getElementById('filtroTipo');
            if (select) {
                tiposOcupacao.forEach(tipo => {
                    const option = document.createElement('option');
                    option.value = tipo.valor;
                    option.textContent = tipo.nome;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Erro ao carregar tipos de ocupação:', error);
        showToast('Não foi possível carregar os tipos de ocupação.', 'danger');
    }
}

async function carregarSalasFiltro() {
    try {
        const response = await fetch(`${API_URL}/salas`, {
            headers: {}
        });

        if (response.ok) {
            const salas = await response.json();
            const select = document.getElementById('filtroSala');
            if (select) {
                select.innerHTML = '<option value="">Todas</option>';
                salas.forEach(sala => {
                    const option = document.createElement('option');
                    option.value = sala.id;
                    option.textContent = sala.nome;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Erro ao carregar salas:', error);
        showToast('Não foi possível carregar a lista de salas.', 'danger');
    }
}

function renderizarOcupacoes(lista) {
    const tbody = document.getElementById('tabelaOcupacoes');
    const listaWrapper = document.getElementById('listaOcupacoes');

    if (!tbody || !listaWrapper) {
        return;
    }

    tbody.innerHTML = '';

    if (!lista || lista.length === 0) {
        const colunas = tbody.closest('table').querySelectorAll('thead th').length;
        const linha = document.createElement('tr');
        linha.innerHTML = `<td colspan="${colunas}" class="text-center py-4">Nenhuma ocupação encontrada.</td>`;
        tbody.appendChild(linha);
        listaWrapper.style.display = 'block';
        return;
    }

    listaWrapper.style.display = 'block';

    lista.forEach(ocupacao => {
        const linha = document.createElement('tr');
        const dataInicio = ocupacao.data_inicio ? formatarData(ocupacao.data_inicio) : '-';
        const dataFim = ocupacao.data_fim ? formatarData(ocupacao.data_fim) : '-';
        const mesmoDia = ocupacao.data_inicio === ocupacao.data_fim;
        const periodoBruto = mesmoDia ? dataInicio : `${dataInicio} - ${dataFim}`;
        const periodo = escapeHTML(periodoBruto);
        const turnoHorario = formatarTurnoHorario(ocupacao);
        const sala = ocupacao.sala_nome
            ? escapeHTML(ocupacao.sala_nome)
            : escapeHTML(`Sala ${ocupacao.sala_id}`);
        const cursoEvento = ocupacao.curso_evento ? escapeHTML(ocupacao.curso_evento) : '-';
        const tipoNome = obterNomeTipoOcupacao(ocupacao.tipo_ocupacao);
        const statusBadge = criarBadgeStatus(ocupacao.status);
        const identificador = ocupacao.id;
        const identificadorURL = encodeURIComponent(identificador);
        const idExibicao = ocupacao.primeira_ocupacao_id ?? ocupacao.id;

        linha.innerHTML = `
            <td>${escapeHTML(idExibicao.toString())}</td>
            <td>${periodo}</td>
            <td>${turnoHorario}</td>
            <td>${sala}</td>
            <td><a href="#" class="curso-evento-link" onclick="abrirModalInstrutor('${identificador}'); return false;">${cursoEvento}</a></td>
            <td>${escapeHTML(tipoNome)}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group" aria-label="Ações da ocupação ${escapeHTML(idExibicao.toString())}">
                    <a class="btn btn-outline-primary" href="/ocupacao/agendamento.html?editar=${identificadorURL}" title="Editar Ocupação">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-outline-danger" title="Excluir Ocupação" onclick="excluirOcupacao('${identificador}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(linha);
    });
}

function construirParametrosFiltro() {
    const params = new URLSearchParams();

    const dataInicio = document.getElementById('filtroDataInicio')?.value;
    const dataFim = document.getElementById('filtroDataFim')?.value;
    const salaId = document.getElementById('filtroSala')?.value;
    const tipo = document.getElementById('filtroTipo')?.value;
    const status = document.getElementById('filtroStatus')?.value;
    const curso = document.getElementById('filtroCurso')?.value;

    if (dataInicio) params.append('data_inicio', dataInicio);
    if (dataFim) params.append('data_fim', dataFim);
    if (salaId) params.append('sala_id', salaId);
    if (tipo) params.append('tipo_ocupacao', tipo);
    if (status) params.append('status', status);
    const cursoNormalizado = curso ? curso.trim() : '';
    if (cursoNormalizado) params.append('curso_evento', cursoNormalizado);

    return params;
}

async function carregarOcupacoes() {
    const loading = document.getElementById('loadingOcupacoes');
    const listaWrapper = document.getElementById('listaOcupacoes');

    if (loading) loading.style.display = 'block';
    if (listaWrapper) listaWrapper.style.display = 'none';

    try {
        const params = construirParametrosFiltro();
        const query = params.toString();
        const url = query ? `${API_URL}/ocupacoes?${query}` : `${API_URL}/ocupacoes`;

        const response = await fetch(url, {
            headers: {}
        });

        if (!response.ok) {
            const erro = await response.json().catch(() => null);
            throw new Error(erro?.erro || `Erro ${response.status}`);
        }

        ocupacoesData = await response.json();
        renderizarOcupacoes(ocupacoesData);
    } catch (error) {
        console.error('Erro ao carregar ocupações:', error);
        showToast(`Não foi possível carregar as ocupações. ${error.message}`, 'danger');
    } finally {
        if (loading) loading.style.display = 'none';
    }
}

function aplicarFiltros() {
    carregarOcupacoes();
}

function limparFiltros() {
    const campos = [
        'filtroDataInicio',
        'filtroDataFim',
        'filtroSala',
        'filtroTipo',
        'filtroStatus',
        'filtroCurso'
    ];

    campos.forEach(id => {
        const elemento = document.getElementById(id);
        if (!elemento) return;

        if (elemento.tagName === 'SELECT') {
            elemento.value = '';
        } else {
            elemento.value = '';
        }
    });

    carregarOcupacoes();
}

async function excluirOcupacao(id) {
    const confirmado = window.confirm('Deseja realmente excluir esta ocupação? Esta ação não pode ser desfeita.');
    if (!confirmado) {
        return;
    }

    try {
        await chamarAPI(`/ocupacoes/${encodeURIComponent(id)}`, 'DELETE');
        showToast('Ocupação excluída com sucesso!', 'success');
        await carregarOcupacoes();
    } catch (error) {
        console.error('Erro ao excluir ocupação:', error);
        const mensagem = error?.message || 'Não foi possível excluir a ocupação.';
        showToast(mensagem, 'danger');
    }
}

window.excluirOcupacao = excluirOcupacao;

document.addEventListener('DOMContentLoaded', async () => {
    if (!(await verificarAutenticacao())) {
        return;
    }

    if (!(await verificarPermissaoAdmin())) {
        return;
    }

    const usuario = getUsuarioLogado();
    if (usuario) {
        const nomeUsuarioNav = document.getElementById('nomeUsuarioNav');
        if (nomeUsuarioNav) {
            nomeUsuarioNav.textContent = usuario.nome;
        }
    }

    await Promise.all([
        carregarTiposOcupacaoFiltro(),
        carregarSalasFiltro()
    ]);

    document.getElementById('btnAplicarFiltros')?.addEventListener('click', aplicarFiltros);
    document.getElementById('btnLimparFiltros')?.addEventListener('click', limparFiltros);
    document.getElementById('filtroCurso')?.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            aplicarFiltros();
        }
    });

    aplicarFiltros();
});

// ===== Modal e funções de instrutor =====
let instrutoresCache = [];
let modalInstrutorBootstrap = null;

async function carregarInstrutores() {
    try {
        const instrutores = await chamarAPI('/instrutores?status=ativo', 'GET');

        instrutoresCache = instrutores;
        const select = document.getElementById('selectInstrutor');
        if (select) {
            select.innerHTML = '<option value="">Sem instrutor</option>';
            instrutoresCache.forEach(instrutor => {
                const option = document.createElement('option');
                option.value = instrutor.id;
                option.textContent = instrutor.nome;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar instrutores:', error);
        showToast('Não foi possível carregar os instrutores.', 'danger');
    }
}

function abrirModalInstrutor(ocupacaoId) {
    document.getElementById('ocupacaoIdModal').value = ocupacaoId;

    if (!modalInstrutorBootstrap) {
        const modalElement = document.getElementById('modalInstrutorOcupacao');
        if (modalElement) {
            modalInstrutorBootstrap = new bootstrap.Modal(modalElement);
        } else {
            console.error('Modal element not found');
            showToast('Erro: Modal não encontrado na página.', 'danger');
            return;
        }
    }

    if (instrutoresCache.length === 0) {
        carregarInstrutores();
    }

    modalInstrutorBootstrap.show();
}

async function salvarInstrutorOcupacao() {
    const ocupacaoId = document.getElementById('ocupacaoIdModal').value;
    const instrutorId = document.getElementById('selectInstrutor').value;

    try {
        const response = await chamarAPI(`/ocupacoes/${ocupacaoId}/instrutor`, 'PATCH', {
            instrutor_id: instrutorId || null
        });

        showToast('Instrutor atribuído com sucesso!', 'success');
        if (modalInstrutorBootstrap) {
            modalInstrutorBootstrap.hide();
        }
        await carregarOcupacoes();
    } catch (error) {
        console.error('Erro ao atribuir instrutor:', error);
        const mensagem = error?.message || 'Não foi possível atribuir o instrutor.';
        showToast(mensagem, 'danger');
    }
}

// Adicionar event listener para o botão salvar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    const btnSalvar = document.getElementById('btnSalvarInstrutor');
    if (btnSalvar) {
        btnSalvar.addEventListener('click', salvarInstrutorOcupacao);
    }
});

// Expor função globalmente para uso no onclick
window.abrirModalInstrutor = abrirModalInstrutor;

