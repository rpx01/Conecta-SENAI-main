"""Serviços de criação e atualização dos horários de treinamentos."""

"""Serviços para gerenciamento de horários."""

from conecta_senai.models import db, Horario


def create_horario(data: dict) -> Horario:
    """Cria um novo registro de horário."""
    horario = Horario(
        nome=data["nome"].strip(),
        turno=data.get("turno"),
    )
    db.session.add(horario)
    db.session.commit()
    return horario


def update_horario(horario: Horario, data: dict) -> Horario:
    """Atualiza os campos do horário informado."""
    if data.get("nome") is not None:
        horario.nome = data["nome"].strip()
    if data.get("turno") is not None:
        horario.turno = data["turno"]
    db.session.commit()
    return horario
