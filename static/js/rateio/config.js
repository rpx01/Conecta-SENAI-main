let configEmEdicaoId = null;

function novaConfig() {
    document.getElementById('configForm').reset();
    configEmEdicaoId = null; 
    document.getElementById('modalConfigLabel').textContent = 'Nova Configuração';
    
    if (window.configModal) {
        window.configModal.show();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    
    if (!verificarAutenticacao() || !isAdmin()) {
        window.location.href = '/selecao-sistema.html';
        return;
    }

    const configModalEl = document.getElementById('configModal');
    window.configModal = new bootstrap.Modal(configModalEl); 
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    const form = document.getElementById('configForm');
    const tableBody = document.getElementById('configsTableBody');
    let configParaExcluirId = null;

    if (configModalEl) {
        configModalEl.addEventListener('hidden.bs.modal', () => {
            form.reset();
            configEmEdicaoId = null;
        });
    }

    async function carregarConfiguracoes() {
        try {
            const configs = await chamarAPI('/rateio-configs');
            tableBody.innerHTML = ''; 
            if (configs.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" class="text-center">Nenhuma configuração encontrada.</td></tr>`;
                return;
            }
            configs.forEach(config => {
                const tr = document.createElement('tr');
                tr.dataset.id = config.id;
                tr.innerHTML = `
                    <td>${escapeHTML(config.filial)}</td>
                    <td>${escapeHTML(config.uo)}</td>
                    <td>${escapeHTML(config.cr)}</td>
                    <td>${escapeHTML(config.classe_valor)}</td>
                    <td>${escapeHTML(config.descricao || '')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1 btn-editar" data-id="${config.id}" title="Editar">
                            <i data-lucide="pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-excluir" data-id="${config.id}" title="Excluir">
                            <i data-lucide="trash"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
            refreshIcons();
        } catch (error) {
            showToast(`Não foi possível carregar configurações: ${error.message}`, 'danger');
        }
    }

    function abrirModal(config = null) {
        form.reset();
        if (config) {
            configEmEdicaoId = config.id;
            document.getElementById('modalConfigLabel').textContent = 'Editar Configuração';
            document.getElementById('filial').value = config.filial;
            document.getElementById('uo').value = config.uo;
            document.getElementById('cr').value = config.cr;
            document.getElementById('classe_valor').value = config.classe_valor;
            document.getElementById('descricao').value = config.descricao || '';
        } else {
            configEmEdicaoId = null;
            document.getElementById('modalConfigLabel').textContent = 'Nova Configuração';
        }
        window.configModal.show();
    }

    document.getElementById('btnSalvarConfig').addEventListener('click', async () => {
        const dados = {
            filial: document.getElementById('filial').value,
            uo: document.getElementById('uo').value,
            cr: document.getElementById('cr').value,
            classe_valor: document.getElementById('classe_valor').value,
            descricao: document.getElementById('descricao').value
        };

        try {
            if (configEmEdicaoId) {
                await chamarAPI(`/rateio-configs/${configEmEdicaoId}`, 'PUT', dados);
                showToast('Configuração atualizada com sucesso!', 'success');
            } else {
                await chamarAPI('/rateio-configs', 'POST', dados);
                showToast('Configuração criada com sucesso!', 'success');
            }
            window.configModal.hide();
            carregarConfiguracoes();
        } catch (error) {
            showToast(`Não foi possível salvar: ${error.message}`, 'danger');
        }
    });

    tableBody.addEventListener('click', async (e) => {
        const btnEditar = e.target.closest('.btn-editar');
        const btnExcluir = e.target.closest('.btn-excluir');

        if (btnEditar) {
            const id = btnEditar.closest('tr').dataset.id;
            const config = await chamarAPI(`/rateio-configs/${id}`); 
            abrirModal(config);
        }

        if (btnExcluir) {
            configParaExcluirId = btnExcluir.closest('tr').dataset.id;
            document.getElementById('confirmacaoModalBody').textContent = 'Tem certeza que deseja excluir esta configuração? Esta ação não pode ser desfeita.';
            confirmacaoModal.show();
        }
    });

    document.getElementById('btnConfirmarExclusao').addEventListener('click', async () => {
        if (!configParaExcluirId) return;
        try {
            await chamarAPI(`/rateio-configs/${configParaExcluirId}`, 'DELETE');
            showToast('Configuração excluída com sucesso!', 'success');
            carregarConfiguracoes();
        } catch (error) {
            showToast(`Não foi possível excluir: ${error.message}`, 'danger');
        } finally {
            confirmacaoModal.hide();
            configParaExcluirId = null;
        }
    });

    carregarConfiguracoes();
});
