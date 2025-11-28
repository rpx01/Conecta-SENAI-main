(function () {
    const form = document.getElementById('formChamadoPublico');
    const areaSelect = document.getElementById('areaSelect');
    const tipoSelect = document.getElementById('tipoEquipamentoSelect');
    const btnEnviar = document.getElementById('btnEnviarChamado');
    const alertErros = document.getElementById('alertErros');
    const alertSucesso = document.getElementById('alertSucesso');

    async function carregarBaseDados() {
        try {
            const resposta = await fetch('/suporte/base-dados', {
                credentials: 'same-origin'
            });
            if (!resposta.ok) {
                throw new Error('Não foi possível carregar as opções do formulário.');
            }
            const dados = await resposta.json();
            preencherSelect(areaSelect, dados.areas || [], 'nome', 'nome');
            preencherSelect(tipoSelect, dados.tipos_equipamento || [], 'id', 'nome');
        } catch (error) {
            console.error(error);
            mostrarErros(['Falha ao carregar áreas e tipos de equipamento. Tente novamente mais tarde.']);
        }
    }

    function preencherSelect(selectEl, itens, valueKey = 'id', labelKey = 'nome') {
        if (!selectEl) return;
        selectEl.innerHTML = '<option value="">Selecione...</option>';
        itens.forEach((item) => {
            if (!item) return;
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            selectEl.appendChild(option);
        });

        const valorDesejado = (selectEl.dataset.selected || '').trim();
        if (valorDesejado) {
            const valorNormalizado = String(valorDesejado);
            const opcoes = Array.from(selectEl.options);
            const alvo = opcoes.find((opt) => String(opt.value) === valorNormalizado);
            if (alvo) {
                alvo.selected = true;
            }
        }
    }

    function validarFormulario() {
        const erros = [];
        if (!form) return erros;
        const nome = form.elements['nome_completo'].value.trim();
        const email = form.elements.email.value.trim();
        const area = areaSelect.value.trim();
        const tipo = tipoSelect.value.trim();
        const descricao = form.elements['descricao_problema'].value.trim();
        const urgencia = form.elements['nivel_urgencia'].value.trim();

        if (!nome) erros.push('Informe o nome completo.');
        if (!email || !email.includes('@')) erros.push('Informe um e-mail válido.');
        if (!area) erros.push('Selecione a área de atendimento.');
        if (!tipo) erros.push('Selecione o tipo de equipamento.');
        if (!descricao) erros.push('Descreva o problema encontrado.');
        if (urgencia && !['Baixo', 'Médio', 'Medio', 'Alto'].includes(urgencia)) {
            erros.push('Selecione um nível de urgência válido.');
        }
        return erros;
    }

    function mostrarErros(erros) {
        if (!alertErros) return;
        alertErros.innerHTML = erros.map((msg) => `<p class="mb-1">${sanitizeHTML(msg)}</p>`).join('');
        alertErros.classList.remove('d-none');
        alertSucesso?.classList.add('d-none');
    }

    function limparAlertas() {
        if (alertErros) {
            alertErros.classList.add('d-none');
            alertErros.textContent = '';
        }
        if (alertSucesso) {
            alertSucesso.classList.add('d-none');
            alertSucesso.textContent = '';
        }
    }

    function mostrarSucesso(mensagem) {
        if (!alertSucesso) return;
        alertSucesso.textContent = mensagem;
        alertSucesso.classList.remove('d-none');
        alertErros?.classList.add('d-none');
    }

    async function enviarFormulario(event) {
        event.preventDefault();
        limparAlertas();
        const erros = validarFormulario();
        if (erros.length) {
            mostrarErros(erros);
            return;
        }

        if (btnEnviar) {
            btnEnviar.disabled = true;
            btnEnviar.dataset.originalText = btnEnviar.dataset.originalText || btnEnviar.innerHTML;
            btnEnviar.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Enviando...';
        }

        try {
            const formData = new FormData(form);
            if (!formData.get('nivel_urgencia')) {
                formData.set('nivel_urgencia', 'Médio');
            }
            const resposta = await fetch('/suporte/abrir-chamado', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
            const payload = await resposta.json().catch(() => ({}));
            if (!resposta.ok) {
                const mensagens = Array.isArray(payload?.erro) ? payload.erro : [payload?.erro || 'Não foi possível registrar o chamado.'];
                mostrarErros(mensagens);
                return;
            }
            form.reset();
            mostrarSucesso(payload?.mensagem || 'Chamado registrado com sucesso. Verifique seu e-mail para acompanhar.');
        } catch (error) {
            console.error(error);
            mostrarErros(['Não foi possível enviar o chamado. Tente novamente mais tarde.']);
        } finally {
            if (btnEnviar) {
                btnEnviar.disabled = false;
                if (btnEnviar.dataset.originalText) {
                    btnEnviar.innerHTML = btnEnviar.dataset.originalText;
                }
            }
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (!form) return;
        carregarBaseDados();
        form.addEventListener('submit', enviarFormulario);
    });
})();
