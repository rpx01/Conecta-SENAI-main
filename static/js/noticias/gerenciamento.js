/* global bootstrap, chamarAPI, showToast, verificarPermissaoAdmin, sanitizeHTML, getUsuarioLogado, verificarAutenticacao */

document.addEventListener('DOMContentLoaded', async () => {
    const usuario = typeof getUsuarioLogado === 'function' ? getUsuarioLogado() : null;

    if (!usuario || (usuario.tipo !== 'admin' && usuario.tipo !== 'secretaria')) {
        alert('Você não tem permissão para acessar esta página. Redirecionando...');
        window.location.href = '/noticias/index.html';
        return;
    }

    if (usuario.tipo === 'admin') {
        const possuiPermissao = await verificarPermissaoAdmin();
        if (!possuiPermissao) {
            return;
        }
    } else if (typeof verificarAutenticacao === 'function') {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) {
            return;
        }
    }

    const tabelaBody = document.getElementById('newsAdminTableBody');
    const paginacaoEl = document.getElementById('newsAdminPagination');
    const totalBadge = document.getElementById('newsAdminTotal');
    const searchForm = document.getElementById('newsAdminSearchForm');
    const resetButton = document.getElementById('newsAdminReset');
    const exportarButton = document.getElementById('btnExportarNoticias');
    const modalEl = document.getElementById('noticiaModal');
    const noticiaModal = new bootstrap.Modal(modalEl);
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoExclusaoModal'));
    const form = document.getElementById('noticiaForm');
    const btnSalvar = document.getElementById('btnSalvarNoticia');
    const publicarImediatamenteCheckbox = document.getElementById('noticiaAtivo');
    const marcarCalendarioCheckbox = document.getElementById('noticiaCalendario');
    const dataEventoContainer =
        document.getElementById('noticiaDataEventoContainer') ||
        document.getElementById('data-evento-div') ||
        document.querySelector('.data-evento-div');
    const dataEventoInput = document.getElementById('noticiaDataEvento');
    const agendamentoDiv = document.getElementById('agendamentoPublicacao');
    const dataAgendamentoInput = document.getElementById('noticiaDataAgendamento');
    const imagemInput = document.getElementById('noticiaImagem');

    const camposFormulario = {
        titulo: document.getElementById('noticiaTitulo'),
        resumo: document.getElementById('noticiaResumo'),
        conteudo: document.getElementById('noticiaConteudo'),
        dataPublicacao: document.getElementById('noticiaDataPublicacao'),
        dataAgendamento: dataAgendamentoInput,
        marcarCalendario: marcarCalendarioCheckbox,
        dataEvento: dataEventoInput
    };

    const feedbacks = {
        titulo: document.getElementById('feedbackTitulo'),
        resumo: document.getElementById('feedbackResumo'),
        conteudo: document.getElementById('feedbackConteudo'),
        dataPublicacao: document.getElementById('feedbackDataPublicacao'),
        dataAgendamento: document.getElementById('feedbackDataAgendamento'),
        dataEvento: document.getElementById('feedbackDataEvento')
    };

    let focoAplicado = false;

    function limparValidacaoCampos() {
        focoAplicado = false;
        Object.values(camposFormulario).forEach(campo => {
            if (!campo) return;
            campo.classList.remove('is-invalid');
            campo.removeAttribute('aria-invalid');
        });
        Object.values(feedbacks).forEach(feedback => {
            if (feedback) {
                feedback.textContent = '';
            }
        });
    }

    function limparErroCampoEspecifico(chave) {
        const campo = camposFormulario[chave];
        const feedback = feedbacks[chave];
        if (campo) {
            campo.classList.remove('is-invalid');
            campo.removeAttribute('aria-invalid');
        }
        if (feedback) {
            feedback.textContent = '';
        }
    }

    function registrarErroCampo(chave, mensagem) {
        const campo = camposFormulario[chave];
        const feedback = feedbacks[chave];
        if (campo) {
            campo.classList.add('is-invalid');
            campo.setAttribute('aria-invalid', 'true');
            if (!focoAplicado && typeof campo.focus === 'function') {
                campo.focus({ preventScroll: true });
                focoAplicado = true;
            }
        }
        if (feedback) {
            feedback.textContent = mensagem;
        }
    }

    function validarCamposObrigatorios(payload) {
        const erros = [];
        const titulo = payload.titulo || '';
        if (!titulo || titulo.length < 3) {
            const mensagem = 'Informe um título com pelo menos 3 caracteres.';
            registrarErroCampo('titulo', mensagem);
            erros.push(mensagem);
        }

        const resumo = payload.resumo || '';
        if (!resumo || resumo.length < 10) {
            const mensagem = 'O resumo deve possuir ao menos 10 caracteres.';
            registrarErroCampo('resumo', mensagem);
            erros.push(mensagem);
        }

        const conteudo = payload.conteudo || '';
        if (!conteudo || conteudo.length < 20) {
            const mensagem = 'O conteúdo deve possuir ao menos 20 caracteres.';
            registrarErroCampo('conteudo', mensagem);
            erros.push(mensagem);
        }

        const dataPublicacao = payload.dataPublicacao;
        if (dataPublicacao) {
            const data = new Date(dataPublicacao);
            if (Number.isNaN(data.getTime())) {
                const mensagem = 'Informe uma data de publicação válida ou deixe o campo vazio.';
                registrarErroCampo('dataPublicacao', mensagem);
                erros.push(mensagem);
            }
        }

        if (payload.publicarImediatamente === false) {
            const dataAgendamento = payload.dataAgendamento;
            if (!dataAgendamento) {
                const mensagem = 'Informe uma data e hora para o agendamento da publicação.';
                registrarErroCampo('dataAgendamento', mensagem);
                erros.push(mensagem);
            } else {
                const data = new Date(dataAgendamento);
                if (Number.isNaN(data.getTime())) {
                    const mensagem = 'Informe uma data de agendamento válida ou marque a publicação imediata.';
                    registrarErroCampo('dataAgendamento', mensagem);
                    erros.push(mensagem);
                }
            }
        } else if (payload.dataAgendamento) {
            const data = new Date(payload.dataAgendamento);
            if (Number.isNaN(data.getTime())) {
                const mensagem = 'Informe uma data de agendamento válida.';
                registrarErroCampo('dataAgendamento', mensagem);
                erros.push(mensagem);
            }
        }

        if (payload.marcarCalendario) {
            const dataEvento = payload.dataEvento;
            if (!dataEvento) {
                const mensagem = 'Informe uma data para o evento.';
                registrarErroCampo('dataEvento', mensagem);
                erros.push(mensagem);
            } else {
                const data = new Date(dataEvento);
                if (Number.isNaN(data.getTime())) {
                    const mensagem = 'Informe uma data do evento válida.';
                    registrarErroCampo('dataEvento', mensagem);
                    erros.push(mensagem);
                }
            }
        } else if (payload.dataEvento) {
            const data = new Date(payload.dataEvento);
            if (Number.isNaN(data.getTime())) {
                const mensagem = 'Informe uma data do evento válida.';
                registrarErroCampo('dataEvento', mensagem);
                erros.push(mensagem);
            }
        }

        return erros;
    }

    function atualizarEstadoAgendamento() {
        if (!agendamentoDiv) {
            return;
        }
        const deveExibir = publicarImediatamenteCheckbox ? !publicarImediatamenteCheckbox.checked : false;
        if (deveExibir) {
            agendamentoDiv.style.display = 'block';
            if (dataAgendamentoInput && !dataAgendamentoInput.value) {
                dataAgendamentoInput.value = camposFormulario.dataPublicacao?.value || '';
            }
        } else {
            agendamentoDiv.style.display = 'none';
            if (dataAgendamentoInput) {
                dataAgendamentoInput.value = '';
                limparErroCampoEspecifico('dataAgendamento');
            }
        }
    }

    function atualizarEstadoCalendario() {
        if (!dataEventoContainer) {
            return;
        }
        const exibir = Boolean(marcarCalendarioCheckbox ? marcarCalendarioCheckbox.checked : false);
        if (exibir) {
            dataEventoContainer.classList.remove('d-none');
            dataEventoContainer.removeAttribute('hidden');
        } else {
            dataEventoContainer.classList.add('d-none');
            dataEventoContainer.setAttribute('hidden', '');
        }
        dataEventoContainer.setAttribute('aria-hidden', exibir ? 'false' : 'true');
        if (marcarCalendarioCheckbox) {
            marcarCalendarioCheckbox.setAttribute('aria-expanded', exibir ? 'true' : 'false');
        }
        if (dataEventoInput) {
            dataEventoInput.required = exibir;
            if (!exibir) {
                dataEventoInput.value = '';
                limparErroCampoEspecifico('dataEvento');
            }
        }
    }

    function normalizarCampoErro(loc) {
        if (!loc) return null;
        if (Array.isArray(loc) && loc.length > 0) {
            return normalizarCampoErro(loc[0]);
        }
        if (typeof loc !== 'string') return null;
        const mapa = {
            data_publicacao: 'dataPublicacao',
            dataPublicacao: 'dataPublicacao',
            data_agendamento: 'dataAgendamento',
            dataAgendamento: 'dataAgendamento',
            marcar_calendario: 'marcarCalendario',
            marcarCalendario: 'marcarCalendario',
            data_evento: 'dataEvento',
            dataEvento: 'dataEvento'
        };
        return mapa[loc] || loc;
    }

    function aplicarErrosServidor(erros) {
        if (!Array.isArray(erros)) return [];
        const mensagens = [];
        erros.forEach(erro => {
            const campo = normalizarCampoErro(erro.loc);
            const mensagem = erro.msg || erro.message || 'Dados inválidos.';
            if (campo && camposFormulario[campo]) {
                registrarErroCampo(campo, mensagem);
            }
            mensagens.push(mensagem);
        });
        return mensagens;
    }

    const inputBusca = document.getElementById('newsAdminSearch');
    const selectStatus = document.getElementById('newsAdminStatus');
    const selectDestaque = document.getElementById('newsAdminDestaque');

    let paginaAtual = 1;
    const porPagina = 10;
    let noticiaParaExcluir = null;

    async function carregarNoticias(page = 1) {
        tabelaBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status" aria-hidden="true"></div>
                    <span class="visually-hidden">Carregando notícias</span>
                </td>
            </tr>`;
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: porPagina.toString(),
            include_inativas: 'true'
        });
        const termo = inputBusca.value.trim();
        if (termo) {
            params.append('busca', termo);
        }
        const status = selectStatus.value;
        if (status === 'ativos') {
            params.append('ativo', 'true');
        } else if (status === 'inativos') {
            params.append('ativo', 'false');
        }
        const destaque = selectDestaque.value;
        if (destaque === 'destaque') {
            params.append('destaque', 'true');
        } else if (destaque === 'comum') {
            params.append('destaque', 'false');
        }
        try {
            const resposta = await chamarAPI(`/noticias?${params.toString()}`);
            const noticias = resposta.items || [];
            totalBadge.textContent = `${resposta.total || noticias.length} registros`;
            if (noticias.length === 0) {
                tabelaBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Nenhuma notícia cadastrada ainda.</td></tr>';
            } else {
                tabelaBody.innerHTML = noticias.map(criarLinhaNoticia).join('');
                tabelaBody.querySelectorAll('[data-acao="editar"]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        const id = Number.parseInt(botao.dataset.id, 10);
                        abrirEdicao(id);
                    });
                });
                tabelaBody.querySelectorAll('[data-acao="excluir"]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        noticiaParaExcluir = Number.parseInt(botao.dataset.id, 10);
                        confirmacaoModal.show();
                    });
                });
            }
            paginaAtual = resposta.page || page;
            renderizarPaginacao(resposta.pages || 1, paginaAtual);
        } catch (error) {
            console.error('Erro ao carregar notícias', error);
            tabelaBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar notícias.</td></tr>';
            tentarRenovarCSRF();
        }
    }

    function criarLinhaNoticia(noticia) {
        const destaqueBadge = noticia.destaque ? '<span class="badge bg-warning text-dark">Destaque</span>' : '<span class="badge bg-light text-dark">Comum</span>';
        const statusBadge = noticia.ativo ? '<span class="badge bg-success">Publicado</span>' : '<span class="badge bg-secondary">Rascunho</span>';
        const dataFormatada = formatarDataTabela(noticia.data_publicacao);
        return `
            <tr>
                <td class="fw-semibold">${escapeHTML(noticia.titulo)}</td>
                <td>${dataFormatada}</td>
                <td>${destaqueBadge}</td>
                <td>${statusBadge}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-2" data-acao="editar" data-id="${noticia.id}" data-bs-noticia-id="${noticia.id}" aria-label="Editar notícia ${escapeHTML(noticia.titulo)}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" data-acao="excluir" data-id="${noticia.id}" aria-label="Excluir notícia ${escapeHTML(noticia.titulo)}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    function renderizarPaginacao(totalPaginas, pagina) {
        paginacaoEl.innerHTML = '';
        if (totalPaginas <= 1) return;
        const criarItem = (label, targetPage, disabled = false, active = false) => `
            <li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${targetPage}">${label}</a>
            </li>
        `;
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Anterior', pagina - 1, pagina <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginacaoEl.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === pagina));
        }
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Próxima', pagina + 1, pagina >= totalPaginas));
        paginacaoEl.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', event => {
                event.preventDefault();
                const alvo = Number.parseInt(link.dataset.page, 10);
                if (!Number.isNaN(alvo) && alvo >= 1 && alvo <= totalPaginas && alvo !== paginaAtual) {
                    paginaAtual = alvo;
                    carregarNoticias(paginaAtual);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    async function abrirEdicao(id) {
        try {
            const noticia = await chamarAPI(`/noticias/${id}?include_inativas=true`);
            preencherFormulario(noticia);
            document.getElementById('noticiaModalLabel').textContent = 'Editar notícia';
            noticiaModal.show();
        } catch (error) {
            console.error('Erro ao buscar notícia', error);
            showToast('Não foi possível carregar os dados da notícia.', 'danger');
        }
    }

    function preencherFormulario(noticia) {
        document.getElementById('noticiaId').value = noticia.id;
        document.getElementById('noticiaTitulo').value = noticia.titulo || '';
        document.getElementById('noticiaResumo').value = noticia.resumo || '';
        document.getElementById('noticiaConteudo').value = noticia.conteudo || '';
        document.getElementById('noticiaAutor').value = noticia.autor || '';
        document.getElementById('noticiaDestaque').checked = Boolean(noticia.destaque);
        if (publicarImediatamenteCheckbox) {
            publicarImediatamenteCheckbox.checked = Boolean(noticia.ativo);
        }
        if (marcarCalendarioCheckbox) {
            marcarCalendarioCheckbox.checked = Boolean(noticia.marcar_calendario);
        }
        if (dataEventoInput) {
            dataEventoInput.value = converterDataParaInputDate(noticia.data_evento);
        }
        const campoDataPublicacao = camposFormulario.dataPublicacao;
        if (campoDataPublicacao) {
            campoDataPublicacao.value = converterDataParaInputLocal(noticia.data_publicacao);
        }
        if (dataAgendamentoInput) {
            if (noticia.ativo) {
                dataAgendamentoInput.value = '';
            } else {
                dataAgendamentoInput.value = converterDataParaInputLocal(noticia.data_publicacao);
            }
        }
        atualizarEstadoAgendamento();
        atualizarEstadoCalendario();
    }

    function limparFormulario() {
        form.reset();
        document.getElementById('noticiaId').value = '';
        document.getElementById('noticiaModalLabel').textContent = 'Nova notícia';
        if (publicarImediatamenteCheckbox) {
            publicarImediatamenteCheckbox.checked = true;
        }
        if (marcarCalendarioCheckbox) {
            marcarCalendarioCheckbox.checked = false;
        }
        if (dataAgendamentoInput) {
            dataAgendamentoInput.value = '';
        }
        if (dataEventoInput) {
            dataEventoInput.value = '';
        }
        if (imagemInput) {
            imagemInput.value = '';
        }
        atualizarEstadoAgendamento();
        atualizarEstadoCalendario();
        limparValidacaoCampos();
    }

    async function salvarNoticia() {
        limparValidacaoCampos();
        const dadosFormulario = new FormData(form);
        const titulo = dadosFormulario.get('titulo')?.toString().trim() || '';
        const resumo = dadosFormulario.get('resumo')?.toString().trim() || '';
        const conteudo = dadosFormulario.get('conteudo')?.toString().trim() || '';
        const autor = dadosFormulario.get('autor')?.toString().trim() || '';
        const dataPublicacaoBruta = dadosFormulario.get('dataPublicacao')?.toString().trim() || '';
        const dataAgendamentoBruta = dadosFormulario.get('dataAgendamento')?.toString().trim() || '';
        let dataEventoBruta = dadosFormulario.get('dataEvento')?.toString().trim() || '';
        const publicarImediatamente = publicarImediatamenteCheckbox ? publicarImediatamenteCheckbox.checked : true;
        const marcarCalendario = marcarCalendarioCheckbox ? marcarCalendarioCheckbox.checked : false;

        if (!marcarCalendario) {
            dataEventoBruta = '';
        }

        const payloadValidacao = {
            titulo,
            resumo,
            conteudo,
            dataPublicacao: dataPublicacaoBruta,
            dataAgendamento: dataAgendamentoBruta,
            publicarImediatamente,
            marcarCalendario,
            dataEvento: dataEventoBruta
        };

        const errosFormulario = validarCamposObrigatorios(payloadValidacao);
        if (errosFormulario.length > 0) {
            showToast(errosFormulario.join(' '), 'warning');
            return;
        }

        const dadosEnvio = new FormData();
        dadosEnvio.append('titulo', titulo);
        dadosEnvio.append('resumo', resumo);
        dadosEnvio.append('conteudo', conteudo);
        dadosEnvio.append('autor', autor);
        dadosEnvio.append('destaque', form.querySelector('#noticiaDestaque').checked ? 'true' : 'false');
        dadosEnvio.append('ativo', publicarImediatamente ? 'true' : 'false');
        dadosEnvio.append('marcarCalendario', marcarCalendario ? 'true' : 'false');

        const arquivoImagem = dadosFormulario.get('imagem');
        if (arquivoImagem instanceof File && arquivoImagem.name) {
            dadosEnvio.append('imagem', arquivoImagem);
        }

        const dataPrincipal = publicarImediatamente ? dataPublicacaoBruta : dataAgendamentoBruta;
        if (dataPrincipal) {
            const data = new Date(dataPrincipal);
            if (!Number.isNaN(data.getTime())) {
                dadosEnvio.append('dataPublicacao', data.toISOString());
            }
        } else if (dataPublicacaoBruta) {
            const data = new Date(dataPublicacaoBruta);
            if (!Number.isNaN(data.getTime())) {
                dadosEnvio.append('dataPublicacao', data.toISOString());
            }
        }

        if (!publicarImediatamente && dataAgendamentoBruta) {
            const data = new Date(dataAgendamentoBruta);
            if (!Number.isNaN(data.getTime())) {
                dadosEnvio.append('dataAgendamento', data.toISOString());
            }
        }

        if (marcarCalendario) {
            if (dataEventoBruta) {
                const dataEvento = new Date(dataEventoBruta);
                if (!Number.isNaN(dataEvento.getTime())) {
                    dadosEnvio.append('dataEvento', dataEvento.toISOString());
                }
            }
        } else {
            dadosEnvio.append('dataEvento', '');
        }

        const noticiaId = document.getElementById('noticiaId').value;
        const metodo = noticiaId ? 'PUT' : 'POST';
        const endpoint = noticiaId ? `/noticias/${noticiaId}` : '/noticias';
        try {
            btnSalvar.disabled = true;
            await chamarAPI(endpoint, metodo, dadosEnvio);
            showToast('Notícia salva com sucesso!', 'success');
            noticiaModal.hide();
            limparFormulario();
            carregarNoticias(paginaAtual);
        } catch (error) {
            console.error('Erro ao salvar notícia', error);
            let mensagem = error?.message || 'Não foi possível salvar a notícia.';
            if (error?.payload?.erros) {
                const mensagensDetalhadas = aplicarErrosServidor(error.payload.erros);
                if (mensagensDetalhadas.length > 0) {
                    mensagem = mensagensDetalhadas.join(' ');
                }
            }
            showToast(mensagem, 'danger');
            tentarRenovarCSRF();
        } finally {
            btnSalvar.disabled = false;
        }
    }

    async function excluirNoticia() {
        if (!noticiaParaExcluir) return;
        try {
            await chamarAPI(`/noticias/${noticiaParaExcluir}`, 'DELETE');
            showToast('Notícia excluída com sucesso.', 'success');
            confirmacaoModal.hide();
            carregarNoticias(paginaAtual);
        } catch (error) {
            console.error('Erro ao excluir notícia', error);
            showToast('Não foi possível excluir a notícia.', 'danger');
            tentarRenovarCSRF();
        } finally {
            noticiaParaExcluir = null;
        }
    }

    async function exportarNoticias() {
        try {
            const resposta = await chamarAPI('/noticias?include_inativas=true&per_page=500');
            const itens = resposta.items || [];
            if (itens.length === 0) {
                showToast('Nenhuma notícia para exportar.', 'info');
                return;
            }
            const cabecalho = ['id', 'titulo', 'resumo', 'conteudo', 'autor', 'imagem_url', 'destaque', 'ativo', 'marcar_calendario', 'data_publicacao', 'data_evento'];
            const linhas = [cabecalho.join(';')];
            itens.forEach(item => {
                const linha = [
                    item.id,
                    protegerCSV(item.titulo),
                    protegerCSV(item.resumo),
                    protegerCSV(stripHTML(item.conteudo)),
                    protegerCSV(item.autor || ''),
                    protegerCSV(item.imagem_url || ''),
                    item.destaque ? '1' : '0',
                    item.ativo ? '1' : '0',
                    item.marcar_calendario ? '1' : '0',
                    item.data_publicacao || '',
                    item.data_evento || ''
                ];
                linhas.push(linha.join(';'));
            });
            const blob = new Blob([linhas.join('\n')], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'noticias.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erro ao exportar notícias', error);
            showToast('Falha ao exportar as notícias.', 'danger');
            tentarRenovarCSRF();
        }
    }

    function protegerCSV(texto = '') {
        const sanitized = texto.replaceAll('"', '""');
        return `"${sanitized}"`;
    }

    function stripHTML(conteudo = '') {
        const div = document.createElement('div');
        div.innerHTML = sanitizeHTML?.(conteudo) || conteudo;
        return div.textContent || '';
    }

    function converterDataParaInputLocal(dataISO) {
        if (!dataISO) return '';
        try {
            const data = new Date(dataISO);
            if (Number.isNaN(data.getTime())) {
                return '';
            }
            const local = new Date(data.getTime() - data.getTimezoneOffset() * 60000);
            return local.toISOString().slice(0, 16);
        } catch (error) {
            return '';
        }
    }

    function converterDataParaInputDate(dataISO) {
        if (!dataISO) return '';
        try {
            const data = new Date(dataISO);
            if (Number.isNaN(data.getTime())) {
                return '';
            }
            const ano = data.getUTCFullYear();
            const mes = String(data.getUTCMonth() + 1).padStart(2, '0');
            const dia = String(data.getUTCDate()).padStart(2, '0');
            return `${ano}-${mes}-${dia}`;
        } catch (error) {
            return '';
        }
    }

    function obterDataAtualFormatada() {
        const agora = new Date();
        const ano = agora.getFullYear();
        const mes = String(agora.getMonth() + 1).padStart(2, '0');
        const dia = String(agora.getDate()).padStart(2, '0');
        const horas = String(agora.getHours()).padStart(2, '0');
        const minutos = String(agora.getMinutes()).padStart(2, '0');
        return `${ano}-${mes}-${dia}T${horas}:${minutos}`;
    }

    function formatarDataTabela(dataISO) {
        if (!dataISO) return '<span class="text-muted">Sem data</span>';
        try {
            const data = new Date(dataISO);
            return data.toLocaleString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch (error) {
            return '<span class="text-muted">Sem data</span>';
        }
    }

    function escapeHTML(texto = '') {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    function tentarRenovarCSRF() {
        if (typeof obterCSRFToken === 'function') {
            obterCSRFToken(true).catch(() => {});
        }
    }

    if (publicarImediatamenteCheckbox) {
        publicarImediatamenteCheckbox.addEventListener('change', atualizarEstadoAgendamento);
    }

    if (marcarCalendarioCheckbox) {
        marcarCalendarioCheckbox.addEventListener('change', atualizarEstadoCalendario);
        marcarCalendarioCheckbox.addEventListener('input', atualizarEstadoCalendario);
    }

    modalEl.addEventListener('show.bs.modal', () => {
        const idAtual = document.getElementById('noticiaId').value;
        if (idAtual) {
            return;
        }
        const campoDataPublicacao = camposFormulario.dataPublicacao;
        if (campoDataPublicacao) {
            campoDataPublicacao.value = obterDataAtualFormatada();
        }
        if (publicarImediatamenteCheckbox) {
            publicarImediatamenteCheckbox.checked = true;
        }
        atualizarEstadoAgendamento();
        atualizarEstadoCalendario();
    });

    modalEl.addEventListener('hidden.bs.modal', limparFormulario);
    btnSalvar.addEventListener('click', salvarNoticia);
    searchForm.addEventListener('submit', event => {
        event.preventDefault();
        paginaAtual = 1;
        carregarNoticias(paginaAtual);
    });
    resetButton.addEventListener('click', () => {
        inputBusca.value = '';
        selectStatus.value = 'todos';
        selectDestaque.value = 'todos';
        paginaAtual = 1;
        carregarNoticias(paginaAtual);
    });
    document.getElementById('btnConfirmarExclusao').addEventListener('click', excluirNoticia);
    exportarButton.addEventListener('click', exportarNoticias);

    atualizarEstadoAgendamento();
    atualizarEstadoCalendario();
    carregarNoticias(paginaAtual);
});
