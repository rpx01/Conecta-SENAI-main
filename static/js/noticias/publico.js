/* global chamarAPI, showToast, getUsuarioLogado, sanitizeHTML */

document.addEventListener('DOMContentLoaded', () => {
    const heroSection = document.querySelector('.news-hero');
    const heroTitleEl = document.getElementById('newsHeroTitle');
    const heroSummaryEl = document.getElementById('newsHeroSummary');
    const heroDateEl = document.getElementById('newsHeroDate');
    const heroButton = document.getElementById('newsHeroReadMore');
    const heroContainer = heroSection?.querySelector('.container');
    let heroControlsWrapper = null;
    let heroPrevButton = null;
    let heroNextButton = null;
    let heroProgressBar = null;

    if (heroContainer) {
        heroControlsWrapper = document.createElement('div');
        heroControlsWrapper.className = 'd-flex align-items-center gap-2 flex-wrap mt-4';
        heroControlsWrapper.setAttribute('role', 'group');
        heroControlsWrapper.setAttribute('aria-label', 'Controles do destaque');

        heroPrevButton = document.createElement('button');
        heroPrevButton.type = 'button';
        heroPrevButton.className = 'btn btn-outline-light btn-sm';
        heroPrevButton.setAttribute('aria-label', 'Mostrar destaque anterior');
        heroPrevButton.innerHTML = '<i class="bi bi-chevron-left" aria-hidden="true"></i><span class="visually-hidden">Anterior</span>';
        heroControlsWrapper.appendChild(heroPrevButton);

        const progressWrapper = document.createElement('div');
        progressWrapper.className = 'flex-grow-1 position-relative overflow-hidden';
        progressWrapper.style.height = '4px';
        progressWrapper.style.background = 'rgba(255, 255, 255, 0.35)';
        progressWrapper.style.borderRadius = '999px';
        progressWrapper.setAttribute('aria-hidden', 'true');

        heroProgressBar = document.createElement('span');
        heroProgressBar.className = 'position-absolute top-0 start-0 h-100 bg-white';
        heroProgressBar.style.width = '0%';
        heroProgressBar.style.borderRadius = 'inherit';
        heroProgressBar.style.transition = 'width 0.2s linear';
        progressWrapper.appendChild(heroProgressBar);
        heroControlsWrapper.appendChild(progressWrapper);

        heroNextButton = document.createElement('button');
        heroNextButton.type = 'button';
        heroNextButton.className = 'btn btn-outline-light btn-sm';
        heroNextButton.setAttribute('aria-label', 'Mostrar próximo destaque');
        heroNextButton.innerHTML = '<i class="bi bi-chevron-right" aria-hidden="true"></i><span class="visually-hidden">Próximo</span>';
        heroControlsWrapper.appendChild(heroNextButton);

        heroContainer.appendChild(heroControlsWrapper);
    }

    const highlightsContainer = document.getElementById('newsHighlights');
    const highlightsEmptyState = document.getElementById('newsHighlightsEmpty');
    const listContainer = document.getElementById('newsGrid');
    const listEmptyState = document.getElementById('newsListEmpty');
    const paginationContainer = document.getElementById('newsPagination');
    const calendarList = document.getElementById('newsCalendarList');
    const calendarEmptyState = document.getElementById('newsCalendarEmpty');
    const searchForm = document.getElementById('newsSearchForm');
    const searchInput = document.getElementById('newsSearchInput');
    const refreshButton = document.getElementById('refreshNewsBtn');
    const searchSubmitButton = searchForm?.querySelector('button[type="submit"]');

    const modalTitle = document.getElementById('newsModalTitle');
    const modalMeta = document.getElementById('newsModalMeta');
    const modalImage = document.getElementById('newsModalImage');
    const modalContent = document.getElementById('newsModalContent');
    const modalElement = document.getElementById('newsModal');
    const modalInstance = modalElement && window.bootstrap
        ? window.bootstrap.Modal.getOrCreateInstance(modalElement)
        : null;

    const managementButton = document.querySelector('[data-testid="management-button"]');
    const systemSelectionButton = document.querySelector('[data-testid="system-selection-button"]');
    const userProfileButton = document.querySelector('[data-testid="user-profile-button"]');
    const userMenu = document.querySelector('.user-menu');

    let paginaAtual = 1;
    const itensPorPagina = 6;
    let termoBusca = '';
    let destaqueAtual = null;
    let destaquesHero = [];
    let indiceDestaqueAtual = 0;
    let intervaloRotacaoId = null;
    let progressoRotacaoId = null;
    let animacaoHeroAtual = null;
    const TEMPO_ROTACAO_MS = 10000;
    let noticiasCalendario = new Map();
    const CALENDAR_DATE_KEY = '__dataEventoDate';

    const usuario = getUsuarioLogado?.();
    const token = window.localStorage?.getItem('token');
    const isVisitante = !usuario && !token;

    if (usuario) {
        const userNameEl = document.getElementById('userName');
        if (userNameEl) {
            userNameEl.textContent = usuario.nome;
        }
        const loginLink = document.querySelector('a.dropdown-item[href="/admin/login.html"]');
        if (loginLink) {
            loginLink.classList.add('d-none');
        }
    }

    if (isVisitante) {
        aplicarRestricoesParaVisitante();
    } else {
        removerRestricoesParaVisitante();
    }

    heroButton?.addEventListener('click', () => {
        if (destaqueAtual) {
            abrirModal(destaqueAtual);
        }
    });

    if (!isVisitante) {
        refreshButton?.addEventListener('click', handleRefreshClick);
        searchForm?.addEventListener('submit', handleSearchSubmit);
    }

    function handleRefreshClick() {
        carregarDestaques();
        carregarLista(paginaAtual);
        carregarCalendario();
    }

    function handleSearchSubmit(event) {
        event.preventDefault();
        termoBusca = searchInput?.value.trim() ?? '';
        paginaAtual = 1;
        carregarLista(paginaAtual);
    }

    async function carregarDestaques() {
        setAriaBusy(highlightsContainer, true);
        pararRotacaoDestaques();
        destaquesHero = [];
        try {
            const resposta = await chamarAPI(`/noticias?destaque=true&per_page=5`);
            const noticias = resposta.items || [];
            if (noticias.length > 0) {
                destaquesHero = noticias;
                indiceDestaqueAtual = 0;
                atualizarHeroEDestaques();
                reiniciarRotacaoDestaques();
            } else {
                destaqueAtual = null;
                destaquesHero = [];
                pararRotacaoDestaques();
                atualizarHero();
                renderizarHighlights([]);
                mostrarEstadoVazioHighlights();
            }
        } catch (error) {
            console.error('Erro ao carregar destaques', error);
            showToast('Não foi possível carregar os destaques de notícias.', 'danger');
            destaqueAtual = null;
            destaquesHero = [];
            pararRotacaoDestaques();
            atualizarHero();
            renderizarHighlights([]);
            mostrarEstadoVazioHighlights();
            tentarRenovarCSRF();
        } finally {
            setAriaBusy(highlightsContainer, false);
        }
    }

    async function carregarLista(pagina = 1) {
        setAriaBusy(listContainer, true);
        try {
            const params = new URLSearchParams({
                page: pagina.toString(),
                per_page: itensPorPagina.toString()
            });
            if (termoBusca) {
                params.append('busca', termoBusca);
            }
            const resposta = await chamarAPI(`/noticias?${params.toString()}`);
            const noticias = resposta.items || [];
            if (noticias.length === 0) {
                listContainer.innerHTML = '';
                listEmptyState.textContent = 'Nenhuma notícia cadastrada ainda.';
                listEmptyState.classList.remove('visually-hidden');
            } else {
                listEmptyState.classList.add('visually-hidden');
                listContainer.innerHTML = noticias.map(criarCardNoticia).join('');
                listContainer.querySelectorAll('[data-news-id]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        const id = Number.parseInt(botao.getAttribute('data-news-id'), 10);
                        const noticia = noticias.find(item => item.id === id);
                        if (noticia) {
                            abrirModal(noticia);
                        }
                    });
                });
            }
            paginaAtual = resposta.page || pagina;
            renderizarPaginacao(resposta.pages || 1, paginaAtual);
        } catch (error) {
            console.error('Erro ao carregar notícias', error);
            showToast('Erro ao carregar notícias. Tente novamente em instantes.', 'danger');
            renderizarPlaceholdersLista();
            tentarRenovarCSRF();
        } finally {
            setAriaBusy(listContainer, false);
        }
    }

    async function carregarCalendario() {
        if (!calendarList) {
            return;
        }

        setAriaBusy(calendarList, true);
        calendarList.innerHTML = '';
        noticiasCalendario = new Map();

        try {
            const params = new URLSearchParams({
                per_page: '100',
                marcar_calendario: 'true'
            });
            const resposta = await chamarAPI(`/noticias?${params.toString()}`);
            const noticias = Array.isArray(resposta.items) ? resposta.items : [];
            const eventosValidos = noticias
                .map(noticia => {
                    const dataEventoNormalizada = normalizarDataISO(noticia.data_evento);
                    if (!dataEventoNormalizada) {
                        return null;
                    }
                    const noticiaComDataNormalizada = {
                        ...noticia,
                        [CALENDAR_DATE_KEY]: dataEventoNormalizada
                    };
                    return {
                        noticia: noticiaComDataNormalizada,
                        dataEvento: dataEventoNormalizada
                    };
                })
                .filter(item => item !== null)
                .sort((a, b) => a.dataEvento - b.dataEvento);

            noticiasCalendario = new Map(
                eventosValidos.map(item => [item.noticia.id, item.noticia])
            );

            const agora = new Date();
            const mesAtual = agora.getMonth();
            const anoAtual = agora.getFullYear();
            const inicioMesAtual = new Date(anoAtual, mesAtual, 1);

            const filtrarPorMesAno = (ano, mes) =>
                eventosValidos.filter(
                    item =>
                        item.dataEvento.getMonth() === mes &&
                        item.dataEvento.getFullYear() === ano
                );

            let eventosDoMes = filtrarPorMesAno(anoAtual, mesAtual);

            if (eventosDoMes.length === 0 && eventosValidos.length > 0) {
                const proximoEvento = eventosValidos.find(
                    item => item.dataEvento >= inicioMesAtual
                );

                if (proximoEvento) {
                    const anoAlvo = proximoEvento.dataEvento.getFullYear();
                    const mesAlvo = proximoEvento.dataEvento.getMonth();
                    eventosDoMes = filtrarPorMesAno(anoAlvo, mesAlvo);
                } else {
                    const ultimoEvento = eventosValidos[eventosValidos.length - 1];
                    const anoAlvo = ultimoEvento.dataEvento.getFullYear();
                    const mesAlvo = ultimoEvento.dataEvento.getMonth();
                    eventosDoMes = filtrarPorMesAno(anoAlvo, mesAlvo);
                }
            }

            renderizarCalendario(eventosDoMes.map(item => item.noticia));
        } catch (error) {
            console.error('Erro ao carregar calendário de notícias', error);
            showToast('Não foi possível carregar os eventos do calendário.', 'danger');
            calendarList.innerHTML = '';
            mostrarEstadoVazioCalendario();
            tentarRenovarCSRF();
        } finally {
            setAriaBusy(calendarList, false);
        }
    }

    async function fetchNoticiasDoCalendario(ano, mes) {
        const params = new URLSearchParams({
            ano: String(ano),
            mes: String(mes),
            per_page: '100',
            marcar_calendario: 'true'
        });

        const resposta = await chamarAPI(`/noticias?${params.toString()}`);
        if (!resposta) {
            return [];
        }

        const { items } = resposta;
        return Array.isArray(items) ? items : [];
    }

    async function popularCalendario(date) {
        if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
            return;
        }

        const calendario = document.querySelector('[data-calendario]');
        if (!calendario) {
            return;
        }

        calendario.querySelectorAll('[data-dia]').forEach(diaElement => {
            diaElement.classList.remove('evento');
            diaElement.querySelectorAll('.evento-marcador').forEach(marcador => marcador.remove());
        });

        try {
            const noticiasDoMes = await fetchNoticiasDoCalendario(date.getFullYear(), date.getMonth() + 1);

            noticiasDoMes.forEach((noticia) => {
                // A data_evento vem como 'YYYY-MM-DDTHH:mm:ss'
                // Precisamos tratar para evitar problemas de fuso horário
                const [dataParte] = noticia.data_evento.split("T");
                const [ano, mes, dia] = dataParte.split("-");
                const dataEvento = new Date(ano, mes - 1, dia);

                const diaDoEvento = dataEvento.getDate();
                const diaElement = document.querySelector(`[data-dia="${diaDoEvento}"]`);

                if (diaElement && !diaElement.querySelector(".evento-marcador")) {
                    diaElement.classList.add("evento");
                    const link = document.createElement("a");
                    link.href = `#noticia-${noticia.id}`;
                    link.classList.add("evento-marcador");
                    link.setAttribute("aria-label", `Evento: ${noticia.titulo}`);
                    diaElement.appendChild(link);
                }
            });
        } catch (error) {
            console.error('Erro ao popular calendário de notícias', error);
        }
    }

    function obterUrlImagem(noticia) {
        if (!noticia) {
            return null;
        }
        if (noticia.imagem_url) {
            return noticia.imagem_url;
        }
        if (noticia.imagem && noticia.imagem.url) {
            return noticia.imagem.url;
        }
        return null;
    }

    function atualizarHero(noticia) {
        if (!noticia) {
            heroTitleEl.textContent = 'Nenhum destaque disponível por enquanto';
            heroSummaryEl.textContent = 'Volte em breve para conferir as novidades da unidade.';
            heroDateEl.textContent = '';
            heroButton.disabled = true;
            heroSection.style.backgroundImage = '';
            return;
        }
        heroTitleEl.textContent = noticia.titulo;
        heroSummaryEl.textContent = noticia.resumo;
        heroDateEl.textContent = formatarDataHumana(noticia.data_publicacao);
        heroDateEl.classList.remove('visually-hidden');
        heroButton.disabled = false;
        const urlImagem = obterUrlImagem(noticia);
        if (urlImagem) {
            heroSection.style.backgroundImage = `linear-gradient(135deg, rgba(22, 65, 148, 0.75), rgba(0, 139, 210, 0.65)), url('${encodeURI(urlImagem)}')`;
            heroSection.style.backgroundSize = 'cover';
            heroSection.style.backgroundPosition = 'center';
        } else {
            heroSection.style.backgroundImage = 'linear-gradient(135deg, rgba(22,65,148,0.95), rgba(0,139,210,0.9))';
        }
    }

    function renderizarHighlights(noticias) {
        if (!noticias || noticias.length === 0) {
            highlightsContainer.innerHTML = '';
            highlightsEmptyState.classList.remove('visually-hidden');
            return;
        }
        highlightsEmptyState.classList.add('visually-hidden');
        highlightsContainer.innerHTML = noticias.map(criarHighlightNoticia).join('');
        highlightsContainer.querySelectorAll('[data-news-id]').forEach(botao => {
            botao.addEventListener('click', event => {
                event.preventDefault();
                const id = Number.parseInt(botao.getAttribute('data-news-id'), 10);
                const noticia = noticias.find(item => item.id === id);
                if (noticia) {
                    abrirModal(noticia);
                }
            });
        });
    }

    function renderizarCalendario(noticias) {
        if (!calendarList) {
            return;
        }

        if (!Array.isArray(noticias) || noticias.length === 0) {
            calendarList.innerHTML = '';
            mostrarEstadoVazioCalendario();
            return;
        }

        ocultarEstadoVazioCalendario();
        calendarList.innerHTML = noticias.map(criarItemCalendario).join('');
        calendarList.querySelectorAll('[data-calendar-news-id]').forEach(botao => {
            botao.addEventListener('click', () => {
                const id = Number.parseInt(botao.getAttribute('data-calendar-news-id'), 10);
                if (Number.isNaN(id)) {
                    return;
                }
                const noticia = noticiasCalendario.get(id);
                if (noticia) {
                    abrirModal(noticia);
                }
            });
        });
    }

    function criarHighlightNoticia(noticia) {
        const resumo = noticia.resumo ?? '';
        return `
            <article class="news-highlight" role="listitem" tabindex="0">
                <p class="news-highlight__date mb-1">${formatarDataHumana(noticia.data_publicacao)}</p>
                <h3 class="news-highlight__title">${escapeHTML(noticia.titulo)}</h3>
                <p class="news-highlight__excerpt">${escapeHTML(resumo)}</p>
                <button class="btn btn-link p-0 mt-2" data-news-id="${noticia.id}" aria-label="Ler notícia ${escapeHTML(noticia.titulo)}" data-bs-toggle="modal" data-bs-target="#newsModal">
                    Ler mais <i class="bi bi-arrow-right-short"></i>
                </button>
            </article>
        `;
    }

    function criarItemCalendario(noticia) {
        const dataRotulo = formatarDataCalendario(
            noticia.data_evento,
            noticia[CALENDAR_DATE_KEY]
        );
        const dataAttr = noticia.data_evento ? escapeHTML(noticia.data_evento) : '';
        return `
            <li class="news-calendar__item d-flex align-items-start gap-2" role="listitem">
                <time class="news-calendar__date" datetime="${dataAttr}">${dataRotulo}</time>
                <button class="btn btn-link p-0 text-start news-calendar__link" type="button" data-calendar-news-id="${noticia.id}" aria-label="Ver detalhes do evento ${escapeHTML(noticia.titulo)}" data-bs-toggle="modal" data-bs-target="#newsModal">
                    ${escapeHTML(noticia.titulo)}
                </button>
            </li>
        `;
    }

    function criarCardNoticia(noticia) {
        const urlImagem = obterUrlImagem(noticia);
        const imagem = urlImagem ? `<img class="news-card__image" src="${encodeURI(urlImagem)}" alt="Imagem ilustrativa da notícia">` : '<div class="news-card__image" role="presentation"></div>';
        return `
            <article class="news-card" role="listitem">
                ${imagem}
                <div class="news-card__body">
                    <time class="news-card__date" datetime="${escapeHTML(noticia.data_publicacao || '')}">${formatarDataHumana(noticia.data_publicacao)}</time>
                    <h3 class="news-card__title">${escapeHTML(noticia.titulo)}</h3>
                    <p class="news-card__summary">${escapeHTML(noticia.resumo ?? '')}</p>
                    <div class="news-card__actions">
                        <button class="btn btn-outline-primary" type="button" data-news-id="${noticia.id}" aria-label="Abrir notícia ${escapeHTML(noticia.titulo)}" data-bs-toggle="modal" data-bs-target="#newsModal">
                            <i class="bi bi-journal-text me-1"></i> Ler notícia
                        </button>
                    </div>
                </div>
            </article>
        `;
    }

    function renderizarPaginacao(totalPaginas, pagina) {
        paginationContainer.innerHTML = '';
        if (totalPaginas <= 1) return;
        const criarItem = (label, targetPage, disabled = false, active = false) => `
            <li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${targetPage}">${label}</a>
            </li>
        `;
        paginationContainer.insertAdjacentHTML('beforeend', criarItem('Anterior', pagina - 1, pagina <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginationContainer.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === pagina));
        }
        paginationContainer.insertAdjacentHTML('beforeend', criarItem('Próxima', pagina + 1, pagina >= totalPaginas));
        const links = paginationContainer.querySelectorAll('a[data-page]');
        if (isVisitante) {
            links.forEach(link => {
                link.setAttribute('aria-disabled', 'true');
                link.setAttribute('tabindex', '-1');
                link.classList.add('disabled');
                const item = link.closest('li');
                item?.classList.add('disabled');
                link.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                });
            });
            return;
        }

        links.forEach(link => {
            link.addEventListener('click', event => {
                event.preventDefault();
                const alvo = Number.parseInt(link.getAttribute('data-page'), 10);
                if (!Number.isNaN(alvo) && alvo >= 1 && alvo <= totalPaginas && alvo !== paginaAtual) {
                    paginaAtual = alvo;
                    carregarLista(paginaAtual);
                    window.scrollTo({ top: document.getElementById('newsListHeading').offsetTop - 80, behavior: 'smooth' });
                }
            });
        });
    }

    function abrirModal(noticia) {
        modalTitle.textContent = noticia.titulo;
        const dataPublicacao = formatarDataHumana(noticia.data_publicacao);
        const autor = noticia.autor ? ` | ${escapeHTML(noticia.autor)}` : '';
        modalMeta.textContent = `${dataPublicacao}${autor}`;
        const urlImagem = obterUrlImagem(noticia);
        if (urlImagem) {
            modalImage.src = urlImagem;
            modalImage.alt = `Imagem ilustrativa da notícia ${noticia.titulo}`;
            modalImage.classList.remove('d-none');
        } else {
            modalImage.classList.add('d-none');
            modalImage.removeAttribute('src');
        }
        modalContent.innerHTML = formatarConteudoNoticia(noticia.conteudo ?? '');
        modalInstance?.show();
    }

    function formatarDataHumana(dataISO) {
        if (!dataISO) return 'Data não informada';
        try {
            const data = new Date(dataISO);
            return data.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
        } catch (error) {
            return 'Data não informada';
        }
    }

    function formatarDataCalendario(dataISO, dataNormalizada) {
        const data = dataNormalizada instanceof Date && !Number.isNaN(dataNormalizada.getTime())
            ? dataNormalizada
            : normalizarDataISO(dataISO);
        if (!data) {
            return 'Data não informada';
        }
        const dia = data.toLocaleDateString('pt-BR', { day: '2-digit' });
        const formatter = new Intl.DateTimeFormat('pt-BR', { month: 'short' });
        let mes = formatter.format(data);
        mes = mes.replace('.', '');
        if (mes.length > 0) {
            mes = mes.charAt(0).toUpperCase() + mes.slice(1);
        }
        return `${dia} ${mes}`;
    }

    function normalizarDataISO(dataISO) {
        if (!dataISO) {
            return null;
        }

        const normalizarParaDate = valor => {
            if (valor instanceof Date) {
                return Number.isNaN(valor.getTime()) ? null : valor;
            }
            if (typeof valor === 'number' && Number.isFinite(valor)) {
                const dataNumero = new Date(valor);
                return Number.isNaN(dataNumero.getTime()) ? null : dataNumero;
            }
            if (typeof valor !== 'string') {
                return null;
            }

            let texto = valor.trim();
            if (!texto) {
                return null;
            }

            // Normaliza separador de data/hora e timezone
            texto = texto.replace(' ', 'T');
            texto = texto.replace(/([+-]\d{2})(\d{2})$/, '$1:$2');

            const possuiHorario = /T\d{2}:\d{2}/.test(texto);
            const possuiTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(texto);

            if (!possuiHorario) {
                texto = `${texto}T00:00:00Z`;
            } else if (!possuiTimezone) {
                texto = `${texto}Z`;
            }

            const data = new Date(texto);
            if (Number.isNaN(data.getTime())) {
                return null;
            }
            return data;
        };

        const data = normalizarParaDate(dataISO);
        if (!data) {
            return null;
        }

        return new Date(
            data.getUTCFullYear(),
            data.getUTCMonth(),
            data.getUTCDate()
        );
    }

    function setAriaBusy(elemento, ocupado) {
        if (!elemento) return;
        elemento.setAttribute('aria-busy', ocupado ? 'true' : 'false');
    }

    function renderizarPlaceholdersLista() {
        const skeleton = `
            <article class="news-card placeholder-glow" aria-hidden="true">
                <div class="news-card__image placeholder"></div>
                <div class="news-card__body">
                    <p class="news-card__date placeholder col-6"></p>
                    <h3 class="news-card__title placeholder col-8"></h3>
                    <p class="news-card__summary placeholder col-10"></p>
                    <div class="news-card__actions mt-3">
                        <span class="btn btn-outline-primary disabled placeholder col-5"></span>
                    </div>
                </div>
            </article>
        `;
        listEmptyState.classList.add('visually-hidden');
        listContainer.innerHTML = skeleton.repeat(3);
    }

    function mostrarEstadoVazioHighlights() {
        highlightsContainer.innerHTML = '';
        highlightsEmptyState.classList.remove('visually-hidden');
    }

    function mostrarEstadoVazioCalendario() {
        calendarEmptyState?.classList.remove('visually-hidden');
    }

    function ocultarEstadoVazioCalendario() {
        calendarEmptyState?.classList.add('visually-hidden');
    }

    function atualizarHeroEDestaques({ animarHero = false } = {}) {
        destaqueAtual = destaquesHero[indiceDestaqueAtual] ?? null;
        const atualizarConteudo = () => {
            if (destaqueAtual) {
                atualizarHero(destaqueAtual);
                const demaisDestaques = destaquesHero.filter((_, index) => index !== indiceDestaqueAtual);
                renderizarHighlights(demaisDestaques);
            } else {
                atualizarHero();
                renderizarHighlights([]);
            }
            atualizarEstadoControlesHero();
        };

        if (animarHero && destaqueAtual) {
            animarTransicaoHero(atualizarConteudo);
        } else {
            atualizarConteudo();
        }
    }

    function iniciarRotacaoDestaques() {
        pararRotacaoDestaques();
        if (destaquesHero.length <= 1) {
            pararProgressoRotacao();
            return;
        }
        reiniciarProgressoRotacao();
        intervaloRotacaoId = window.setInterval(() => {
            avancarDestaque(true);
        }, TEMPO_ROTACAO_MS);
    }

    function pararRotacaoDestaques() {
        if (intervaloRotacaoId) {
            window.clearInterval(intervaloRotacaoId);
            intervaloRotacaoId = null;
        }
        pararProgressoRotacao();
    }

    function reiniciarRotacaoDestaques() {
        const deveRotacionar = destaquesHero.length > 1;
        pararRotacaoDestaques();
        if (deveRotacionar) {
            iniciarRotacaoDestaques();
        } else {
            atualizarEstadoControlesHero();
        }
    }

    function avancarDestaque(animar = true) {
        if (destaquesHero.length === 0) {
            return;
        }
        indiceDestaqueAtual = (indiceDestaqueAtual + 1) % destaquesHero.length;
        atualizarHeroEDestaques({ animarHero: animar });
        reiniciarProgressoRotacao();
    }

    function retrocederDestaque(animar = true) {
        if (destaquesHero.length === 0) {
            return;
        }
        indiceDestaqueAtual = (indiceDestaqueAtual - 1 + destaquesHero.length) % destaquesHero.length;
        atualizarHeroEDestaques({ animarHero: animar });
        reiniciarProgressoRotacao();
    }

    function atualizarEstadoControlesHero() {
        if (!heroControlsWrapper) {
            return;
        }
        const possuiDestaques = destaquesHero.length > 0;
        heroControlsWrapper.classList.toggle('visually-hidden', !possuiDestaques);
        const unicoDestaque = destaquesHero.length <= 1;
        if (heroPrevButton) {
            heroPrevButton.disabled = unicoDestaque;
        }
        if (heroNextButton) {
            heroNextButton.disabled = unicoDestaque;
        }
        if (!possuiDestaques) {
            atualizarBarraProgresso(0);
        }
    }

    function podeAnimarHero() {
        return Boolean(heroSection && typeof heroSection.animate === 'function');
    }

    function animarTransicaoHero(callback) {
        if (!podeAnimarHero()) {
            callback?.();
            return;
        }

        if (animacaoHeroAtual) {
            animacaoHeroAtual.cancel();
        }

        const fadeOut = heroSection.animate(
            [
                { opacity: 1, transform: 'translateY(0)' },
                { opacity: 0, transform: 'translateY(16px)' }
            ],
            {
                duration: 280,
                easing: 'ease',
                fill: 'forwards'
            }
        );
        animacaoHeroAtual = fadeOut;

        const aoFinalizarFadeOut = () => {
            callback?.();
            const fadeIn = heroSection.animate(
                [
                    { opacity: 0, transform: 'translateY(-16px)' },
                    { opacity: 1, transform: 'translateY(0)' }
                ],
                {
                    duration: 280,
                    easing: 'ease',
                    fill: 'forwards'
                }
            );
            animacaoHeroAtual = fadeIn;
            fadeIn.addEventListener('finish', () => {
                animacaoHeroAtual = null;
            }, { once: true });
            fadeIn.addEventListener('cancel', () => {
                animacaoHeroAtual = null;
            }, { once: true });
        };

        fadeOut.addEventListener('finish', aoFinalizarFadeOut, { once: true });
        fadeOut.addEventListener('cancel', () => {
            animacaoHeroAtual = null;
            callback?.();
        }, { once: true });
    }

    function iniciarProgressoRotacao() {
        pararProgressoRotacao();
        if (!heroProgressBar || destaquesHero.length <= 1) {
            atualizarBarraProgresso(0);
            return;
        }
        atualizarBarraProgresso(0);
        let tempoDecorrido = 0;
        const passoMs = 80;
        progressoRotacaoId = window.setInterval(() => {
            tempoDecorrido += passoMs;
            const percentual = Math.min((tempoDecorrido / TEMPO_ROTACAO_MS) * 100, 100);
            atualizarBarraProgresso(percentual);
            if (percentual >= 100) {
                pararProgressoRotacao();
            }
        }, passoMs);
    }

    function pararProgressoRotacao() {
        if (progressoRotacaoId) {
            window.clearInterval(progressoRotacaoId);
            progressoRotacaoId = null;
        }
    }

    function reiniciarProgressoRotacao() {
        iniciarProgressoRotacao();
    }

    function atualizarBarraProgresso(percentual) {
        if (!heroProgressBar) {
            return;
        }
        const valorNormalizado = Math.max(0, Math.min(100, percentual));
        heroProgressBar.style.width = `${valorNormalizado}%`;
    }

    function tentarRenovarCSRF() {
        if (typeof obterCSRFToken === 'function') {
            obterCSRFToken(true).catch(() => {});
        }
    }

    function formatarConteudoNoticia(conteudo = '') {
        if (typeof conteudo !== 'string') {
            return '';
        }
        const textoNormalizado = conteudo.replace(/\r\n?/g, '\n');
        const textoEscapado = escapeHTML(textoNormalizado);
        const textoComLinks = transformarUrlsEmLinks(textoEscapado);
        const textoComQuebras = textoComLinks.replace(/\n/g, '<br>');
        return sanitizeHTML?.(textoComQuebras) || textoComQuebras;
    }

    function transformarUrlsEmLinks(texto = '') {
        const urlRegex = /((https?:\/\/|www\.)[^\s<]+)/gi;
        return texto.replace(urlRegex, urlOriginal => {
            const possuiProtocolo = /^https?:\/\//i.test(urlOriginal);
            const href = possuiProtocolo ? urlOriginal : `https://${urlOriginal}`;
            const hrefSeguro = escapeHTML(href);
            return `<a href="${hrefSeguro}" target="_blank" rel="noopener noreferrer">${urlOriginal}</a>`;
        });
    }

    function escapeHTML(texto = '') {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    function aplicarRestricoesParaVisitante() {
        if (managementButton) {
            managementButton.style.display = 'none';
            managementButton.setAttribute('aria-hidden', 'true');
        }

        if (systemSelectionButton) {
            systemSelectionButton.style.pointerEvents = 'none';
            systemSelectionButton.style.opacity = '0.6';
            systemSelectionButton.style.cursor = 'not-allowed';
            systemSelectionButton.setAttribute('aria-disabled', 'true');
            systemSelectionButton.setAttribute('tabindex', '-1');
        }

        if (userProfileButton) {
            userProfileButton.style.pointerEvents = 'none';
            userProfileButton.style.cursor = 'not-allowed';
            userProfileButton.setAttribute('aria-disabled', 'true');
            userProfileButton.setAttribute('tabindex', '-1');
            userProfileButton.classList.add('disabled');
        }

        if (userMenu) {
            userMenu.style.pointerEvents = 'none';
            userMenu.style.opacity = '0.6';
        }

        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.setAttribute('aria-disabled', 'true');
            refreshButton.classList.add('d-none');
            refreshButton.addEventListener('click', event => {
                event.preventDefault();
                event.stopPropagation();
            });
        }

        if (searchForm) {
            searchForm.setAttribute('aria-disabled', 'true');
            searchForm.classList.add('d-none');
            searchForm.addEventListener('submit', event => {
                event.preventDefault();
                event.stopPropagation();
            });
        }

        if (searchInput) {
            searchInput.value = '';
            searchInput.disabled = true;
            searchInput.setAttribute('aria-disabled', 'true');
        }

        if (searchSubmitButton) {
            searchSubmitButton.disabled = true;
            searchSubmitButton.setAttribute('aria-disabled', 'true');
            searchSubmitButton.classList.add('d-none');
        }

        if (paginationContainer) {
            paginationContainer.setAttribute('aria-disabled', 'true');
            paginationContainer.classList.add('d-none');
            const links = paginationContainer.querySelectorAll('a.page-link');
            links.forEach(link => {
                link.setAttribute('aria-disabled', 'true');
                link.setAttribute('tabindex', '-1');
                link.classList.add('disabled');
                const item = link.closest('li');
                item?.classList.add('disabled');
                link.addEventListener('click', event => {
                    event.preventDefault();
                    event.stopPropagation();
                });
            });
        }
    }

    function removerRestricoesParaVisitante() {
        if (managementButton) {
            managementButton.style.display = '';
            managementButton.removeAttribute('aria-hidden');
        }

        if (systemSelectionButton) {
            systemSelectionButton.style.pointerEvents = '';
            systemSelectionButton.style.opacity = '';
            systemSelectionButton.style.cursor = '';
            systemSelectionButton.removeAttribute('aria-disabled');
            systemSelectionButton.removeAttribute('tabindex');
        }

        if (userProfileButton) {
            userProfileButton.style.pointerEvents = '';
            userProfileButton.style.cursor = '';
            userProfileButton.removeAttribute('aria-disabled');
            userProfileButton.removeAttribute('tabindex');
            userProfileButton.classList.remove('disabled');
        }

        if (userMenu) {
            userMenu.style.pointerEvents = '';
            userMenu.style.opacity = '';
        }
    }

    if (heroPrevButton) {
        heroPrevButton.addEventListener('click', () => {
            retrocederDestaque(true);
            reiniciarRotacaoDestaques();
        });
    }

    if (heroNextButton) {
        heroNextButton.addEventListener('click', () => {
            avancarDestaque(true);
            reiniciarRotacaoDestaques();
        });
    }

    if (heroSection) {
        heroSection.addEventListener('mouseenter', () => {
            if (destaquesHero.length > 1) {
                pararRotacaoDestaques();
            }
        });
        heroSection.addEventListener('mouseleave', () => {
            if (destaquesHero.length > 1) {
                iniciarRotacaoDestaques();
            }
        });
        heroSection.addEventListener('focusin', () => {
            if (destaquesHero.length > 1) {
                pararRotacaoDestaques();
            }
        });
        heroSection.addEventListener('focusout', event => {
            if (destaquesHero.length > 1 && !heroSection.contains(event.relatedTarget)) {
                iniciarRotacaoDestaques();
            }
        });
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            pararRotacaoDestaques();
        } else if (destaquesHero.length > 1) {
            iniciarRotacaoDestaques();
        }
    });

    carregarDestaques();
    carregarLista(paginaAtual);
    carregarCalendario();
});
