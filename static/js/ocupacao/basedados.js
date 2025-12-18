document.addEventListener('DOMContentLoaded', async () => {
    
    if (!await verificarAutenticacao()) return;
    if (!await verificarPermissaoAdmin()) return;

    const usuario = getUsuarioLogado();
    document.getElementById('nomeUsuarioNav').textContent = usuario.nome;

    const tabsCarregadas = {
        salas: false,
        docentes: false,
        turmas: false
    };

    carregarDadosAbaAtiva('salas');

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

    restaurarAbaAtiva();

    function carregarDadosAbaAtiva(aba) {
        if (tabsCarregadas[aba]) {
            return; 
        }

        switch (aba) {
            case 'salas':
                
                tabsCarregadas.salas = true;
                break;

            case 'docentes':
                
                tabsCarregadas.docentes = true;
                break;

            case 'turmas':
                
                tabsCarregadas.turmas = true;
                break;
        }
    }

    function salvarAbaAtiva(aba) {
        localStorage.setItem('baseDadosAbaAtiva', aba);
    }

    function restaurarAbaAtiva() {
        const abaAtiva = localStorage.getItem('baseDadosAbaAtiva');

        if (abaAtiva && abaAtiva !== 'salas') {
            
            const tabElement = document.getElementById(`${abaAtiva}-tab`);
            if (tabElement) {
                const tab = new bootstrap.Tab(tabElement);
                tab.show();
            }
        }
    }
});

window.aplicarFiltros = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.aplicarFiltros();
    }
};

window.limparFiltros = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.limparFiltros();
    }
};

window.novaSala = function () {
    if (window.gerenciadorSalas) {
        window.gerenciadorSalas.novaSala();
    }
};
