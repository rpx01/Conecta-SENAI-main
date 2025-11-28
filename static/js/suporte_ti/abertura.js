/* global bootstrap, chamarAPI, verificarAutenticacao, getUsuarioLogado, showToast */

(function () {
    const modalEl = document.getElementById('modalNovoChamado');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    const btnAbrirChamado = document.getElementById('btnAbrirChamado');
    const btnEnviarChamado = document.getElementById('btnEnviarChamado');
    const form = document.getElementById('formNovoChamado');
    const areaSelect = document.getElementById('areaSelect');
    const tipoSelect = document.getElementById('tipoEquipamentoSelect');
    const nivelUrgenciaSelect = document.getElementById('nivelUrgenciaSelect');
    const anexosInput = document.getElementById('anexosInput');
    const descricaoProblema = document.getElementById('descricaoProblema');
    const erroFormulario = document.getElementById('erroFormulario');
    const nomeUsuarioInput = document.getElementById('nomeUsuario');
    const emailUsuarioInput = document.getElementById('emailUsuario');

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) {
            return;
        }

        popularDadosUsuario();
        await carregarBaseDados();
    }

    function popularDadosUsuario() {
        const usuario = getUsuarioLogado();
        if (usuario) {
            const spanUser = document.getElementById('userName');
            if (spanUser) {
                spanUser.textContent = usuario.nome;
            }
            nomeUsuarioInput.value = usuario.nome;
            emailUsuarioInput.value = usuario.email;
        }
    }

    async function carregarBaseDados() {
        try {
            const dados = await chamarAPI('/suporte_ti/basedados_formulario');
            preencherSelect(areaSelect, dados.areas || [], 'nome');
            preencherSelect(tipoSelect, dados.tipos_equipamento || []);
        } catch (error) {
            console.error(error);
            showToast('Não foi possível carregar as opções do formulário.', 'danger');
        }
    }

    function preencherSelect(selectElement, itens, valueKey = 'id', labelKey = 'nome') {
        if (!selectElement) return;
        selectElement.innerHTML = '<option value="">Selecione...</option>';
        for (const item of itens) {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            selectElement.appendChild(option);
        }
    }

    function validarFormulario() {
        const erros = [];
        if (!areaSelect.value) {
            erros.push('Selecione a área de atendimento.');
        }
        if (!tipoSelect.value) {
            erros.push('Informe o tipo de equipamento.');
        }
        if (!descricaoProblema.value.trim()) {
            erros.push('Descreva o problema encontrado.');
        }
        if (!nivelUrgenciaSelect.value) {
            erros.push('Defina o nível de urgência.');
        }
        const arquivos = Array.from(anexosInput.files || []);
        if (arquivos.length > 5) {
            erros.push('Você pode anexar no máximo 5 imagens.');
        }
        if (erros.length > 0) {
            exibirErros(erros);
            return false;
        }
        ocultarErros();
        return true;
    }

    function exibirErros(erros) {
        if (!erroFormulario) return;
        erroFormulario.innerHTML = erros.map((msg) => `<p class="mb-1">${msg}</p>`).join('');
        erroFormulario.classList.remove('d-none');
    }

    function ocultarErros() {
        if (!erroFormulario) return;
        erroFormulario.classList.add('d-none');
        erroFormulario.textContent = '';
    }

    async function enviarChamado() {
        if (!validarFormulario()) {
            return;
        }
        const formData = new FormData(form);
        const arquivos = Array.from(anexosInput.files || []);
        formData.delete('anexos');
        arquivos.forEach((arquivo) => {
            formData.append('anexos', arquivo);
        });

        try {
            btnEnviarChamado && btnEnviarChamado.setAttribute('disabled', 'disabled');
            await chamarAPI('/suporte_ti/novo_chamado', 'POST', formData);
            showToast('Chamado criado com sucesso!', 'success');
            form.reset();
            popularDadosUsuario();
            ocultarErros();
            if (modal) {
                modal.hide();
            }
        } catch (error) {
            console.error(error);
            const mensagem = error?.payload?.erro || error.message || 'Erro ao abrir chamado.';
            const mensagens = Array.isArray(mensagem) ? mensagem : [mensagem];
            exibirErros(mensagens);
        } finally {
            btnEnviarChamado && btnEnviarChamado.removeAttribute('disabled');
        }
    }

    if (btnAbrirChamado && modal) {
        btnAbrirChamado.addEventListener('click', () => {
            ocultarErros();
            modal.show();
        });
    }

    if (btnEnviarChamado) {
        btnEnviarChamado.addEventListener('click', enviarChamado);
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
