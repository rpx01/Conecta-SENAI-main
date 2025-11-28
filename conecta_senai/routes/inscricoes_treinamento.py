from flask import Blueprint, request, jsonify
from conecta_senai.models import db
from conecta_senai.models.inscricao_treinamento import (
    InscricaoTreinamentoFormulario,
)
from conecta_senai.schemas.inscricao_treinamento import InscricaoTreinamentoCreate

bp = Blueprint('inscricoes_treinamento', __name__, url_prefix='/api/inscricoes-treinamento')


@bp.post('')
def criar():
    data = request.get_json() or {}
    payload = InscricaoTreinamentoCreate(**data)

    ent = InscricaoTreinamentoFormulario(
        treinamento_id=payload.treinamento_id,
        nome_treinamento=payload.nome_treinamento,
        matricula=payload.matricula,
        tipo_treinamento=payload.tipo_treinamento,
        nome_completo=payload.nome_completo,
        naturalidade=payload.naturalidade,
        email=str(payload.email),
        data_nascimento=payload.data_nascimento,
        cpf=payload.cpf,
        empresa=payload.empresa,
    )
    db.session.add(ent)
    db.session.commit()
    return jsonify({'id': ent.id}), 201
