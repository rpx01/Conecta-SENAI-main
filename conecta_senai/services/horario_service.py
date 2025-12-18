from conecta_senai.models import Horario, db


def create_horario(data: dict) -> Horario:
    horario = Horario(
        nome=data["nome"].strip(),
        turno=data.get("turno"),
    )
    db.session.add(horario)
    db.session.commit()
    return horario


def update_horario(horario: Horario, data: dict) -> Horario:
    if data.get("nome") is not None:
        horario.nome = data["nome"].strip()
    if data.get("turno") is not None:
        horario.turno = data["turno"]
    db.session.commit()
    return horario
