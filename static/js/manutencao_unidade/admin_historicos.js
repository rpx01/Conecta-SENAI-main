/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabela = document.querySelector('#tabelaHistoricos tbody');
    const totalHistoricosEl = document.getElementById('totalHistoricos');
    const detalhesContainer = document.getElementById('detalhesHistorico');
    const listaAnexos = document.getElementById('listaAnexosHistorico');
    const modalEl = document.getElementById('modalDetalhesHistorico');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    const modalEditarEl = document.getElementById('modalEditarChamadoHistorico');
    const modalEditar = modalEditarEl ? new bootstrap.Modal(modalEditarEl) : null;
    const formEditar = document.getElementById('formEditarChamadoHistorico');
    const editarAreaSelect = document.getElementById('editarAreaHistoricoSelect');
    const editarTipoSelect = document.getElementById('editarTipoEquipamentoHistoricoSelect');
    const editarUrgenciaSelect = document.getElementById('editarUrgenciaHistoricoSelect');
    const editarDescricaoTextarea = document.getElementById('editarDescricaoHistorico');
    const editarPatrimonioInput = document.getElementById('editarPatrimonioHistoricoInput');
    const editarNumeroSerieInput = document.getElementById('editarNumeroSerieHistoricoInput');
    const btnSalvarEdicaoHistorico = document.getElementById('btnSalvarEdicaoHistorico');

    let usuarioLogado = null;
    let areasBase = [];
    let tiposEquipamentoBase = [];
    let chamadoEmEdicao = null;
    let textoOriginalSalvarEdicao = btnSalvarEdicaoHistorico?.innerHTML || '';
    let exibindoSomenteMesAtual = true;

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        usuarioLogado = getUsuarioLogado();
        atualizarNomeUsuario();
        await carregarBaseDados();
        await carregarHistoricos();
        configurarBotoesHistoricos();
    }

    function atualizarNomeUsuario() {
        const usuario = usuarioLogado || getUsuarioLogado();
        if (usuario) {
            const span = document.getElementById('userName');
            if (span) {
                span.textContent = usuario.nome;
            }
        }
    }

    async function carregarBaseDados() {
        try {
            const dados = await chamarAPI('/suporte_ti/basedados_formulario');
            areasBase = Array.isArray(dados.areas) ? dados.areas : [];
            tiposEquipamentoBase = Array.isArray(dados.tipos_equipamento)
                ? dados.tipos_equipamento
                : [];
            atualizarSelectsEdicao();
        } catch (error) {
            console.error('Falha ao carregar dados de apoio:', error);
        }
    }

    function preencherSelectEdicao(selectEl, itens, placeholder) {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = placeholder;
        option.dataset.placeholder = 'true';
        selectEl.appendChild(option);
        itens.forEach((item) => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = item.nome;
            selectEl.appendChild(opt);
        });
    }

    function atualizarSelectsEdicao() {
        preencherSelectEdicao(editarAreaSelect, areasBase, 'Selecione...');
        preencherSelectEdicao(editarTipoSelect, tiposEquipamentoBase, 'Selecione...');
    }

    async function carregarHistoricos() {
        try {
            const params = new URLSearchParams();
            params.set('status', 'Finalizado,Cancelado');

            if (exibindoSomenteMesAtual) {
                const agora = new Date();
                const inicioMes = new Date(agora.getFullYear(), agora.getMonth(), 1);
                const fimMes = new Date(agora.getFullYear(), agora.getMonth() + 1, 0);

                const dataInicio = inicioMes.toISOString().slice(0, 10); // yyyy-mm-dd
                const dataFim = fimMes.toISOString().slice(0, 10);

                console.log('[Históricos] Filtro de mês ativo:', {
                    mes: agora.getMonth() + 1,
                    ano: agora.getFullYear(),
                    dataInicio,
                    dataFim
                });

                params.set('data_inicio', dataInicio);
                params.set('data_fim', dataFim);
            } else {
                console.log('[Históricos] Exibindo todos os registros (sem filtro de data)');
            }

            const endpoint = `/suporte_ti/admin/todos_chamados?${params.toString()}`;
            console.log('[Históricos] Buscando:', endpoint);
            const chamados = await chamarAPI(endpoint);
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            renderizarChamados([]);
        }
    }

    function renderizarChamados(chamados) {
        if (!tabela) return;
        tabela.innerHTML = '';
        const lista = Array.isArray(chamados) ? chamados : [];
        const total = lista.length;
        if (totalHistoricosEl) {
            totalHistoricosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum histórico encontrado no momento.</td>';
            tabela.appendChild(linha);
            return;
        }
        lista.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            const statusAtual = chamado.status || '-';
            const botoesRoot = usuarioLogado?.is_root
                ? `
                        <button class="btn btn-sm btn-outline-secondary" data-acao="editar" title="Editar chamado">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" data-acao="excluir" title="Excluir chamado">
                            <i class="bi bi-trash"></i>
                        </button>`
                : '';
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(statusAtual)}">${sanitizeHTML(statusAtual)}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                        ${botoesRoot}
                    </div>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModalDetalhes(chamado));
            if (usuarioLogado?.is_root) {
                const botaoEditar = tr.querySelector('button[data-acao="editar"]');
                botaoEditar?.addEventListener('click', () => abrirModalEdicao(chamado));

                const botaoExcluir = tr.querySelector('button[data-acao="excluir"]');
                botaoExcluir?.addEventListener('click', () => excluirChamado(chamado));
            }
            tabela.appendChild(tr);
        });
    }

    function classeUrgencia(urgencia) {
        switch ((urgencia || '').toLowerCase()) {
            case 'alto':
                return 'danger';
            case 'médio':
            case 'medio':
                return 'warning';
            default:
                return 'secondary';
        }
    }

    function classeStatus(status) {
        switch ((status || '').toLowerCase()) {
            case 'aberto':
                return 'primary';
            case 'em atendimento':
                return 'warning';
            case 'finalizado':
                return 'success';
            case 'cancelado':
                return 'secondary';
            default:
                return 'secondary';
        }
    }

    function preencherDetalheTexto(elemento, valor) {
        if (!elemento) return;
        const placeholder = '-';
        if (valor === null || valor === undefined) {
            elemento.textContent = placeholder;
            return;
        }
        const texto = typeof valor === 'string' ? valor : String(valor);
        if (!texto.trim()) {
            elemento.textContent = placeholder;
            return;
        }
        const partes = texto.split(/\r?\n/);
        if (partes.length === 1) {
            elemento.textContent = partes[0];
            return;
        }
        elemento.innerHTML = '';
        partes.forEach((parte, index) => {
            if (index) {
                elemento.appendChild(document.createElement('br'));
            }
            elemento.appendChild(document.createTextNode(parte));
        });
    }

    function abrirModalDetalhes(chamado) {
        if (!modal || !detalhesContainer) return;
        detalhesContainer.innerHTML = '';
        const campos = [
            ['Protocolo', `#${chamado.id}`],
            ['Data de abertura', formatarData(chamado.created_at)],
            ['Usuário', chamado.nome || chamado.email || '-'],
            ['Área', chamado.area || '-'],
            ['Tipo de equipamento', chamado.tipo_equipamento_nome || '-'],
            ['Patrimônio', chamado.patrimonio || '-'],
            ['Número de série', chamado.numero_serie || '-'],
            ['Descrição', chamado.descricao_problema || '-'],
            ['Nível de urgência', chamado.nivel_urgencia || '-'],
            ['Status', chamado.status || '-'],
            ['Observações', chamado.observacoes || '-']
        ];
        campos.forEach(([label, valor]) => {
            const dt = document.createElement('dt');
            dt.className = 'col-sm-4 fw-semibold';
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.className = 'col-sm-8';
            preencherDetalheTexto(dd, valor);
            detalhesContainer.appendChild(dt);
            detalhesContainer.appendChild(dd);
        });
        renderizarAnexos(chamado.anexos || []);
        modal.show();
    }

    function renderizarAnexos(anexos) {
        if (!listaAnexos) return;
        listaAnexos.innerHTML = '';
        if (!anexos.length) {
            return;
        }
        const titulo = document.createElement('h3');
        titulo.className = 'h6 mt-3';
        titulo.textContent = 'Anexos';
        const lista = document.createElement('ul');
        lista.className = 'list-unstyled';
        anexos.forEach((caminho, index) => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = caminho;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = `Arquivo ${index + 1}`;
            li.appendChild(link);
            lista.appendChild(li);
        });
        listaAnexos.appendChild(titulo);
        listaAnexos.appendChild(lista);
    }

    function normalizarUrgenciaValor(urgencia) {
        switch ((urgencia || '').toLowerCase()) {
            case 'alto':
                return 'Alto';
            case 'medio':
            case 'médio':
                return 'Médio';
            case 'baixo':
                return 'Baixo';
            default:
                return '';
        }
    }

    function encontrarAreaPorNome(nome) {
        if (!nome) return null;
        const comparador = nome.trim().toLowerCase();
        return (
            areasBase.find((area) => (area.nome || '').trim().toLowerCase() === comparador) || null
        );
    }

    function abrirModalEdicao(chamado) {
        if (!modalEditar || !usuarioLogado?.is_root) {
            return;
        }
        chamadoEmEdicao = chamado;
        atualizarSelectsEdicao();

        if (editarDescricaoTextarea) {
            editarDescricaoTextarea.value = chamado.descricao_problema || '';
        }
        if (editarPatrimonioInput) {
            editarPatrimonioInput.value = chamado.patrimonio || '';
        }
        if (editarNumeroSerieInput) {
            editarNumeroSerieInput.value = chamado.numero_serie || '';
        }
        if (editarUrgenciaSelect) {
            editarUrgenciaSelect.value = normalizarUrgenciaValor(chamado.nivel_urgencia);
        }
        if (editarAreaSelect) {
            let valorSelecionado = '';
            if (chamado.area) {
                const area = encontrarAreaPorNome(chamado.area);
                if (area) {
                    valorSelecionado = String(area.id);
                } else {
                    const opcao = document.createElement('option');
                    opcao.value = '__custom__';
                    opcao.dataset.areaNome = chamado.area;
                    opcao.textContent = chamado.area;
                    editarAreaSelect.appendChild(opcao);
                    valorSelecionado = '__custom__';
                }
            }
            editarAreaSelect.value = valorSelecionado;
        }
        if (editarTipoSelect) {
            let valorSelecionado = '';
            if (chamado.tipo_equipamento_id) {
                const tipo = tiposEquipamentoBase.find(
                    (item) => item.id === chamado.tipo_equipamento_id
                );
                if (tipo) {
                    valorSelecionado = String(tipo.id);
                } else {
                    const opcao = document.createElement('option');
                    opcao.value = String(chamado.tipo_equipamento_id);
                    opcao.textContent = chamado.tipo_equipamento_nome
                        || `Tipo ${chamado.tipo_equipamento_id}`;
                    opcao.dataset.custom = 'true';
                    editarTipoSelect.appendChild(opcao);
                    valorSelecionado = opcao.value;
                }
            }
            editarTipoSelect.value = valorSelecionado;
        }

        modalEditar.show();
    }

    async function salvarEdicaoHistorico() {
        if (!usuarioLogado?.is_root || !chamadoEmEdicao) {
            modalEditar?.hide();
            return;
        }
        if (formEditar && !formEditar.reportValidity()) {
            return;
        }

        const payload = {};
        const descricao = editarDescricaoTextarea?.value.trim() || '';
        if (!descricao) {
            showToast('A descrição do problema é obrigatória.', 'warning');
            return;
        }
        payload.descricao_problema = descricao;

        if (editarUrgenciaSelect) {
            const urgencia = normalizarUrgenciaValor(editarUrgenciaSelect.value);
            if (!urgencia) {
                showToast('Selecione um nível de urgência válido.', 'warning');
                return;
            }
            payload.nivel_urgencia = urgencia;
        }

        if (editarTipoSelect) {
            const tipoValor = editarTipoSelect.value;
            if (!tipoValor) {
                showToast('Selecione o tipo de equipamento.', 'warning');
                return;
            }
            const tipoId = Number(tipoValor);
            if (Number.isNaN(tipoId)) {
                showToast('Tipo de equipamento inválido.', 'warning');
                return;
            }
            payload.tipo_equipamento_id = tipoId;
        }

        if (editarAreaSelect) {
            const opcaoSelecionada = editarAreaSelect.selectedOptions[0];
            if (!opcaoSelecionada || opcaoSelecionada.dataset?.placeholder) {
                showToast('Selecione a área responsável.', 'warning');
                return;
            }
            if (editarAreaSelect.value && editarAreaSelect.value !== '__custom__') {
                const areaId = Number(editarAreaSelect.value);
                if (Number.isNaN(areaId)) {
                    showToast('Área inválida.', 'warning');
                    return;
                }
                payload.area_id = areaId;
            }
            const areaNome = opcaoSelecionada.dataset.areaNome || opcaoSelecionada.textContent.trim();
            if (areaNome) {
                payload.area = areaNome;
            }
        }

        if (editarPatrimonioInput) {
            const valorPatrimonio = editarPatrimonioInput.value.trim();
            payload.patrimonio = valorPatrimonio || null;
        }
        if (editarNumeroSerieInput) {
            const valorSerie = editarNumeroSerieInput.value.trim();
            payload.numero_serie = valorSerie || null;
        }

        if (btnSalvarEdicaoHistorico) {
            btnSalvarEdicaoHistorico.disabled = true;
            btnSalvarEdicaoHistorico.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Salvando...';
        }

        try {
            const resposta = await chamarAPI(
                `/suporte_ti/admin/chamados/${chamadoEmEdicao.id}`,
                'PUT',
                payload
            );
            showToast(resposta?.mensagem || 'Chamado atualizado com sucesso!', 'success');
            modalEditar?.hide();
            chamadoEmEdicao = null;
            await carregarHistoricos();
        } catch (error) {
            showToast(error?.message || 'Não foi possível atualizar o chamado.', 'danger');
        } finally {
            if (btnSalvarEdicaoHistorico) {
                btnSalvarEdicaoHistorico.disabled = false;
                btnSalvarEdicaoHistorico.innerHTML = textoOriginalSalvarEdicao
                    || '<i class="bi bi-save me-2"></i>Salvar alterações';
            }
        }
    }

    async function excluirChamado(chamado) {
        if (!usuarioLogado?.is_root) {
            return;
        }
        const confirmou = window.confirm(
            'Tem certeza de que deseja excluir este chamado? Essa ação não poderá ser desfeita.'
        );
        if (!confirmou) {
            return;
        }
        try {
            const resposta = await chamarAPI(`/suporte_ti/admin/chamados/${chamado.id}`, 'DELETE');
            showToast(resposta?.mensagem || 'Chamado excluído com sucesso!', 'success');
            await carregarHistoricos();
        } catch (error) {
            showToast(error?.message || 'Não foi possível excluir o chamado.', 'danger');
        }
    }

    if (btnSalvarEdicaoHistorico) {
        btnSalvarEdicaoHistorico.addEventListener('click', salvarEdicaoHistorico);
    }

    if (modalEditarEl) {
        modalEditarEl.addEventListener('hidden.bs.modal', () => {
            chamadoEmEdicao = null;
            if (formEditar) {
                formEditar.reset();
            }
            atualizarSelectsEdicao();
            if (btnSalvarEdicaoHistorico) {
                btnSalvarEdicaoHistorico.disabled = false;
                btnSalvarEdicaoHistorico.innerHTML = textoOriginalSalvarEdicao
                    || '<i class="bi bi-save me-2"></i>Salvar alterações';
            }
        });
    }

    function configurarBotoesHistoricos() {
        // Botão para exibir todos os históricos ou apenas mês atual
        const btnExibirTodosHistoricos = document.getElementById('btnExibirTodosHistoricos');
        if (btnExibirTodosHistoricos) {
            console.log('[Históricos] Botão "Exibir todos" configurado');
            btnExibirTodosHistoricos.addEventListener('click', () => {
                console.log('[Históricos] Alternando filtro de mês. Estado anterior:', exibindoSomenteMesAtual);
                exibindoSomenteMesAtual = !exibindoSomenteMesAtual;
                btnExibirTodosHistoricos.textContent = exibindoSomenteMesAtual
                    ? 'Exibir todos'
                    : 'Exibir apenas mês atual';
                carregarHistoricos();
            });
        } else {
            console.error('[Históricos] Botão "btnExibirTodosHistoricos" não encontrado no DOM');
        }

        // Botão para exportar todos os chamados para Excel/CSV
        const btnExportarExcelHistoricos = document.getElementById('btnExportarExcelHistoricos');
        if (btnExportarExcelHistoricos) {
            console.log('[Históricos] Botão "Exportar Excel" configurado');
            btnExportarExcelHistoricos.addEventListener('click', () => {
                console.log('[Históricos] Iniciando exportação para Excel');
                window.location.href = '/api/suporte_ti/admin/chamados/exportar_excel';
            });
        } else {
            console.error('[Históricos] Botão "btnExportarExcelHistoricos" não encontrado no DOM');
        }
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();

