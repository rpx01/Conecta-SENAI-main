// Arquivo JavaScript global para o Sistema de Agenda de Laboratório
// Contém funções de autenticação, manipulação de localStorage e utilitários

// Constantes globais
const API_URL = '/api';

// Overlay de carregamento reutilizável
let loadingOverlay;

// Cache para resultado de verificação de autenticação
let autenticacaoCache = null;
let verificacaoAutenticacaoPromise = null;

function criarLoadingOverlay() {
    if (loadingOverlay) return;
    loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.className = 'loading-overlay d-none';
    loadingOverlay.setAttribute('role', 'status');
    loadingOverlay.setAttribute('aria-live', 'polite');
    loadingOverlay.setAttribute('tabindex', '0');
    loadingOverlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary" aria-hidden="true"></div>
            <span class="ms-2">Carregando...</span>
        </div>`;
    document.body.appendChild(loadingOverlay);
}

function refreshIcons() {
    if (window.lucide) {
        lucide.createIcons({ attrs: { strokeWidth: 1.75 } });
    }
}
window.refreshIcons = refreshIcons;

function mostrarLoading() {
    criarLoadingOverlay();
    document.body.setAttribute('aria-busy', 'true');
    loadingOverlay.classList.remove('d-none');
}

function ocultarLoading() {
    if (!loadingOverlay) return;
    loadingOverlay.classList.add('d-none');
    document.body.removeAttribute('aria-busy');
}

async function executarComLoading(acao) {
    mostrarLoading();
    try {
        return await acao();
    } finally {
        ocultarLoading();
    }
}

function normalizarPathname(pathname) {
    if (!pathname || typeof pathname !== 'string') {
        return '';
    }

    let path = pathname.trim().toLowerCase();

    // Garante que o caminho comece com '/'
    if (path && !path.startsWith('/')) {
        path = `/${path}`;
    }

    // Remove parâmetros de consulta ou hash, caso tenham sido incluídos acidentalmente
    const queryIndex = path.indexOf('?');
    if (queryIndex !== -1) {
        path = path.slice(0, queryIndex);
    }
    const hashIndex = path.indexOf('#');
    if (hashIndex !== -1) {
        path = path.slice(0, hashIndex);
    }

    // Remove barras extras ao final mantendo a raiz
    if (path.length > 1) {
        path = path.replace(/\/+$/, '');
        if (!path) {
            path = '/';
        }
    }

    return path || '/';
}

// Páginas públicas acessíveis sem autenticação
const PAGINAS_PUBLICAS = new Set([
    '/admin/login.html',
    '/register',
    '/forgot',
    '/reset',
    '/noticias',
    '/noticias/',
    '/noticias/index.html',
    '/suporte_ti/abertura_publica.html'
].map(normalizarPathname));

const PREFIXOS_PUBLICOS = ['/noticias/'];
const PREFIXOS_PUBLICOS_NORMALIZADOS = PREFIXOS_PUBLICOS.map(prefix => ({
    original: prefix,
    normalizado: normalizarPathname(prefix)
}));

const EXCECOES_PREFIXOS_PUBLICOS = new Set([
    '/noticias/gerenciamento.html'
].map(normalizarPathname));

const PAGINAS_REDIRECIONAMENTO = new Set([
    '/admin/login.html',
    '/register',
    '/forgot',
    '/reset'
].map(normalizarPathname));

function ehPaginaPublica(pathname) {
    const normalizado = normalizarPathname(pathname);
    if (!normalizado) return false;
    if (PAGINAS_PUBLICAS.has(normalizado)) {
        return true;
    }
    if (EXCECOES_PREFIXOS_PUBLICOS.has(normalizado)) {
        return false;
    }
    return PREFIXOS_PUBLICOS_NORMALIZADOS.some(({ original, normalizado: prefixNormalizado }) => {
        const requerSubcaminho = original.endsWith('/');
        if (requerSubcaminho) {
            return normalizado === prefixNormalizado || normalizado.startsWith(`${prefixNormalizado}/`);
        }
        return normalizado.startsWith(prefixNormalizado);
    });
}

// Variável global para armazenar o token CSRF e evitar múltiplas buscas
let csrfToken = null;

/**
 * Obtém o token CSRF da API. O token é armazenado em memória para
 * reutilização e renovado quando explicitamente solicitado.
 * @param {boolean} force - Quando true, força a renovação do token
 * @returns {Promise<string>} Token CSRF válido
 */
async function obterCSRFToken(force = false) {
    if (csrfToken && !force) {
        return csrfToken;
    }

    try {
        const resp = await fetch(`${API_URL}/csrf-token`, {
            credentials: 'include'
        });
        if (!resp.ok) {
            throw new Error('Falha ao obter o token CSRF.');
        }
        const data = await resp.json();
        csrfToken = data.csrf_token;
        return csrfToken;
    } catch (err) {
        console.error(err);
        showToast('Erro de segurança. Não foi possível carregar o token CSRF.', 'danger');
        throw err;
    }
}

/**
 * Escapa caracteres HTML para prevenir ataques XSS.
 * @param {string} str - Texto a escapar
 * @returns {string} - HTML escapado
 */
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function sanitizeHTML(html) {
    return window.DOMPurify ? DOMPurify.sanitize(html) : html;
}

/**
 * Alterna o estado de processamento de um botão, exibindo um spinner.
 * @param {HTMLElement} btn - Botão alvo
 * @param {boolean} busy - Se verdadeiro, ativa o estado de espera
 */
function setBusy(btn, busy = true) {
    if (!btn) return;

    if (busy) {
        if (!btn.dataset.originalHtml) {
            btn.dataset.originalHtml = btn.innerHTML;
        }
        btn.disabled = true;
        btn.innerHTML = `${btn.dataset.originalHtml}<span class="spinner-border" role="status" aria-hidden="true"></span>`;
    } else {
        btn.disabled = false;
        if (btn.dataset.originalHtml) {
            btn.innerHTML = btn.dataset.originalHtml;
            delete btn.dataset.originalHtml;
        }
    }
}

const MAPA_SLUGS_PARA_URLS = {
    laboratorios: ['/laboratorios/calendario.html'],
    treinamentos: ['/treinamentos/index.html'],
    ocupacao: ['/ocupacao/dashboard.html'],
    noticias: ['/noticias/index.html'],
    noticias_admin: ['/noticias/gerenciamento.html'],
    suporte_ti: ['/suporte_ti/abertura.html'],
    suporte_ti_admin: ['/suporte_ti/admin_chamados.html'],
    rateio: ['/rateio/dashboard.html'],
    usuarios: ['/admin/usuarios.html']
};

function normalizarUrlModulo(modulo) {
    if (typeof modulo !== 'string') {
        return null;
    }

    const entrada = modulo.trim();
    if (!entrada) {
        return null;
    }

    try {
        const url = new URL(entrada, window.location.origin);
        if (!url.pathname) {
            return null;
        }

        // Remove barra extra ao final, exceto para a raiz
        if (url.pathname !== '/' && url.pathname.endsWith('/')) {
            return url.pathname.slice(0, -1);
        }

        return url.pathname;
    } catch (_) {
        return null;
    }
}

function normalizarModuloEntrada(modulo) {
    if (typeof modulo !== 'string') {
        return [];
    }

    const entrada = modulo.trim();
    if (!entrada) {
        return [];
    }

    const urlsMapeadas = MAPA_SLUGS_PARA_URLS[entrada];
    if (urlsMapeadas) {
        const urls = Array.isArray(urlsMapeadas) ? urlsMapeadas : [urlsMapeadas];
        return urls
            .map((url) => normalizarUrlModulo(url))
            .filter((urlNormalizada) => typeof urlNormalizada === 'string' && urlNormalizada.length > 0);
    }

    const urlNormalizada = normalizarUrlModulo(entrada);
    return urlNormalizada ? [urlNormalizada] : [];
}

function normalizarListaModulos(entradas = []) {
    if (!entradas) {
        return [];
    }

    let valores = [];

    if (Array.isArray(entradas)) {
        valores = entradas;
    } else if (typeof entradas === 'string') {
        valores = entradas.split(',');
    } else if (entradas && typeof entradas[Symbol.iterator] === 'function') {
        valores = Array.from(entradas);
    }

    return valores
        .flatMap((valor) => normalizarModuloEntrada(valor))
        .filter((url) => typeof url === 'string' && url.length > 0);
}

const MODULOS_PADRAO = normalizarListaModulos([
    '/laboratorios/calendario.html',
    '/treinamentos/index.html',
    '/ocupacao/dashboard.html',
    '/noticias/index.html',
    '/suporte_ti/abertura.html'
]);

// Mapeia os módulos disponíveis de acordo com o tipo de usuário
function obterModulosDisponiveis(usuario = {}) {
    const modulos = new Set(MODULOS_PADRAO);

    const modulosUsuario = Array.isArray(usuario.modulos)
        ? usuario.modulos
        : typeof usuario.modulos === 'string' && usuario.modulos.length > 0
            ? usuario.modulos.split(',')
            : [];

    normalizarListaModulos(modulosUsuario).forEach((url) => modulos.add(url));

    if (usuario.tipo === 'admin') {
        normalizarListaModulos([
            '/rateio/dashboard.html',
            '/admin/usuarios.html',
            '/noticias/gerenciamento.html',
            '/suporte_ti/admin_chamados.html'
        ]).forEach((url) => modulos.add(url));
    }

    return Array.from(modulos);
}

// Redireciona o usuário após o login com base nos módulos disponíveis
function redirecionarAposLogin(usuario) {
    const modulos = obterModulosDisponiveis(usuario);
    const moduloSalvo = localStorage.getItem('moduloSelecionado');

    if (moduloSalvo && modulos.includes(moduloSalvo)) {
        window.location.href = moduloSalvo;
        return;
    }

    if (modulos.length === 1) {
        window.location.href = modulos[0];
    } else {
        window.location.href = '/selecao-sistema.html';
    }
}

// Funções de autenticação
/**
 * Realiza o login do usuário
 * @param {string} email - Email do usuário
 * @param {string} senha - Senha do usuário
 * @returns {Promise} - Promise com o resultado do login
 */
async function realizarLogin(email, senha, recaptchaToken = '') {
    try {
        const data = await chamarAPI('/login', 'POST', {
            email,
            senha,
            recaptcha_token: recaptchaToken
        });

        if (data && data.usuario) {
            const isRoot = Boolean(data.is_root ?? data.usuario.is_root);
            const usuarioComMetadados = { ...data.usuario, is_root: isRoot };
            localStorage.setItem('usuario', JSON.stringify(usuarioComMetadados));
            localStorage.setItem('isAdmin', usuarioComMetadados.tipo === 'admin');
            localStorage.setItem('isRoot', isRoot ? 'true' : 'false');
            redirecionarAposLogin(usuarioComMetadados);
            return { ...data, usuario: usuarioComMetadados, is_root: isRoot };
        }

        throw new Error('Resposta inesperada do servidor');
    } catch (error) {
        console.error('Erro no login:', error);
        if (error.name === 'TypeError') {
            throw new Error('Erro de conexão com o servidor');
        }
        throw error;
    }
}

/**
 * Realiza o logout do usuário
 */
async function realizarLogout() {
    try {
        await chamarAPI('/logout', 'POST', {});
    } catch (_) {
        // Ignora erros de logout
    }
    localStorage.removeItem('usuario');
    localStorage.removeItem('isRoot');
    window.location.href = '/admin/login.html';
}

/**
 * Verifica se o usuário está autenticado
 * @returns {boolean} - True se autenticado, false caso contrário
 */
/**
 * Obtém os dados do usuário logado
 * @returns {Object|null} - Objeto com os dados do usuário ou null se não estiver autenticado
 */
function getUsuarioLogado() {
    const usuarioJSON = localStorage.getItem('usuario');
    if (!usuarioJSON) {
        return null;
    }

    try {
        const usuario = JSON.parse(usuarioJSON);
        if (typeof usuario.is_root === 'undefined') {
            const armazenado = localStorage.getItem('isRoot');
            if (armazenado !== null) {
                usuario.is_root = armazenado === 'true';
            }
        }
        return usuario;
    } catch (erro) {
        console.error('Não foi possível ler os dados do usuário armazenados.', erro);
        return null;
    }
}

/**
 * Verifica se o usuário logado é administrador
 * @returns {boolean} - True se for administrador, false caso contrário
 */
function isAdmin() {
    const usuario = getUsuarioLogado();
    // Acesso total para admin, acesso a treinamentos para secretaria
    if (!usuario) return false;
    if (usuario.tipo === 'admin') return true;
    if (usuario.tipo === 'secretaria' && window.location.pathname.includes('/treinamentos/')) {
        return true;
    }
    return false;
}

function isUserAdmin() {
    return localStorage.getItem('isAdmin') === 'true';
}

// Função para ajustar a visibilidade dos elementos com base no papel do usuário
function ajustarVisibilidadePorPapel() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;

    if (usuario.tipo !== 'admin') {
        document.querySelectorAll('.admin-only').forEach(el => {
            // Se for secretaria e estiver na área de treinamentos, mostra o elemento
            if (usuario.tipo === 'secretaria' && window.location.pathname.includes('/treinamentos/')) {
                // Deixamos o elemento visível para a secretaria
            } else {
                el.style.display = 'none';
            }
        });
    }
}

/**
 * Redireciona para a página de login se o usuário não estiver autenticado
 */
/**
 * Verifica se o usuário está autenticado, validando o token com o servidor.
 * @returns {Promise<boolean>} - True se autenticado, false caso contrário
 */
async function verificarAutenticacao() {
    if (autenticacaoCache !== null) {
        return autenticacaoCache;
    }
    if (verificacaoAutenticacaoPromise) {
        return verificacaoAutenticacaoPromise;
    }

    verificacaoAutenticacaoPromise = (async () => {
        const usuario = getUsuarioLogado();
        if (!usuario) {
            window.location.href = '/admin/login.html';
            return false;
        }

        try {
            // Valida o token acessando os dados do próprio usuário
            await chamarAPI(`/usuarios/${usuario.id}`);
            autenticacaoCache = true;
            return true;
        } catch (error) {
            console.warn('Sessão inválida. Redirecionando para login.');
            realizarLogout();
            autenticacaoCache = false;
            return false;
        } finally {
            verificacaoAutenticacaoPromise = null;
        }
    })();

    return verificacaoAutenticacaoPromise;
}

/**
 * Verifica se o usuário tem permissão de administrador
 * Redireciona para o dashboard se não tiver
 */
async function verificarPermissaoAdmin() {
    // Passo 1: Verifica se o usuário está autenticado. Se não, a função já redireciona.
    if (!(await verificarAutenticacao())) return false;

    // Passo 2: Verifica se a página atual é a de seleção de sistema.
    const paginaAtual = window.location.pathname;
    if (paginaAtual === '/selecao-sistema.html') {
        // Se for a página de seleção, NÃO FAÇA NADA. Permita o acesso.
        return true;
    }

    // Passo 3: Se NÃO for a página de seleção, continue com a verificação de admin.
    if (!isAdmin()) {
        showToast('Desculpe, você não tem permissão para acessar esta página. Vamos redirecioná-lo(a).', 'warning');
        window.location.href = '/selecao-sistema.html'; // Redireciona para um local seguro
        return false;
    }

    return true;
}

// ---------- Proteção de Rotas Global ----------
// Esta IIFE garante que o redirecionamento ocorra apenas quando necessário,
// evitando loops na página de login ou registro.
(async function() {
    const currentPage = normalizarPathname(window.location.pathname);

    // Se a página não for pública, valida a sessão no servidor
    if (!ehPaginaPublica(currentPage)) {
        await verificarAutenticacao();
    }

    // Usuário logado tentando acessar página pública que deve redirecionar
    const usuario = getUsuarioLogado();
    if (usuario && PAGINAS_REDIRECIONAMENTO.has(currentPage)) {
        window.location.href = '/selecao-sistema.html';
    }

    // Ajusta interface conforme o papel do usuário
    ajustarVisibilidadePorPapel();
})();

// Funções para chamadas à API
/**
 * Realiza uma chamada à API com autenticação
 * @param {string} endpoint - Endpoint da API
 * @param {string} method - Método HTTP (GET, POST, PUT, DELETE)
 * @param {Object} body - Corpo da requisição (opcional)
 * @returns {Promise} - Promise com o resultado da chamada
 */
async function chamarAPI(endpoint, method = 'GET', body = null) {
    const endpointFormatado = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_URL}${endpointFormatado}`;
    const opts = {
        method,
        credentials: 'include',
        headers: {}
    };

    const mutativo = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase());
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    if (mutativo) {
        const token = await obterCSRFToken();
        opts.headers['X-CSRF-Token'] = token;
        if (isFormData) {
            opts.body = body;
        } else if (body !== null) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
    } else if (body !== null) {
        if (isFormData) {
            opts.body = body;
        } else {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
    }

    return await executarComLoading(async () => {
        let response = await fetch(url, opts);
        if (mutativo && (response.status === 403 || response.status === 419)) {
            const novoToken = await obterCSRFToken(true);
            opts.headers['X-CSRF-Token'] = novoToken;
            response = await fetch(url, opts);
        }

        if (response.status === 401 && endpointFormatado !== '/login') {
            localStorage.removeItem('usuario');
            window.location.href = '/admin/login.html';
            throw new Error('Sessão expirada');
        }

        if (!response.ok) {
            let json = null;
            try { json = await response.json(); } catch (_) {}
            const mensagem = json?.erro || json?.message || response.statusText;
            const error = new Error(mensagem);
            error.status = response.status;
            if (json !== null) {
                error.payload = json;
            }
            throw error;
        }

        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) {
            return await response.json();
        }
        return null;
    });
}

// Funções de formatação e utilidades
/**
 * Formata uma data no padrão brasileiro
 * @param {string} dataISO - Data em formato ISO
 * @returns {string} - Data formatada (DD/MM/YYYY)
 */
function formatarData(dataISO) {
    if (!dataISO) return '';
    const [parteData] = dataISO.split('T');
    const data = new Date(`${parteData}T00:00:00-03:00`);
    return data.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

/**
 * Formata um horário no padrão 24h
 * @param {string} horario - Horário em formato HH:MM
 * @returns {string} - Horário formatado
 */
function formatarHorario(horario) {
    if (!horario) return '';

    // Se já estiver no formato correto HH:MM, apenas normaliza zeros à esquerda
    const partes = horario.split(':');
    if (partes.length === 2) {
        const horas = parseInt(partes[0], 10);
        const minutos = parseInt(partes[1], 10);

        if (!isNaN(horas) && !isNaN(minutos)) {
            const h = String(horas).padStart(2, '0');
            const m = String(minutos).padStart(2, '0');
            return `${h}:${m}`;
        }
    }

    // Caso não seja possível formatar, retorna original
    return horario;
}

/**
 * Garante a existência de um container global para toasts
 * @returns {HTMLElement} - Elemento container
 */
function criarToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = 1100;
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Exibe uma mensagem usando toasts do Bootstrap
 * @param {string} mensagem - Mensagem a ser exibida
 * @param {string} tipo - Tipo do toast (success, danger, warning, info)
 */
function showToast(mensagem, tipo = 'info') {
    const toastContainer = criarToastContainer();

    const toastId = `toast-${Date.now()}`;
    const baseTextColor = tipo === 'warning' ? 'text-dark' : 'text-white';
    const bgColor =
        tipo === 'danger' ? 'bg-danger' :
        (tipo === 'success' ? 'bg-success' :
        (tipo === 'warning' ? 'bg-warning' : 'bg-primary'));
    const closeBtnClass = tipo === 'warning' ? '' : 'btn-close-white';

    const toastHtml = `
        <div id="${toastId}" class="toast ${baseTextColor} ${bgColor}" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="5000">
            <div class="d-flex">
                <div class="toast-body">
                    ${escapeHTML(mensagem)}
                </div>
                <button type="button" class="btn-close ${closeBtnClass} me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>`;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);

    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });

    toast.show();
}

/**
 * Exibe notificação rápida via Toast do Bootstrap.
 * @param {string} tipo - success|warning|danger|info
 * @param {string} mensagem - Mensagem a ser exibida
 */
function notify(tipo, mensagem) {
    showToast(mensagem, tipo);
}

window.showToast = showToast;
window.notify = notify;
window.setBusy = setBusy;
window.normalizarUrlModulo = normalizarUrlModulo;
document.addEventListener('DOMContentLoaded', criarToastContainer);

/**
 * Retorna a classe CSS correspondente ao turno
 * @param {string} turno - Nome do turno (Manhã, Tarde, Noite)
 * @returns {string} - Nome da classe CSS
 */
function getClasseTurno(turno) {
    switch (turno) {
        case 'Manhã':
            return 'agendamento-manha';
        case 'Tarde':
            return 'agendamento-tarde';
        case 'Noite':
            return 'agendamento-noite';
        default:
            return '';
    }
}

/**
 * Executa uma ação assíncrona desabilitando o botão durante a operação para
 * evitar cliques duplicados. Caso o botão contenha um elemento com a classe
 * `.spinner-border`, ele será exibido enquanto a Promise estiver pendente. Se
 * houver um span com classe `.btn-text`, o texto é temporariamente alterado
 * para "Processando...".
 *
 * @param {HTMLButtonElement|HTMLInputElement} btn - Botão que dispara a ação
 * @param {() => Promise<any>} acao - Função assíncrona a ser executada
 * @returns {Promise<any>} - Resultado da Promise da ação
 */
async function executarAcaoComFeedback(btn, acao) {
    if (!btn || typeof acao !== 'function') {
        throw new Error('Parâmetros inválidos em executarAcaoComFeedback');
    }

    const spinner = btn.querySelector('.spinner-border');
    const textoSpan = btn.querySelector('.btn-text');
    const textoOriginal = textoSpan ? textoSpan.textContent : '';

    btn.disabled = true;
    if (spinner) spinner.classList.remove('d-none');
    if (textoSpan) textoSpan.textContent = 'Processando...';

    try {
        return await executarComLoading(acao);
    } finally {
        if (spinner) spinner.classList.add('d-none');
        if (textoSpan) textoSpan.textContent = textoOriginal;
        btn.disabled = false;
    }
}

/**
 * Adiciona o link para a página de Laboratórios e Turmas no menu
 * @param {string} containerSelector - Seletor CSS do container do menu
 * @param {boolean} isNavbar - Indica se é o menu da navbar ou sidebar
 */
function adicionarLinkLabTurmas(containerSelector, isNavbar = false) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    // Verifica se o link já existe para evitar duplicação
    const linkExistente = container.querySelector('a[href="/laboratorios/turmas.html"]');
    if (linkExistente) return;
    
    // Cria o elemento do link baseado no tipo de menu
    if (isNavbar) {
        // Para navbar (menu superior)
        const navItem = document.createElement('li');
        navItem.className = 'nav-item admin-only';
        
        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = '/laboratorios/turmas.html';
        link.innerHTML = '<i data-lucide="building-2" class="me-1"></i> Laboratórios e Turmas';
        
        navItem.appendChild(link);

        // Insere antes do último item (dropdown do usuário)
        const lastItem = container.querySelector('.dropdown');
        if (lastItem) {
            container.insertBefore(navItem, lastItem);
        } else {
            container.appendChild(navItem);
        }
        refreshIcons();
    } else {
        // Para sidebar (menu lateral)
        const link = document.createElement('a');
        link.className = 'nav-link admin-only';
        link.href = '/laboratorios/turmas.html';
        link.innerHTML = '<i data-lucide="building-2"></i> Laboratórios e Turmas';
        
        // Insere antes do último item (Meu Perfil)
        const lastItem = container.querySelector('a[href="/laboratorios/perfil.html"], a[href="/ocupacao/perfil.html"], a[href="/admin/perfil.html"]');
        if (lastItem) {
            container.insertBefore(link, lastItem);
        } else {
            container.appendChild(link);
        }
        refreshIcons();
    }
}

// Adiciona o link para a página de Logs
function adicionarLinkLogs(containerSelector, isNavbar = false) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const linkExistente = container.querySelector('a[href="/laboratorios/logs.html"]');
    if (linkExistente) return;

    if (isNavbar) {
        const navItem = document.createElement('li');
        navItem.className = 'nav-item admin-only';

        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = '/laboratorios/logs.html';
        link.innerHTML = '<i data-lucide="book-open-text" class="me-1"></i> Logs';

        navItem.appendChild(link);

        const lastItem = container.querySelector('.dropdown');
        if (lastItem) {
            container.insertBefore(navItem, lastItem);
        } else {
            container.appendChild(navItem);
        }
        refreshIcons();
    } else {
        const link = document.createElement('a');
        link.className = 'nav-link admin-only';
        link.href = '/laboratorios/logs.html';
        link.innerHTML = '<i data-lucide="book-open-text"></i> Logs';

        const lastItem = container.querySelector('a[href="/laboratorios/perfil.html"], a[href="/ocupacao/perfil.html"], a[href="/admin/perfil.html"]');
        if (lastItem) {
            container.insertBefore(link, lastItem);
        } else {
            container.appendChild(link);
        }
        refreshIcons();
    }
}

/**
 * Adiciona ao menu do usuário um botão para retornar à tela de seleção de sistema
 */
function adicionarBotaoSelecaoSistema() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;
    const modulos = obterModulosDisponiveis(usuario);
    if (modulos.length <= 1) return;

    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        // Evita duplicação do botão
        if (menu.querySelector('a[href="/selecao-sistema.html"]')) return;

        const li = document.createElement('li');

        const link = document.createElement('a');
        link.className = 'dropdown-item';
        link.href = '/selecao-sistema.html';
        link.innerHTML = '<i data-lucide="arrow-left" class="me-2"></i> Retornar à tela de seleção de sistema';
        link.addEventListener('click', () => localStorage.removeItem('moduloSelecionado'));

        li.appendChild(link);

        const logoutLink = menu.querySelector('#btnLogout') || menu.querySelector('a[onclick="realizarLogout()"]');
        if (logoutLink && logoutLink.parentElement) {
            menu.insertBefore(li, logoutLink.parentElement);
        } else {
            menu.appendChild(li);
        }
        refreshIcons();
    });
}

/**
 * Converte a navbar colapsável em offcanvas para telas pequenas.
 */
function configurarNavbarOffcanvas() {
    const navbar = document.querySelector('.navbar');
    const toggler = document.querySelector('.navbar-toggler');
    const collapse = document.querySelector('.navbar .collapse.navbar-collapse');

    if (!navbar || !toggler || !collapse) return;

    // Ajusta breakpoint de expansão
    navbar.classList.remove('navbar-expand-lg');
    navbar.classList.add('navbar-expand-md');

    // Configura o botão para abrir o offcanvas
    toggler.setAttribute('data-bs-toggle', 'offcanvas');
    toggler.setAttribute('data-bs-target', '#navOffcanvas');
    toggler.setAttribute('aria-controls', 'navOffcanvas');
    toggler.setAttribute('aria-label', 'Abrir menu');

    // Cria estrutura do offcanvas
    const offcanvas = document.createElement('div');
    offcanvas.id = 'navOffcanvas';
    offcanvas.className = 'offcanvas offcanvas-start offcanvas-md';
    offcanvas.tabIndex = -1;
    offcanvas.innerHTML = `
        <div class="offcanvas-header d-md-none">
            <h5 class="offcanvas-title">Menu</h5>
            <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body"></div>
    `;

    const body = offcanvas.querySelector('.offcanvas-body');

    while (collapse.firstChild) {
        body.appendChild(collapse.firstChild);
    }

    collapse.parentNode.replaceChild(offcanvas, collapse);
}

// Inicialização da página
document.addEventListener('DOMContentLoaded', async function() {

    // Verifica autenticação em todas as páginas exceto as públicas
    const paginaAtual = window.location.pathname.toLowerCase();

    // Limpa escolha salva ao retornar para a seleção de sistema
    document.querySelectorAll('a[href="/selecao-sistema.html"]').forEach(link => {
        link.addEventListener('click', () => localStorage.removeItem('moduloSelecionado'));
    });

    // Configura o botão de logout em todas as páginas
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', function(e) {
            e.preventDefault();
            realizarLogout();
        });
    }

    if (ehPaginaPublica(paginaAtual)) {
        return;
    }

    // Verifica se o usuário está autenticado
    if (!(await verificarAutenticacao())) {
        return;
    }


    
    // Verifica se é a página de seleção de sistema
    if (paginaAtual === '/selecao-sistema.html') {
        if (!(await verificarPermissaoAdmin())) {
            return;
        }
        return;
    }
    
    // Páginas que requerem permissão de administrador
    if (paginaAtual === '/admin/usuarios.html' || paginaAtual === '/laboratorios/turmas.html') {
        if (!(await verificarPermissaoAdmin())) {
            return;
        }
    }
    
    // Adiciona o botão de retorno para admins
    adicionarBotaoSelecaoSistema();

    // Atualiza a interface com os dados do usuário
    atualizarInterfaceUsuario();

    // CHAMA A NOVA FUNÇÃO PARA AJUSTAR A INTERFACE
    ajustarVisibilidadePorPapel();
    
    // Adiciona os links de navegação para administradores apenas nos módulos permitidos
    if (isAdmin()) {
        const modulosDeInclusao = [
            '/laboratorios/'
            // Se outras áreas precisarem destes links, adicione aqui
        ];

        const deveExibirLinks = modulosDeInclusao.some(modulo => paginaAtual.startsWith(modulo));

        if (deveExibirLinks) {
            adicionarLinkLabTurmas('.navbar-nav.ms-auto', true);
            adicionarLinkLabTurmas('#sidebarDrawer nav ul', false);

            adicionarLinkLogs('.navbar-nav.ms-auto', true);
            adicionarLinkLogs('#sidebarDrawer nav ul', false);

            configurarObservadoresMenu();
        }
    }

    configurarNavbarOffcanvas();
});

/**
 * Configura observadores de mutação para garantir que os links admin sejam adicionados
 * mesmo quando o DOM é modificado dinamicamente
 */
function configurarObservadoresMenu() {
    // Configura o observador para a navbar
    const navbarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('.navbar-nav.ms-auto', true);
        adicionarLinkLogs('.navbar-nav.ms-auto', true);
    });

    const navbar = document.querySelector('.navbar-nav.ms-auto');
    if (navbar) {
        navbarObserver.observe(navbar, { childList: true, subtree: true });
    }

    // Configura o observador para a sidebar
    const sidebarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('#sidebarDrawer nav ul', false);
        adicionarLinkLogs('#sidebarDrawer nav ul', false);
    });
    
    const sidebar = document.querySelector('#sidebarDrawer nav ul');
    if (sidebar) {
        sidebarObserver.observe(sidebar, { childList: true, subtree: true });
    }
}

/**
 * Atualiza elementos da interface com os dados do usuário logado
 */
function atualizarInterfaceUsuario() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;
    
    // Atualiza o nome do usuário na navbar
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = usuario.nome;
    }
    
    // Exibe ou oculta elementos baseado no tipo de usuário
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(element => {
        element.style.display = isAdmin() ? '' : 'none';
    });
    
    // Carrega notificações no dashboard
    if (window.location.pathname === '/laboratorios/calendario.html') {
        carregarNotificacoes();
    }
}

/**
 * Carrega notificações do usuário para exibição no dashboard
 */
async function carregarNotificacoes() {
    const notificacoesContainer = document.getElementById('notificacoesContainer');
    if (!notificacoesContainer) return;
    
    try {
        const notificacoes = await chamarAPI('/notificacoes');
        
        if (notificacoes.length === 0) {
            notificacoesContainer.innerHTML = '<p class="text-muted">Nenhuma notificação disponível.</p>';
            return;
        }
        
        let html = '';
        notificacoes.forEach(notificacao => {
            const classeNotificacao = notificacao.lida ? 'bg-light' : 'bg-info bg-opacity-10';
            const mensagem = sanitizeHTML(notificacao.mensagem);
            const dataCriacao = sanitizeHTML(formatarData(notificacao.data_criacao));
            const idNotificacao = sanitizeHTML(String(notificacao.id));
            html += `
                <div class="card mb-2 ${classeNotificacao}">
                    <div class="card-body">
                        <p class="card-text">${mensagem}</p>
                        <p class="card-text"><small class="text-muted">
                            ${dataCriacao}
                        </small></p>
                        ${!notificacao.lida ? `
                            <button class="btn btn-sm btn-outline-primary marcar-lida"
                                data-id="${idNotificacao}">Marcar como lida</button>
                        ` : ''}
                    </div>
                </div>
            `;
        });

        notificacoesContainer.innerHTML = sanitizeHTML(html);
        
        // Adiciona event listeners para os botões de marcar como lida
        document.querySelectorAll('.marcar-lida').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.getAttribute('data-id');
                try {
                    await chamarAPI(`/notificacoes/${id}/marcar-lida`, 'PUT');
                    // Recarrega as notificações
                    carregarNotificacoes();
                } catch (error) {
                    showToast('Não conseguimos marcar a notificação como lida.', 'danger');
                }
            });
        });
    } catch (error) {
        notificacoesContainer.innerHTML = '<p class="text-danger">Erro ao carregar notificações.</p>';
    }
}

/**
 * Carrega laboratórios do sistema para uso em filtros e formulários
 * @returns {Promise<Array>} - Promise com a lista de laboratórios
 */
async function carregarLaboratoriosParaFiltro(seletorElemento) {
    const selectElement = document.querySelector(seletorElemento);
    if (!selectElement) return [];
    
    try {
        const laboratorios = await chamarAPI('/laboratorios');
        
        // Mantém a opção "Todos"
        let html = '<option value="">Todos</option>';
        
        // Adiciona as opções de laboratórios
        laboratorios.forEach(lab => {
            html += `<option value="${lab.nome}">${lab.nome}</option>`;
        });
        
        selectElement.innerHTML = html;
        return laboratorios;
    } catch (error) {
        console.error('Erro ao carregar laboratórios para filtro:', error);
        return [];
    }
}

// Exporta dados genéricos (CSV, PDF ou XLSX)
async function exportarDados(endpoint, formato, nomeArquivo) {
    try {
        const response = await fetch(`${API_URL}${endpoint}?formato=${formato}`, {
        });
        if (!response.ok) {
            throw new Error('Erro ao exportar dados');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${nomeArquivo}.${formato}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Erro ao exportar dados:', error);
        showToast('Não conseguimos exportar os dados.', 'danger');
    }
}

// Preenche de forma genérica uma tabela a partir de um endpoint
async function preencherTabela(idTabela, endpoint, funcaoRenderizarLinha) {
    const tabela = document.getElementById(idTabela);
    if (!tabela) {
        console.error(`Tabela com id '${idTabela}' não encontrada.`);
        return [];
    }
    const thead = tabela.querySelector('thead');
    const tbody = tabela.querySelector('tbody');
    const numColunas = thead ? thead.querySelector('tr').childElementCount : 1;

    // Exibe um texto enquanto os dados são carregados
    tbody.innerHTML = `<tr><td colspan="${numColunas}" class="text-center py-4">Carregando...</td></tr>`;

    try {
        const dados = await chamarAPI(endpoint, 'GET');
        tbody.innerHTML = '';
        if (dados && dados.length > 0) {
            dados.forEach(item => {
                const linhaHtml = funcaoRenderizarLinha(item);
                if (linhaHtml) {
                    tbody.insertAdjacentHTML('beforeend', linhaHtml);
                }
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="${numColunas}" class="text-center">Nenhum registro encontrado.</td></tr>`;
        }
        return dados;
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="${numColunas}" class="text-center text-danger">Erro ao carregar os dados.</td></tr>`;
        console.error(`Erro ao preencher tabela ${idTabela}:`, error);
        return [];
    }
}

// Inicializa um menu lateral oculto baseado nos links da navbar
(() => {
    if (document.getElementById('sidebarDrawer')) {
        return;
    }

    const cssHref = '/css/menu-suspenso.css';
    if (!document.querySelector(`link[href="${cssHref}"]`)) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssHref;
        document.head.appendChild(link);
    }

    const edge = document.createElement('div');
    edge.id = 'hoverEdge';
    edge.setAttribute('aria-hidden', 'true');
    document.body.appendChild(edge);

    const drawer = document.createElement('aside');
    drawer.id = 'sidebarDrawer';
    drawer.className = 'drawer';
    drawer.setAttribute('aria-label', 'Menu lateral');
    drawer.setAttribute('aria-expanded', 'false');
    drawer.innerHTML = `
        <div class="drawer-header"><h2>Menu</h2></div>
        <nav class="drawer-nav"><ul></ul></nav>
    `;

    const navList = document.querySelector('nav .navbar-nav');
    const ul = drawer.querySelector('ul');
    if (navList) {
        navList.querySelectorAll('li').forEach(li => {
            ul.appendChild(li.cloneNode(true));
        });
    }

    document.body.appendChild(drawer);

    let openTimer, closeTimer;
    const open = () => {
        clearTimeout(closeTimer);
        drawer.classList.add('open');
        drawer.setAttribute('aria-expanded', 'true');
    };
    const close = () => {
        clearTimeout(openTimer);
        if (!drawer.matches(':hover')) {
            drawer.classList.remove('open');
            drawer.setAttribute('aria-expanded', 'false');
        }
    };

    edge.addEventListener('mouseenter', () => { openTimer = setTimeout(open, 80); });
    drawer.addEventListener('mouseleave', () => { closeTimer = setTimeout(close, 150); });
    drawer.addEventListener('focusin', open);
    drawer.addEventListener('focusout', () => { setTimeout(close, 120); });
    edge.addEventListener('click', () => {
        drawer.classList.toggle('open');
        const expanded = drawer.classList.contains('open');
        drawer.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
})();
