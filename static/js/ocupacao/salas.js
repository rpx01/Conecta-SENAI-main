class GerenciadorSalas {
    constructor() {
        this.salasData = [];
        this.salaEditando = null;
        this.recursosSala = [];

        this.inicializar();
    }

    inicializar() {
        document.addEventListener('DOMContentLoaded', () => {
            this.carregarRecursosSala();
            this.carregarSalas();
        });

        const formSala = document.getElementById('formSala');
        if (formSala) {
            formSala.addEventListener('submit', e => {
                e.preventDefault();
                this.salvarSala();
            });
        }

        const btnConfirmarExclusao = document.getElementById('confirmarExcluirSala');
        if (btnConfirmarExclusao) {
            btnConfirmarExclusao.addEventListener('click', () => this.confirmarExclusaoSala());
        }
    }

    async carregarRecursosSala() {
        try {
            const response = await fetch(`${API_URL}/salas/recursos`, {
                headers: {
                }
            });
        
        if (response.ok) {
            this.recursosSala = await response.json();
            
            const container = document.getElementById('recursosContainer');
            container.innerHTML = '';
            
            this.recursosSala.forEach(recurso => {
                const col = document.createElement('div');
                col.className = 'col-md-4 col-sm-6';
                col.innerHTML = `
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" value="${recurso.valor}" id="recurso_${recurso.valor}" name="recursos">
                        <label class="form-check-label" for="recurso_${recurso.valor}">
                            ${recurso.nome}
                        </label>
                    </div>
                `;
                container.appendChild(col);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar recursos de sala:', error);
    }
    }

    async carregarSalas() {
        try {
            document.getElementById('loadingSalas').style.display = 'block';
            document.getElementById('listaSalas').style.display = 'none';
        
        const params = new URLSearchParams();
        
        const status = document.getElementById('filtroStatus').value;
        const capacidade = document.getElementById('filtroCapacidade').value;

        if (status) params.append('status', status);
        if (capacidade) params.append('capacidade_min', capacidade);
        
        const response = await fetch(`${API_URL}/salas?${params.toString()}`, {
            headers: {
            }
        });

        if (response.ok) {
            this.salasData = await response.json();
            
            const busca = document.getElementById('filtroBusca').value.toLowerCase();
            let salasFiltradas = this.salasData;
            
            if (busca) {
                salasFiltradas = this.salasData.filter(sala =>
                    sala.nome.toLowerCase().includes(busca) ||
                    (sala.localizacao && sala.localizacao.toLowerCase().includes(busca))
                );
            }
            
            this.renderizarTabelaSalas(salasFiltradas);
        } else {
            const erro = await response.json().catch(() => ({}));
            throw new Error(erro.erro || `Erro ${response.status}`);
        }
    } catch (error) {
        console.error('Erro ao carregar salas:', error);
        let mensagem = 'Não conseguimos carregar as salas.';
        if (error.message.includes('Failed to fetch')) {
            mensagem += ' Verifique sua conexão e tente novamente.';
        } else {
            mensagem += ` ${error.message}`;
        }
        showToast(mensagem, 'danger');
    } finally {
        document.getElementById('loadingSalas').style.display = 'none';
    }
}

    renderizarTabelaSalas(salas) {
    const tbody = document.getElementById('tabelaSalas');
    
    tbody.innerHTML = '';

    if (!salas || salas.length === 0) {
        const colCount = tbody.closest('table').querySelector('thead tr').childElementCount;
        tbody.innerHTML = `<tr><td colspan="${colCount}" class="text-center py-4">Nenhuma sala encontrada.</td></tr>`;
        document.getElementById('listaSalas').style.display = 'block';
        return;
    }

    document.getElementById('listaSalas').style.display = 'block';

    salas.forEach(sala => {
        const statusBadge = sala.status === 'ativa'
            ? `<span class="badge bg-success">Ativa</span>`
            : sala.status === 'manutencao'
                ? `<span class="badge bg-warning">Manutenção</span>`
                : `<span class="badge bg-secondary">Inativa</span>`;

        const row = `
            <tr>
                <td>${sala.id}</td>
                <td><strong>${escapeHTML(sala.nome)}</strong></td>
                <td>${Array.isArray(sala.recursos) && sala.recursos.length > 0 ? sala.recursos.map(r => escapeHTML(r)).join(', ') : '-'}</td>
                <td>${sala.capacidade}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary" title="Editar Sala" onclick="gerenciadorSalas.editarSala(${sala.id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger" title="Excluir Sala" onclick="gerenciadorSalas.excluirSala(${sala.id}, '${escapeHTML(sala.nome)}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', row);
    });
}

    getStatusBadge(status) {
    const badges = {
        'ativa': '<span class="badge bg-success">Ativa</span>',
        'inativa': '<span class="badge bg-secondary">Inativa</span>',
        'manutencao': '<span class="badge bg-warning">Manutenção</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">-</span>';
    }

    aplicarFiltros() {
    this.carregarSalas();
    }

    limparFiltros() {
        document.getElementById('filtroStatus').value = '';
        document.getElementById('filtroCapacidade').value = '';
        document.getElementById('filtroBusca').value = '';
    this.carregarSalas();
    }

    novaSala() {
    this.salaEditando = null;
    document.getElementById('modalSalaLabel').textContent = 'Nova Sala';
    document.getElementById('btnSalvarTexto').textContent = 'Salvar';
    document.getElementById('formSala').reset();
    document.getElementById('salaId').value = '';
    
    this.recursosSala.forEach(recurso => {
        const checkbox = document.getElementById(`recurso_${recurso.valor}`);
        if (checkbox) checkbox.checked = false;
    });
    }

    coletarRecursosSelecionados() {
        return Array.from(
            document.querySelectorAll('#formSala input[name="recursos"]:checked')
        ).map(cb => cb.value);
    }

    async editarSala(id) {
    try {
        const response = await fetch(`${API_URL}/salas/${id}`, {
            headers: {
            }
        });
        
        if (response.ok) {
            const sala = await response.json();
            this.salaEditando = sala;
            
            document.getElementById('modalSalaLabel').textContent = 'Editar Sala';
            document.getElementById('btnSalvarTexto').textContent = 'Atualizar';
            document.getElementById('salaId').value = sala.id;
            document.getElementById('salaNome').value = sala.nome;
            document.getElementById('salaCapacidade').value = sala.capacidade;
            document.getElementById('salaLocalizacao').value = sala.localizacao || '';
            document.getElementById('salaStatus').value = sala.status;
            document.getElementById('salaObservacoes').value = sala.observacoes || '';
            
            this.recursosSala.forEach(recurso => {
                const checkbox = document.getElementById(`recurso_${recurso.valor}`);
                if (checkbox) {
                    const lista = Array.isArray(sala.recursos) ? sala.recursos : [];
                    checkbox.checked = lista.includes(recurso.valor);
                }
            });
            
            const modal = new bootstrap.Modal(document.getElementById('modalSala'));
            modal.show();
        } else {
            throw new Error('Erro ao carregar dados da sala');
        }
    } catch (error) {
        console.error('Erro ao editar sala:', error);
        showToast('Não foi possível carregar os dados da sala.', 'danger');
    }
}

    async salvarSala() {
    const btn = document.getElementById('btnSalvarSala');
    const spinner = btn ? btn.querySelector('.spinner-border') : null;
    if (btn && spinner) {
        btn.disabled = true;
        spinner.classList.remove('d-none');
    }
    try {
        
        const recursos = this.coletarRecursosSelecionados();

        const formData = {
            nome: document.getElementById('salaNome').value.trim(),
            capacidade: parseInt(document.getElementById('salaCapacidade').value),
            localizacao: document.getElementById('salaLocalizacao').value,
            status: document.getElementById('salaStatus').value,
            observacoes: document.getElementById('salaObservacoes').value.trim(),
            recursos: recursos
        };
        
        if (!formData.nome) {
            showToast('Informe o nome da sala para continuar.', 'warning');
            return;
        }
        
        if (!formData.capacidade || formData.capacidade <= 0) {
            showToast('A capacidade precisa ser um número maior que zero.', 'warning');
            return;
        }
        
        const salaId = document.getElementById('salaId').value;
        const isEdicao = salaId !== '';
        
        const response = await fetch(`${API_URL}/salas${isEdicao ? `/${salaId}` : ''}`, {
            method: isEdicao ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast(`Sala ${isEdicao ? 'atualizada' : 'criada'} com sucesso!`, 'success');

            const modal = bootstrap.Modal.getInstance(document.getElementById('modalSala'));
            modal.hide();

            this.novaSala();

            this.carregarSalas();
        } else {
            let mensagemErro = 'Ocorreu um erro desconhecido.';
            if (result.detail && Array.isArray(result.detail)) {
                mensagemErro = 'Erro de validação: ' + result.detail
                    .map(e => `Campo '${e.loc.join('.')}' - ${e.msg}`)
                    .join('; ');
            } else if (typeof result.detail === 'string') {
                mensagemErro = result.detail;
            } else if (Array.isArray(result.erro)) {
                mensagemErro = 'Erro de validação: ' + result.erro
                    .map(e => `Campo '${e.loc.join('.')}' - ${e.msg}`)
                    .join('; ');
            } else if (typeof result.erro === 'string') {
                mensagemErro = result.erro;
            } else if (result.message) {
                mensagemErro = result.message;
            }

            throw new Error(mensagemErro);
        }
    } catch (error) {
        console.error('Erro ao salvar sala:', error);
            showToast(`Não conseguimos salvar a sala: ${error.message}`, 'danger');
    } finally {
        if (btn && spinner) {
            btn.disabled = false;
            spinner.classList.add('d-none');
        }
    }
}

    excluirSala(id, nome) {
    document.getElementById('nomeSalaExcluir').textContent = nome;
    document.getElementById('modalExcluirSala').setAttribute('data-sala-id', id);
    
    const modal = new bootstrap.Modal(document.getElementById('modalExcluirSala'));
    modal.show();
}

    async confirmarExclusaoSala() {
    try {
        const salaId = document.getElementById('modalExcluirSala').getAttribute('data-sala-id');
        
        const response = await fetch(`${API_URL}/salas/${salaId}`, {
            method: 'DELETE',
            headers: {
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Sala excluída com sucesso!', 'success');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalExcluirSala'));
            modal.hide();
            
            this.carregarSalas();
        } else {
            throw new Error(result.erro || 'Erro ao excluir sala');
        }
    } catch (error) {
        console.error('Erro ao excluir sala:', error);
        showToast(`Não conseguimos excluir a sala: ${error.message}`, 'danger');
    }
}

    verOcupacoesSala(id) {
        
        window.location.href = `/ocupacao/calendario.html?sala_id=${id}`;
    }

}

window.gerenciadorSalas = new GerenciadorSalas();

