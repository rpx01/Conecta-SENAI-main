/* global bootstrap, chamarAPI, verificarAutenticacao, getUsuarioLogado, formatarData, sanitizeHTML */

(function () {
    const tabela = document.querySelector('#tabelaChamados tbody');
    const alertaSemChamados = document.getElementById('alertSemChamados');
    const detalhesContainer = document.getElementById('detalhesChamado');
    const listaAnexos = document.getElementById('listaAnexos');
    const modalEl = document.getElementById('modalDetalhesChamado');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) {
            return;
        }
        atualizarNomeUsuario();
        await carregarChamados();
    }

    function atualizarNomeUsuario() {
        const usuario = getUsuarioLogado();
        if (usuario) {
            const span = document.getElementById('userName');
            if (span) {
                span.textContent = usuario.nome;
            }
        }
    }

    async function carregarChamados() {
        try {
            const chamados = await chamarAPI('/suporte_ti/meus_chamados');
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            mostrarMensagemErro('Não foi possível carregar seus chamados.');
        }
    }

    function mostrarMensagemErro(mensagem) {
        if (alertaSemChamados) {
            alertaSemChamados.textContent = mensagem;
            alertaSemChamados.classList.remove('alert-info');
            alertaSemChamados.classList.add('alert-danger');
            alertaSemChamados.classList.remove('d-none');
        }
    }

    function renderizarChamados(chamados) {
        if (!tabela) return;
        tabela.innerHTML = '';
        if (!Array.isArray(chamados) || chamados.length === 0) {
            if (alertaSemChamados) {
                alertaSemChamados.classList.remove('d-none');
                alertaSemChamados.classList.remove('alert-danger');
                alertaSemChamados.classList.add('alert-info');
                alertaSemChamados.innerHTML = '<i class="bi bi-info-circle me-2"></i>Ainda não há chamados cadastrados. Clique em "Abrir novo chamado" para criar o primeiro.';
            }
            return;
        }
        alertaSemChamados && alertaSemChamados.classList.add('d-none');
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(chamado.status)}">${sanitizeHTML(chamado.status || '-')}</span></td>
                <td><button class="btn btn-sm btn-outline-primary" data-id="${chamado.id}"><i class="bi bi-eye"></i></button></td>
            `;
            const botao = tr.querySelector('button');
            botao?.addEventListener('click', () => abrirModalDetalhes(chamado));
            tabela.appendChild(tr);
        });
    }

    function classeUrgencia(urgencia) {
        switch ((urgencia || '').toLowerCase()) {
            case 'alto':
                return 'danger';
            case 'médio':
            case 'medio':
                return 'warning';
            default:
                return 'secondary';
        }
    }

    function classeStatus(status) {
        switch ((status || '').toLowerCase()) {
            case 'aberto':
                return 'primary';
            case 'em atendimento':
                return 'warning';
            case 'finalizado':
                return 'success';
            case 'cancelado':
                return 'secondary';
            default:
                return 'secondary';
        }
    }

    function preencherDetalheTexto(elemento, valor) {
        if (!elemento) return;
        const placeholder = '-';
        if (valor === null || valor === undefined) {
            elemento.textContent = placeholder;
            return;
        }
        const texto = typeof valor === 'string' ? valor : String(valor);
        if (!texto.trim()) {
            elemento.textContent = placeholder;
            return;
        }
        const partes = texto.split(/\r?\n/);
        if (partes.length === 1) {
            elemento.textContent = partes[0];
            return;
        }
        elemento.innerHTML = '';
        partes.forEach((parte, index) => {
            if (index) {
                elemento.appendChild(document.createElement('br'));
            }
            elemento.appendChild(document.createTextNode(parte));
        });
    }

    function abrirModalDetalhes(chamado) {
        if (!detalhesContainer || !modal) return;
        detalhesContainer.innerHTML = '';
        const campos = [
            ['Protocolo', `#${chamado.id}`],
            ['Data de abertura', formatarData(chamado.created_at)],
            ['Área', chamado.area],
            ['Tipo de equipamento', chamado.tipo_equipamento_nome || '-'],
            ['Patrimônio', chamado.patrimonio || '-'],
            ['Número de série', chamado.numero_serie || '-'],
            ['Descrição', chamado.descricao_problema || '-'],
            ['Nível de urgência', chamado.nivel_urgencia || '-'],
            ['Status', chamado.status || '-'],
            ['Observações', chamado.observacoes || '-']
        ];
        campos.forEach(([label, valor]) => {
            const dt = document.createElement('dt');
            dt.className = 'col-sm-4 fw-semibold';
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.className = 'col-sm-8';
            preencherDetalheTexto(dd, valor);
            detalhesContainer.appendChild(dt);
            detalhesContainer.appendChild(dd);
        });
        renderizarAnexos(chamado.anexos || []);
        modal.show();
    }

    function renderizarAnexos(anexos) {
        if (!listaAnexos) return;
        listaAnexos.innerHTML = '';
        if (!anexos.length) {
            return;
        }
        const titulo = document.createElement('h3');
        titulo.className = 'h6 mt-3';
        titulo.textContent = 'Anexos';
        const lista = document.createElement('ul');
        lista.className = 'list-unstyled';
        anexos.forEach((caminho, index) => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = caminho;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = `Arquivo ${index + 1}`;
            li.appendChild(link);
            lista.appendChild(li);
        });
        listaAnexos.appendChild(titulo);
        listaAnexos.appendChild(lista);
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
