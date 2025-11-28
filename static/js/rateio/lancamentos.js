class LancamentosApp {
    constructor() {
        this.selectInstrutor = document.getElementById('selectInstrutor');
        this.selectAno = document.getElementById('selectAno');
        this.gridContainer = document.getElementById('grid-anual-container');

        this.modalEl = document.getElementById('lancamentoModal');
        this.modal = new bootstrap.Modal(this.modalEl);
        this.modalTitle = document.getElementById('lancamentoModalLabel');
        this.lancamentosContainer = document.getElementById('lancamentosAtuaisContainer');
        this.selectConfig = document.getElementById('selectConfigModal');
        this.inputPercentual = document.getElementById('inputPercentualModal');
        this.btnAdicionar = document.getElementById('btnAdicionarRateioModal');
        this.btnSalvar = document.getElementById('btnSalvarModal');
        this.totalPercentual = document.getElementById('totalPercentualModal');
        this.progressBar = document.getElementById('progressBarModal');

        this.dadosAno = {};
        this.mesAtual = null;

        this.registrarEventos();
        this.carregarInstrutores();
        this.preencherAnos();
        this.carregarConfigs();
    }

    registrarEventos() {
        this.selectInstrutor.addEventListener('change', () => this.carregarAno());
        this.selectAno.addEventListener('change', () => this.carregarAno());
        this.btnAdicionar.addEventListener('click', () => this.adicionarItem());
        this.btnSalvar.addEventListener('click', () => this.salvar());
    }

    async carregarInstrutores() {
        try {
            const instrutores = await chamarAPI('/instrutores');
            this.selectInstrutor.innerHTML = '<option value="">Selecione</option>' +
                instrutores.map(i => `<option value="${i.id}">${escapeHTML(i.nome)}</option>`).join('');
        } catch (e) {
            showToast(e.message, 'danger');
        }
    }

    preencherAnos() {
        const ano = new Date().getFullYear();
        let options = '';
        for (let a = ano - 1; a <= ano + 1; a++) {
            options += `<option value="${a}" ${a === ano ? 'selected' : ''}>${a}</option>`;
        }
        this.selectAno.innerHTML = options;
    }

    async carregarConfigs() {
        try {
            const configs = await chamarAPI('/rateio-configs');
            this.selectConfig.innerHTML = '<option value="">Selecione</option>' +
                configs.map(c => `<option value="${c.id}">${escapeHTML(c.classe_valor)}</option>`).join('');
        } catch (e) {
            showToast(e.message, 'danger');
        }
    }

    async carregarAno() {
        const instrutorId = this.selectInstrutor.value;
        if (!instrutorId) return;
        const ano = parseInt(this.selectAno.value, 10);
        try {
            this.dadosAno = await chamarAPI(`/rateio/lancamentos-ano?instrutor_id=${instrutorId}&ano=${ano}`);
            this.renderizarGrid();
        } catch (e) {
            showToast(e.message, 'danger');
        }
    }

    renderizarGrid() {
        this.gridContainer.innerHTML = '';
        for (let m = 1; m <= 12; m++) {
            const dados = this.dadosAno[m] || [];
            const total = dados.reduce((a, b) => a + b.percentual, 0);
            let badgeClass = 'bg-light text-dark border';
            let badgeText = 'Vazio';
            if (total === 100) {
                badgeClass = 'bg-success';
                badgeText = 'Completo (100%)';
            } else if (total > 0) {
                badgeClass = 'bg-warning';
                badgeText = `Parcial (${total}%)`;
            }
            const itens = dados.map(d => `<li class="list-group-item">${escapeHTML(d.rateio_config.classe_valor)}: ${d.percentual}%</li>`).join('');
            const card = document.createElement('div');
            card.className = 'col';
            card.dataset.mes = m;
            card.innerHTML = `
                <div class="card h-100 month-card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${this.nomeMes(m)}</h6>
                        <span class="badge ${badgeClass}">${badgeText}</span>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            ${itens || '<li class="list-group-item text-muted">Sem lançamentos</li>'}
                        </ul>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-primary btn-sm w-100" data-mes="${m}">
                            <i data-lucide="pencil" class="me-1"></i> Gerenciar Lançamentos
                        </button>
                    </div>
                </div>`;
            card.querySelector('button').addEventListener('click', () => this.abrirModal(m));
        this.gridContainer.appendChild(card);
        }
        this.gridContainer.style.display = 'flex';
        refreshIcons();
    }

    nomeMes(m) {
        const nomes = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
        return nomes[m - 1];
    }

    abrirModal(mes) {
        this.mesAtual = mes;
        const ano = parseInt(this.selectAno.value, 10);
        this.modalTitle.textContent = `Lançamentos para ${this.nomeMes(mes)} / ${ano}`;
        const dados = this.dadosAno[mes] || [];
        this.lancamentosContainer.innerHTML = '';
        dados.forEach(l => this.criarLinha(l));
        this.atualizarTotal();
        this.modal.show();
    }

    criarLinha(lancamento) {
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.dataset.id = lancamento.rateio_config_id;
        div.innerHTML = `
            <span class="input-group-text flex-grow-1">${escapeHTML(lancamento.rateio_config.classe_valor)}</span>
            <input type="number" class="form-control percentual" value="${lancamento.percentual}" min="0" max="100">
            <button class="btn btn-outline-danger btn-remover" type="button"><i data-lucide="trash"></i></button>`;
        div.querySelector('.btn-remover').addEventListener('click', () => {
            div.remove();
            this.atualizarTotal();
        });
        div.querySelector('.percentual').addEventListener('input', () => this.atualizarTotal());
        this.lancamentosContainer.appendChild(div);
        refreshIcons();
    }

    adicionarItem() {
        const configId = this.selectConfig.value;
        const percent = parseFloat(this.inputPercentual.value || '0');
        if (!configId || percent <= 0) return;
        const selected = this.selectConfig.selectedOptions[0].textContent;
        this.criarLinha({ rateio_config_id: parseInt(configId, 10), percentual: percent, rateio_config: { classe_valor: selected } });
        this.inputPercentual.value = '';
        this.atualizarTotal();
    }

    atualizarTotal() {
        const valores = Array.from(this.lancamentosContainer.querySelectorAll('.percentual')).map(i => parseFloat(i.value) || 0);
        const total = valores.reduce((a, b) => a + b, 0);
        this.totalPercentual.textContent = `${total}%`;
        this.progressBar.style.width = `${total}%`;
    }

    async salvar() {
        const instrutorId = this.selectInstrutor.value;
        const ano = parseInt(this.selectAno.value, 10);
        const mes = this.mesAtual;
        if (!instrutorId || !mes) return;
        const lancamentos = Array.from(this.lancamentosContainer.children).map(div => ({
            rateio_config_id: parseInt(div.dataset.id, 10),
            percentual: parseFloat(div.querySelector('.percentual').value || '0')
        }));
        try {
            await chamarAPI('/rateio/lancamentos', 'POST', { instrutor_id: parseInt(instrutorId, 10), ano, mes, lancamentos });
            const atualizados = await chamarAPI(`/rateio/lancamentos?instrutor_id=${instrutorId}&ano=${ano}&mes=${mes}`);
            this.dadosAno[mes] = atualizados;
            this.atualizarCard(mes);
            this.modal.hide();
            showToast('Lançamentos salvos!', 'success');
        } catch (e) {
            showToast(e.message, 'danger');
        }
    }

    atualizarCard(mes) {
        const card = this.gridContainer.querySelector(`[data-mes="${mes}"]`);
        if (!card) return;
        const dados = this.dadosAno[mes] || [];
        const total = dados.reduce((a, b) => a + b.percentual, 0);
        let badgeClass = 'bg-light text-dark border';
        let badgeText = 'Vazio';
        if (total === 100) {
            badgeClass = 'bg-success';
            badgeText = 'Completo (100%)';
        } else if (total > 0) {
            badgeClass = 'bg-warning';
            badgeText = `Parcial (${total}%)`;
        }
        const itens = dados.map(d => `<li class="list-group-item">${escapeHTML(d.rateio_config.classe_valor)}: ${d.percentual}%</li>`).join('');
        card.innerHTML = `
            <div class="card h-100 month-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${this.nomeMes(mes)}</h6>
                    <span class="badge ${badgeClass}">${badgeText}</span>
                </div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
                        ${itens || '<li class="list-group-item text-muted">Sem lançamentos</li>'}
                    </ul>
                </div>
                <div class="card-footer">
                    <button class="btn btn-primary btn-sm w-100" data-mes="${mes}">
                        <i data-lucide="pencil" class="me-1"></i> Gerenciar Lançamentos
                    </button>
                </div>
            </div>`;
        card.querySelector('button').addEventListener('click', () => this.abrirModal(mes));
        refreshIcons();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    new LancamentosApp();
});
