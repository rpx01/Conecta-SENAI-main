/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabelaChamadosAbertos = document.querySelector('#tabelaChamadosAbertos tbody');
    const tabelaChamadosEmAtendimento = document.querySelector('#tabelaChamadosEmAtendimento tbody');
    const totalChamadosAbertosEl = document.getElementById('totalChamados');
    const totalChamadosAtendimentoEl = document.getElementById('totalChamadosAtendimento');
    const filtroStatus = document.getElementById('filtroStatus');
    const filtroUrgencia = document.getElementById('filtroUrgencia');
    const filtroArea = document.getElementById('filtroArea');
    const filtroTipo = document.getElementById('filtroTipoEquipamento');
    const filtroDataInicio = document.getElementById('filtroDataInicio');
    const filtroDataFim = document.getElementById('filtroDataFim');
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    const btnLimparFiltros = document.getElementById('btnLimparFiltros');
    const detalhesContainer = document.getElementById('detalhesChamadoAdmin');
    const listaAnexos = document.getElementById('listaAnexosAdmin');
    const modalDetalhesEl = document.getElementById('modalDetalhesChamadoAdmin');
    const modalDetalhes = modalDetalhesEl ? new bootstrap.Modal(modalDetalhesEl) : null;
    const modalFinalizarEl = document.getElementById('modalFinalizarChamado');
    const modalFinalizar = modalFinalizarEl ? new bootstrap.Modal(modalFinalizarEl) : null;
    const observacoesFinalizacaoEl = document.getElementById('observacoesFinalizacao');
    const btnConfirmarFinalizacao = document.getElementById('btnConfirmarFinalizacao');
    const modalEditarEl = document.getElementById('modalEditarChamado');
    const modalEditar = modalEditarEl ? new bootstrap.Modal(modalEditarEl) : null;
    const formEditarChamado = document.getElementById('formEditarChamado');
    const editarAreaSelect = document.getElementById('editarAreaSelect');
    const editarTipoSelect = document.getElementById('editarTipoEquipamentoSelect');
    const editarUrgenciaSelect = document.getElementById('editarUrgenciaSelect');
    const editarDescricaoTextarea = document.getElementById('editarDescricaoProblema');
    const editarPatrimonioInput = document.getElementById('editarPatrimonioInput');
    const editarNumeroSerieInput = document.getElementById('editarNumeroSerieInput');
    const btnSalvarEdicaoChamado = document.getElementById('btnSalvarEdicaoChamado');

    let chamadoSelecionadoParaFinalizar = null;
    let textoOriginalBotaoFinalizacao = '';
    let usuarioLogado = null;
    let chamadoEmEdicao = null;
    let textoOriginalSalvarEdicao = '';
    let areasBase = [];
    let tiposEquipamentoBase = [];

    if (btnSalvarEdicaoChamado) {
        textoOriginalSalvarEdicao = btnSalvarEdicaoChamado.innerHTML;
    }

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        usuarioLogado = getUsuarioLogado();
        atualizarNomeUsuario();
        await carregarBaseFiltros();
        await buscarChamados();
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

    async function carregarBaseFiltros() {
        try {
            const dados = await chamarAPI('/suporte_ti/basedados_formulario');
            areasBase = Array.isArray(dados.areas) ? dados.areas : [];
            tiposEquipamentoBase = Array.isArray(dados.tipos_equipamento)
                ? dados.tipos_equipamento
                : [];
            preencherSelect(filtroArea, areasBase, 'Todas', 'nome');
            preencherSelect(filtroTipo, tiposEquipamentoBase, 'Todos');
            atualizarSelectsEdicao();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelect(selectEl, itens, placeholder, valueKey = 'id', labelKey = 'nome') {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        if (placeholder !== undefined) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = placeholder;
            selectEl.appendChild(option);
        }
        itens.forEach((item) => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            selectEl.appendChild(option);
        });
    }

    function preencherSelectEdicao(selectEl, itens, placeholder, valueKey = 'id', labelKey = 'nome') {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = placeholder;
        option.dataset.placeholder = 'true';
        selectEl.appendChild(option);
        itens.forEach((item) => {
            const opt = document.createElement('option');
            opt.value = item[valueKey];
            opt.textContent = item[labelKey];
            selectEl.appendChild(opt);
        });
    }

    function atualizarSelectsEdicao() {
        preencherSelectEdicao(editarAreaSelect, areasBase, 'Selecione...');
        preencherSelectEdicao(editarTipoSelect, tiposEquipamentoBase, 'Selecione...');
    }

    function obterStatusSelecionados() {
        if (!filtroStatus) return [];
        return Array.from(filtroStatus.selectedOptions).map((opt) => opt.value);
    }

    async function buscarChamados() {
        const params = new URLSearchParams();
        const status = obterStatusSelecionados();
        if (status.length) {
            params.set('status', status.join(','));
        } else {
            params.set('status', 'Aberto,Em Atendimento');
        }
        if (filtroUrgencia?.value) {
            params.set('nivel_urgencia', filtroUrgencia.value);
        }
        if (filtroArea?.value) {
            params.set('area', filtroArea.value);
        }
        if (filtroTipo?.value) {
            params.set('tipo_equipamento_id', filtroTipo.value);
        }
        if (filtroDataInicio?.value) {
            params.set('data_inicio', filtroDataInicio.value);
        }
        if (filtroDataFim?.value) {
            params.set('data_fim', filtroDataFim.value);
        }
        const endpoint = params.toString()
            ? `/suporte_ti/admin/todos_chamados?${params.toString()}`
            : '/suporte_ti/admin/todos_chamados?status=Aberto,Em Atendimento';
        try {
            const chamados = await chamarAPI(endpoint);
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            renderizarChamados([]);
        }
    }

    function renderizarChamados(chamados) {
        const listaChamados = Array.isArray(chamados) ? chamados : [];
        const chamadosAbertos = listaChamados.filter((item) => (item.status || '').toLowerCase() === 'aberto');
        const chamadosEmAtendimento = listaChamados.filter((item) => (item.status || '').toLowerCase() === 'em atendimento');

        atualizarTabelaAbertos(chamadosAbertos);
        atualizarTabelaEmAtendimento(chamadosEmAtendimento);
    }

    function atualizarTabelaAbertos(chamados) {
        if (!tabelaChamadosAbertos) return;
        tabelaChamadosAbertos.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAbertosEl) {
            totalChamadosAbertosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum chamado em aberto no momento.</td>';
            tabelaChamadosAbertos.appendChild(linha);
            return;
        }
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            const statusAtual = chamado.status || 'Aberto';
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
                        <button class="btn btn-sm btn-success" data-acao="atender" title="Mover para atendimento">
                            <i class="bi bi-headset"></i> Atender chamado
                        </button>
                        ${botoesRoot}
                    </div>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModal(chamado));

            const botaoAtender = tr.querySelector('button[data-acao="atender"]');
            botaoAtender?.addEventListener('click', async () => {
                botaoAtender.disabled = true;
                const sucesso = await atualizarStatusChamado(chamado.id, 'Em Atendimento');
                if (!sucesso) {
                    botaoAtender.disabled = false;
                }
            });

            if (usuarioLogado?.is_root) {
                const botaoEditar = tr.querySelector('button[data-acao="editar"]');
                botaoEditar?.addEventListener('click', () => abrirModalEdicao(chamado));

                const botaoExcluir = tr.querySelector('button[data-acao="excluir"]');
                botaoExcluir?.addEventListener('click', () => excluirChamado(chamado));
            }

            tabelaChamadosAbertos.appendChild(tr);
        });
    }

    function atualizarTabelaEmAtendimento(chamados) {
        if (!tabelaChamadosEmAtendimento) return;
        tabelaChamadosEmAtendimento.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAtendimentoEl) {
            totalChamadosAtendimentoEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum chamado em atendimento.</td>';
            tabelaChamadosEmAtendimento.appendChild(linha);
            return;
        }
        chamados.forEach((chamado, indice) => {
            const statusAtual = chamado.status || 'Em Atendimento';
            const tr = document.createElement('tr');
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
                        <button class="btn btn-sm btn-success" data-acao="finalizar" title="Finalizar chamado">
                            <i class="bi bi-check2"></i> Finalizar
                        </button>
                        <button class="btn btn-sm btn-outline-danger" data-acao="cancelar" title="Cancelar chamado">
                            <i class="bi bi-x-circle"></i> Cancelar
                        </button>
                        ${botoesRoot}
                    </div>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModal(chamado));

            const botaoFinalizar = tr.querySelector('button[data-acao="finalizar"]');
            botaoFinalizar?.addEventListener('click', () => abrirModalFinalizacao(chamado));

            const botaoCancelar = tr.querySelector('button[data-acao="cancelar"]');
            botaoCancelar?.addEventListener('click', async () => {
                if (!window.confirm('Tem certeza de que deseja cancelar este chamado?')) {
                    return;
                }
                botaoCancelar.disabled = true;
                const sucesso = await atualizarStatusChamado(chamado.id, 'Cancelado');
                if (!sucesso) {
                    botaoCancelar.disabled = false;
                }
            });

            if (usuarioLogado?.is_root) {
                const botaoEditar = tr.querySelector('button[data-acao="editar"]');
                botaoEditar?.addEventListener('click', () => abrirModalEdicao(chamado));

                const botaoExcluir = tr.querySelector('button[data-acao="excluir"]');
                botaoExcluir?.addEventListener('click', () => excluirChamado(chamado));
            }

            tabelaChamadosEmAtendimento.appendChild(tr);
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

    async function atualizarStatusChamado(chamadoId, novoStatus, corpoAdicional = {}) {
        try {
            const resposta = await chamarAPI(
                `/suporte_ti/admin/chamados/${chamadoId}/status`,
                'PUT',
                { status: novoStatus, ...corpoAdicional }
            );
            showToast(resposta?.mensagem || 'Status atualizado com sucesso!', 'success');
            await buscarChamados();
            return true;
        } catch (error) {
            const mensagem = error?.message || 'Não foi possível atualizar o status do chamado.';
            showToast(mensagem, 'danger');
            return false;
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

    function abrirModal(chamado) {
        if (!modalDetalhes || !detalhesContainer) return;
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
        modalDetalhes.show();
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
                const areaEncontrada = encontrarAreaPorNome(chamado.area);
                if (areaEncontrada) {
                    valorSelecionado = String(areaEncontrada.id);
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

        if (btnSalvarEdicaoChamado && !textoOriginalSalvarEdicao) {
            textoOriginalSalvarEdicao = btnSalvarEdicaoChamado.innerHTML;
        }

        modalEditar.show();
    }

    async function salvarEdicaoChamado() {
        if (!usuarioLogado?.is_root || !chamadoEmEdicao) {
            modalEditar?.hide();
            return;
        }
        if (formEditarChamado && !formEditarChamado.reportValidity()) {
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
            const urgenciaNormalizada = normalizarUrgenciaValor(editarUrgenciaSelect.value);
            if (!urgenciaNormalizada) {
                showToast('Selecione um nível de urgência válido.', 'warning');
                return;
            }
            payload.nivel_urgencia = urgenciaNormalizada;
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

        if (btnSalvarEdicaoChamado) {
            btnSalvarEdicaoChamado.disabled = true;
            btnSalvarEdicaoChamado.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Salvando...';
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
            await buscarChamados();
        } catch (error) {
            showToast(error?.message || 'Não foi possível atualizar o chamado.', 'danger');
        } finally {
            if (btnSalvarEdicaoChamado) {
                btnSalvarEdicaoChamado.disabled = false;
                btnSalvarEdicaoChamado.innerHTML = textoOriginalSalvarEdicao
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
            await buscarChamados();
        } catch (error) {
            showToast(error?.message || 'Não foi possível excluir o chamado.', 'danger');
        }
    }

    function abrirModalFinalizacao(chamado) {
        if (!modalFinalizar) return;
        chamadoSelecionadoParaFinalizar = chamado;
        textoOriginalBotaoFinalizacao = btnConfirmarFinalizacao?.innerHTML || '';
        if (observacoesFinalizacaoEl) {
            observacoesFinalizacaoEl.value = '';
        }
        modalFinalizar.show();
    }

    async function confirmarFinalizacao() {
        if (!chamadoSelecionadoParaFinalizar) {
            modalFinalizar?.hide();
            return;
        }
        if (!btnConfirmarFinalizacao) return;
        textoOriginalBotaoFinalizacao = textoOriginalBotaoFinalizacao || btnConfirmarFinalizacao.innerHTML;
        btnConfirmarFinalizacao.disabled = true;
        btnConfirmarFinalizacao.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Finalizando...';
        const possuiCampoObservacoes = Boolean(observacoesFinalizacaoEl);
        const observacoes = possuiCampoObservacoes
            ? observacoesFinalizacaoEl.value.trim()
            : '';
        const corpo = possuiCampoObservacoes ? { observacoes } : {};
        const sucesso = await atualizarStatusChamado(chamadoSelecionadoParaFinalizar.id, 'Finalizado', corpo);
        btnConfirmarFinalizacao.disabled = false;
        btnConfirmarFinalizacao.innerHTML = textoOriginalBotaoFinalizacao || '<i class="bi bi-check2-circle me-2"></i>Confirmar finalização';
        if (sucesso) {
            modalFinalizar?.hide();
            chamadoSelecionadoParaFinalizar = null;
            if (observacoesFinalizacaoEl) {
                observacoesFinalizacaoEl.value = '';
            }
        }
    }

    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', buscarChamados);
    }

    if (btnLimparFiltros) {
        btnLimparFiltros.addEventListener('click', () => {
            filtroStatus && Array.from(filtroStatus.options).forEach((opt) => (opt.selected = false));
            if (filtroUrgencia) filtroUrgencia.value = '';
            if (filtroArea) filtroArea.value = '';
            if (filtroTipo) filtroTipo.value = '';
            if (filtroDataInicio) filtroDataInicio.value = '';
            if (filtroDataFim) filtroDataFim.value = '';
            buscarChamados();
        });
    }

    if (btnConfirmarFinalizacao) {
        btnConfirmarFinalizacao.addEventListener('click', confirmarFinalizacao);
    }

    if (btnSalvarEdicaoChamado) {
        btnSalvarEdicaoChamado.addEventListener('click', salvarEdicaoChamado);
    }

    if (modalEditarEl) {
        modalEditarEl.addEventListener('hidden.bs.modal', () => {
            chamadoEmEdicao = null;
            if (formEditarChamado) {
                formEditarChamado.reset();
            }
            atualizarSelectsEdicao();
            if (btnSalvarEdicaoChamado) {
                btnSalvarEdicaoChamado.disabled = false;
                btnSalvarEdicaoChamado.innerHTML = textoOriginalSalvarEdicao
                    || '<i class="bi bi-save me-2"></i>Salvar alterações';
            }
        });
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
