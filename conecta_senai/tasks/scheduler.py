"""Agendador de tarefas periódicas da aplicação Conecta SENAI."""

"""Background scheduler setup."""

import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING


scheduler = BackgroundScheduler()


def start_scheduler(app):
    """Start background scheduler if enabled."""
    intervalo = int(os.getenv("NOTIFICACAO_INTERVALO_MINUTOS", "60"))

    def job():
        from conecta_senai.tasks.jobs.notificacoes import _executar_lembretes

        with app.app_context():
            _executar_lembretes()

    scheduler.add_job(
        job,
        "interval",
        minutes=intervalo,
        id="lembretes_notificacoes",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    def convocacao_job():
        from conecta_senai.tasks.jobs.convocacao_automatica import convocacao_automatica_job

        with app.app_context():
            convocacao_automatica_job()

    scheduler.add_job(
        convocacao_job,
        "interval",
        hours=1,
        id="convocacao_automatica",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    def publicacao_noticias_job():
        from conecta_senai.tasks.jobs.noticias import publicar_noticias_agendadas

        with app.app_context():
            publicar_noticias_agendadas()

    scheduler.add_job(
        publicacao_noticias_job,
        "interval",
        minutes=5,
        id="publicar_noticias_agendadas",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    def limpeza_destaques_job():
        from conecta_senai.tasks.jobs.noticias import remover_destaques_expirados

        with app.app_context():
            remover_destaques_expirados()

    scheduler.add_job(
        limpeza_destaques_job,
        "cron",
        hour=3,
        minute=0,
        id="remover_destaques_expirados",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    if scheduler.state != STATE_RUNNING:
        scheduler.start()
        app.logger.info(
            "Scheduler de tarefas iniciado com %d jobs agendados.",
            len(scheduler.get_jobs()),
        )
    else:
        app.logger.debug("Scheduler já estava em execução; jobs atualizados.")

    app.extensions.setdefault("apscheduler", scheduler)
    return scheduler
