/* global Chart, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado */

(function () {
    let graficoStatus;
    let graficoTipos;
    let graficoUrgencia;
    let graficoTempos;
    let dadosBasedados = null;

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await carregarBasedados();
        await carregarIndicadores();
        configurarEventosFiltros();
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

    async function carregarBasedados() {
        try {
            dadosBasedados = await chamarAPI('/suporte_ti/basedados_formulario');
            preencherFiltros(dadosBasedados);
        } catch (error) {
            console.error('Erro ao carregar base de dados:', error);
        }
    }

    function preencherFiltros(dados) {
        // Preencher áreas
        const selectArea = document.getElementById('filtroArea');
        if (selectArea && dados?.areas) {
            dados.areas.forEach((area) => {
                const option = document.createElement('option');
                option.value = area;
                option.textContent = area;
                selectArea.appendChild(option);
            });
        }

        // Preencher tipos de equipamento
        const selectTipo = document.getElementById('filtroTipo');
        if (selectTipo && dados?.tipos_equipamento) {
            dados.tipos_equipamento.forEach((tipo) => {
                const option = document.createElement('option');
                option.value = tipo.id;
                option.textContent = tipo.nome;
                selectTipo.appendChild(option);
            });
        }
    }

    function configurarEventosFiltros() {
        const btnAplicar = document.getElementById('btnAplicarFiltros');
        const btnLimpar = document.getElementById('btnLimparFiltros');

        if (btnAplicar) {
            btnAplicar.addEventListener('click', aplicarFiltros);
        }

        if (btnLimpar) {
            btnLimpar.addEventListener('click', limparFiltros);
        }
    }

    async function aplicarFiltros() {
        const params = new URLSearchParams();

        const dataInicio = document.getElementById('filtroDataInicio')?.value;
        const dataFim = document.getElementById('filtroDataFim')?.value;
        const area = document.getElementById('filtroArea')?.value;
        const tipo = document.getElementById('filtroTipo')?.value;
        const urgencia = document.getElementById('filtroUrgencia')?.value;
        const status = document.getElementById('filtroStatus')?.value;

        if (dataInicio) params.append('data_inicio', dataInicio);
        if (dataFim) params.append('data_fim', dataFim);
        if (area) params.append('area', area);
        if (tipo) params.append('tipo_equipamento_id', tipo);
        if (urgencia) params.append('nivel_urgencia', urgencia);
        if (status) params.append('status', status);

        await carregarIndicadores(params.toString());
    }

    async function limparFiltros() {
        document.getElementById('filtroDataInicio').value = '';
        document.getElementById('filtroDataFim').value = '';
        document.getElementById('filtroArea').value = '';
        document.getElementById('filtroTipo').value = '';
        document.getElementById('filtroUrgencia').value = '';
        document.getElementById('filtroStatus').value = '';

        await carregarIndicadores();
    }

    async function carregarIndicadores(queryParams = '') {
        try {
            const url = queryParams
                ? `/suporte_ti/admin/indicadores?${queryParams}`
                : '/suporte_ti/admin/indicadores';
            const dados = await chamarAPI(url);
            atualizarCards(dados);
            atualizarNovosCards(dados);
            montarGraficos(dados);
            montarGraficoTempos(dados);
        } catch (error) {
            console.error(error);
        }
    }

    function atualizarCards(dados) {
        const total = dados?.total_chamados || 0;
        const porStatus = dados?.por_status || [];
        const abertos = somarStatus(porStatus, ['Aberto', 'Em Atendimento']);
        const finalizados = somarStatus(porStatus, ['Finalizado']);

        const indicadorTotal = document.getElementById('indicadorTotal');
        const indicadorAbertos = document.getElementById('indicadorAbertos');
        const indicadorFinalizados = document.getElementById('indicadorFinalizados');

        if (indicadorTotal) indicadorTotal.textContent = total;
        if (indicadorAbertos) indicadorAbertos.textContent = abertos;
        if (indicadorFinalizados) indicadorFinalizados.textContent = finalizados;
    }

    function atualizarNovosCards(dados) {
        console.log('Dados recebidos para novos cards:', dados);

        // Tempo médio até atendimento
        const tempoAtendimento = dados?.tempo_medio_abertura_para_atendimento_segundos || 0;
        console.log('Tempo atendimento (segundos):', tempoAtendimento);

        const { valor: valorAtend, unidade: unidadeAtend } = formatarTempo(tempoAtendimento);
        const indicadorTempoAtendimento = document.getElementById('indicadorTempoAtendimento');
        const unidadeTempoAtendimento = document.getElementById('unidadeTempoAtendimento');
        if (indicadorTempoAtendimento) indicadorTempoAtendimento.textContent = valorAtend;
        if (unidadeTempoAtendimento) unidadeTempoAtendimento.textContent = unidadeAtend;

        // Tempo médio até encerramento
        const tempoEncerramento = dados?.tempo_medio_abertura_para_encerramento_segundos || 0;
        console.log('Tempo encerramento (segundos):', tempoEncerramento);

        const { valor: valorEncer, unidade: unidadeEncer } = formatarTempo(tempoEncerramento);
        const indicadorTempoEncerramento = document.getElementById('indicadorTempoEncerramento');
        const unidadeTempoEncerramento = document.getElementById('unidadeTempoEncerramento');
        if (indicadorTempoEncerramento) indicadorTempoEncerramento.textContent = valorEncer;
        if (unidadeTempoEncerramento) unidadeTempoEncerramento.textContent = unidadeEncer;

        // Percentual atendidos em 24h
        const percentual24h = dados?.percentual_atendidos_em_24h || 0;
        console.log('Percentual 24h:', percentual24h);

        const indicadorSLA24h = document.getElementById('indicadorSLA24h');
        if (indicadorSLA24h) indicadorSLA24h.textContent = percentual24h.toFixed(1);
    }

    function formatarTempo(segundos) {
        console.log('formatarTempo chamada com:', segundos);

        if (segundos === 0 || segundos === null || segundos === undefined) {
            return { valor: '-', unidade: '' };
        }

        const horas = segundos / 3600;
        if (horas < 1) {
            const minutos = Math.round(segundos / 60);
            return { valor: minutos, unidade: 'minutos' };
        } else if (horas < 24) {
            return { valor: horas.toFixed(1), unidade: 'horas' };
        } else {
            const dias = horas / 24;
            return { valor: dias.toFixed(1), unidade: 'dias' };
        }
    }

    function somarStatus(lista, chaves) {
        const conjunto = new Set(chaves.map((c) => c.toLowerCase()));
        return lista
            .filter((item) => conjunto.has((item.status || '').toLowerCase()))
            .reduce((acc, item) => acc + (item.quantidade || 0), 0);
    }

    function montarGraficos(dados) {
        const coresStatus = ['#0d6efd', '#ffc107', '#198754', '#6c757d', '#6610f2'];
        const coresTipos = ['#6f42c1', '#198754', '#0dcaf0', '#fd7e14', '#d63384', '#20c997'];
        const coresUrgencia = ['#198754', '#ffc107', '#dc3545'];

        const ctxStatus = document.getElementById('graficoStatus');
        const ctxTipos = document.getElementById('graficoTipos');
        const ctxUrgencia = document.getElementById('graficoUrgencia');

        const dadosStatus = dados?.por_status || [];
        const dadosTipos = dados?.por_tipo_equipamento || [];
        const dadosUrgencia = dados?.por_nivel_urgencia || [];

        if (graficoStatus) graficoStatus.destroy();
        if (ctxStatus) {
            graficoStatus = new Chart(ctxStatus, {
                type: 'doughnut',
                data: {
                    labels: dadosStatus.map((item) => item.status),
                    datasets: [
                        {
                            data: dadosStatus.map((item) => item.quantidade),
                            backgroundColor: coresStatus.slice(0, dadosStatus.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                    },
                },
            });
        }

        if (graficoTipos) graficoTipos.destroy();
        if (ctxTipos) {
            graficoTipos = new Chart(ctxTipos, {
                type: 'bar',
                data: {
                    labels: dadosTipos.map((item) => item.tipo),
                    datasets: [
                        {
                            data: dadosTipos.map((item) => item.quantidade),
                            backgroundColor: coresTipos.slice(0, dadosTipos.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                            },
                        },
                    },
                    plugins: {
                        legend: { display: false },
                    },
                },
            });
        }

        if (graficoUrgencia) graficoUrgencia.destroy();
        if (ctxUrgencia) {
            graficoUrgencia = new Chart(ctxUrgencia, {
                type: 'bar',
                data: {
                    labels: dadosUrgencia.map((item) => item.nivel),
                    datasets: [
                        {
                            label: 'Chamados',
                            data: dadosUrgencia.map((item) => item.quantidade),
                            backgroundColor: coresUrgencia.slice(0, dadosUrgencia.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        },
                    },
                    plugins: {
                        legend: { display: false },
                    },
                },
            });
        }
    }

    function montarGraficoTempos(dados) {
        const ctxTempos = document.getElementById('graficoTempos');
        if (!ctxTempos) return;

        const dadosTempos = dados?.tempo_medio_por_urgencia || [];

        // Converter segundos para horas
        const labelsNiveis = dadosTempos.map((item) => item.nivel);
        const temposAtendimento = dadosTempos.map((item) => (item.tempo_atendimento / 3600).toFixed(2));
        const temposEncerramento = dadosTempos.map((item) => (item.tempo_encerramento / 3600).toFixed(2));

        if (graficoTempos) graficoTempos.destroy();

        graficoTempos = new Chart(ctxTempos, {
            type: 'bar',
            data: {
                labels: labelsNiveis,
                datasets: [
                    {
                        label: 'Tempo até atendimento (horas)',
                        data: temposAtendimento,
                        backgroundColor: '#0dcaf0',
                        borderColor: '#0dcaf0',
                        borderWidth: 1,
                    },
                    {
                        label: 'Tempo até encerramento (horas)',
                        data: temposEncerramento,
                        backgroundColor: '#6c757d',
                        borderColor: '#6c757d',
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Tempo (horas)',
                        },
                    },
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${context.parsed.y} horas`;
                            },
                        },
                    },
                },
            },
        });
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
