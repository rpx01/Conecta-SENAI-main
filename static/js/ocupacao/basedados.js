// Gerenciamento da página unificada Base de Dados
// Coordena as abas de Salas, Corpo Docente e Turmas

document.addEventListener('DOMContentLoaded', async () => {
    // Verifica autenticação e permissão de admin
    if (!await verificarAutenticacao()) return;
    if (!await verificarPermissaoAdmin()) return;

    // Atualiza nome do usuário na navbar
    const usuario = getUsuarioLogado();
    document.getElementById('nomeUsuarioNav').textContent = usuario.nome;

    // Estado das abas - controla qual aba foi carregada
    const tabsCarregadas = {
        salas: false,
        docentes: false,
        turmas: false
    };

    // Carrega dados da aba ativa inicial (Salas)
    carregarDadosAbaAtiva('salas');

    // Event listeners para mudança de abas
    const salasTab = document.getElementById('salas-tab');
    const docentesTab = document.getElementById('docentes-tab');
    const turmasTab = document.getElementById('turmas-tab');

    salasTab.addEventListener('shown.bs.tab', () => {
        carregarDadosAbaAtiva('salas');
        salvarAbaAtiva('salas');
    });

    docentesTab.addEventListener('shown.bs.tab', () => {
        carregarDadosAbaAtiva('docentes');
        salvarAbaAtiva('docentes');
    });

    turmasTab.addEventListener('shown.bs.tab', () => {
        carregarDadosAbaAtiva('turmas');
        salvarAbaAtiva('turmas');
    });

    // Restaura aba ativa da última sessão
    restaurarAbaAtiva();

    /**
     * Carrega os dados da aba ativa se ainda não foram carregados
     */
    function carregarDadosAbaAtiva(aba) {
        if (tabsCarregadas[aba]) {
            return; // Já foi carregada
        }

        switch (aba) {
            case 'salas':
                // Salas já são carregadas automaticamente pela classe GerenciadorSalas
                // que é instanciada no salas.js
                tabsCarregadas.salas = true;
                break;

            case 'docentes':
                // O GerenciadorInstrutores já inicializa automaticamente
                // quando o DOM está pronto, não precisamos fazer nada aqui
                tabsCarregadas.docentes = true;
                break;

            case 'turmas':
                // As turmas já são carregadas automaticamente no turmas.js
                tabsCarregadas.turmas = true;
                break;
        }
    }

    /**
     * Salva a aba ativa no localStorage para persistência
     */
    function salvarAbaAtiva(aba) {
        localStorage.setItem('baseDadosAbaAtiva', aba);
    }

    /**
     * Restaura a última aba ativa do localStorage
     */
    function restaurarAbaAtiva() {
        const abaAtiva = localStorage.getItem('baseDadosAbaAtiva');

        if (abaAtiva && abaAtiva !== 'salas') {
            // Ativa a aba salva
            const tabElement = document.getElementById(`${abaAtiva}-tab`);
            if (tabElement) {
                const tab = new bootstrap.Tab(tabElement);
                tab.show();
            }
        }
    }
});

// Funções globais para compatibilidade com os scripts existentes

/**
 * Função global para aplicar filtros de salas
 * Chamada pelos botões na aba de salas
 */
window.aplicarFiltros = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.aplicarFiltros();
    }
};

/**
 * Função global para limpar filtros de salas
 */
window.limparFiltros = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.limparFiltros();
    }
};

/**
 * Função global para criar nova sala
 */
window.novaSala = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.novaSala();
    }
};
