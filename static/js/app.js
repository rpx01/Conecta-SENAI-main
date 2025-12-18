const API_URL = '/api';

let loadingOverlay;

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

    if (path && !path.startsWith('/')) {
        path = `/${path}`;
    }

    const queryIndex = path.indexOf('?');
    if (queryIndex !== -1) {
        path = path.slice(0, queryIndex);
    }
    const hashIndex = path.indexOf('#');
    if (hashIndex !== -1) {
        path = path.slice(0, hashIndex);
    }

    if (path.length > 1) {
        path = path.replace(/\/+$/, '');
        if (!path) {
            path = '/';
        }
    }

    return path || '/';
}

const PAGINAS_PUBLICAS = new Set([
    '/admin/login.html',
    '/register',
    '/forgot',
    '/reset',
    '/noticias',
    '/noticias/',
    '/noticias/index.html',
    '/suporte_ti/abertura_publica.html',
    '/manutencao_unidade/abertura_publica.html'
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

let csrfToken = null;

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

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function sanitizeHTML(html) {
    return window.DOMPurify ? DOMPurify.sanitize(html) : html;
}

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
    manutencao_unidade: ['/manutencao_unidade/abertura.html'],
    manutencao_unidade_admin: ['/manutencao_unidade/admin_chamados.html'],
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
    '/suporte_ti/abertura.html',
    '/manutencao_unidade/abertura.html'
]);

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
            '/suporte_ti/admin_chamados.html',
            '/manutencao_unidade/admin_chamados.html'
        ]).forEach((url) => modulos.add(url));
    }

    return Array.from(modulos);
}

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

async function realizarLogout() {
    try {
        await chamarAPI('/logout', 'POST', {});
    } catch (_) {
        
    }
    localStorage.removeItem('usuario');
    localStorage.removeItem('isRoot');
    window.location.href = '/admin/login.html';
}

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

function isAdmin() {
    const usuario = getUsuarioLogado();
    
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

function ajustarVisibilidadePorPapel() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;

    if (usuario.tipo !== 'admin') {
        document.querySelectorAll('.admin-only').forEach(el => {
            
            if (usuario.tipo === 'secretaria' && window.location.pathname.includes('/treinamentos/')) {
                
            } else {
                el.style.display = 'none';
            }
        });
    }
}

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

async function verificarPermissaoAdmin() {
    
    if (!(await verificarAutenticacao())) return false;

    const paginaAtual = window.location.pathname;
    if (paginaAtual === '/selecao-sistema.html') {
        
        return true;
    }

    if (!isAdmin()) {
        showToast('Desculpe, você não tem permissão para acessar esta página. Vamos redirecioná-lo(a).', 'warning');
        window.location.href = '/selecao-sistema.html'; 
        return false;
    }

    return true;
}

(async function() {
    const currentPage = normalizarPathname(window.location.pathname);

    if (!ehPaginaPublica(currentPage)) {
        await verificarAutenticacao();
    }

    const usuario = getUsuarioLogado();
    if (usuario && PAGINAS_REDIRECIONAMENTO.has(currentPage)) {
        window.location.href = '/selecao-sistema.html';
    }

    ajustarVisibilidadePorPapel();
})();

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

function formatarData(dataISO) {
    if (!dataISO) return '';
    const [parteData] = dataISO.split('T');
    const data = new Date(`${parteData}T00:00:00-03:00`);
    return data.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

function formatarHorario(horario) {
    if (!horario) return '';

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

    return horario;
}

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

function notify(tipo, mensagem) {
    showToast(mensagem, tipo);
}

window.showToast = showToast;
window.notify = notify;
window.setBusy = setBusy;
window.normalizarUrlModulo = normalizarUrlModulo;
document.addEventListener('DOMContentLoaded', criarToastContainer);

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

function adicionarLinkLabTurmas(containerSelector, isNavbar = false) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    const linkExistente = container.querySelector('a[href="/laboratorios/turmas.html"]');
    if (linkExistente) return;
    
    if (isNavbar) {
        
        const navItem = document.createElement('li');
        navItem.className = 'nav-item admin-only';
        
        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = '/laboratorios/turmas.html';
        link.innerHTML = '<i data-lucide="building-2" class="me-1"></i> Laboratórios e Turmas';
        
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
        link.href = '/laboratorios/turmas.html';
        link.innerHTML = '<i data-lucide="building-2"></i> Laboratórios e Turmas';
        
        const lastItem = container.querySelector('a[href="/laboratorios/perfil.html"], a[href="/ocupacao/perfil.html"], a[href="/admin/perfil.html"]');
        if (lastItem) {
            container.insertBefore(link, lastItem);
        } else {
            container.appendChild(link);
        }
        refreshIcons();
    }
}

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

function adicionarBotaoSelecaoSistema() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;
    const modulos = obterModulosDisponiveis(usuario);
    if (modulos.length <= 1) return;

    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        
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

function configurarNavbarOffcanvas() {
    const navbar = document.querySelector('.navbar');
    const toggler = document.querySelector('.navbar-toggler');
    const collapse = document.querySelector('.navbar .collapse.navbar-collapse');

    if (!navbar || !toggler || !collapse) return;

    navbar.classList.remove('navbar-expand-lg');
    navbar.classList.add('navbar-expand-md');

    toggler.setAttribute('data-bs-toggle', 'offcanvas');
    toggler.setAttribute('data-bs-target', '#navOffcanvas');
    toggler.setAttribute('aria-controls', 'navOffcanvas');
    toggler.setAttribute('aria-label', 'Abrir menu');

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

document.addEventListener('DOMContentLoaded', async function() {

    const paginaAtual = window.location.pathname.toLowerCase();

    document.querySelectorAll('a[href="/selecao-sistema.html"]').forEach(link => {
        link.addEventListener('click', () => localStorage.removeItem('moduloSelecionado'));
    });

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

    if (!(await verificarAutenticacao())) {
        return;
    }

    if (paginaAtual === '/selecao-sistema.html') {
        if (!(await verificarPermissaoAdmin())) {
            return;
        }
        return;
    }
    
    if (paginaAtual === '/admin/usuarios.html' || paginaAtual === '/laboratorios/turmas.html') {
        if (!(await verificarPermissaoAdmin())) {
            return;
        }
    }
    
    adicionarBotaoSelecaoSistema();

    atualizarInterfaceUsuario();

    ajustarVisibilidadePorPapel();
    
    if (isAdmin()) {
        const modulosDeInclusao = [
            '/laboratorios/'
            
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

function configurarObservadoresMenu() {
    
    const navbarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('.navbar-nav.ms-auto', true);
        adicionarLinkLogs('.navbar-nav.ms-auto', true);
    });

    const navbar = document.querySelector('.navbar-nav.ms-auto');
    if (navbar) {
        navbarObserver.observe(navbar, { childList: true, subtree: true });
    }

    const sidebarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('#sidebarDrawer nav ul', false);
        adicionarLinkLogs('#sidebarDrawer nav ul', false);
    });
    
    const sidebar = document.querySelector('#sidebarDrawer nav ul');
    if (sidebar) {
        sidebarObserver.observe(sidebar, { childList: true, subtree: true });
    }
}

function atualizarInterfaceUsuario() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;
    
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = usuario.nome;
    }
    
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(element => {
        element.style.display = isAdmin() ? '' : 'none';
    });
    
    if (window.location.pathname === '/laboratorios/calendario.html') {
        carregarNotificacoes();
    }
}

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
        
        document.querySelectorAll('.marcar-lida').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.getAttribute('data-id');
                try {
                    await chamarAPI(`/notificacoes/${id}/marcar-lida`, 'PUT');
                    
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

async function carregarLaboratoriosParaFiltro(seletorElemento) {
    const selectElement = document.querySelector(seletorElemento);
    if (!selectElement) return [];
    
    try {
        const laboratorios = await chamarAPI('/laboratorios');
        
        let html = '<option value="">Todos</option>';
        
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

async function preencherTabela(idTabela, endpoint, funcaoRenderizarLinha) {
    const tabela = document.getElementById(idTabela);
    if (!tabela) {
        console.error(`Tabela com id '${idTabela}' não encontrada.`);
        return [];
    }
    const thead = tabela.querySelector('thead');
    const tbody = tabela.querySelector('tbody');
    const numColunas = thead ? thead.querySelector('tr').childElementCount : 1;

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
