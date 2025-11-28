# flake8: noqa
"""Modelos relacionados a treinamentos."""

from datetime import datetime
from sqlalchemy import text
from conecta_senai.models import db


class LocalRealizacao(db.Model):
    """Locais disponíveis para realização de treinamentos."""

    __tablename__ = "locais_realizacao"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome}

    def __repr__(self):
        return f"<LocalRealizacao {self.nome}>"

class Treinamento(db.Model):
    """Modelo de treinamento oferecido."""

    __tablename__ = "treinamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    capacidade_maxima = db.Column(db.Integer)
    carga_horaria = db.Column(db.Integer)
    tem_pratica = db.Column(db.Boolean, nullable=False, default=False)
    links_materiais = db.Column(db.JSON)
    
    # NOVOS CAMPOS ADICIONADOS AQUI
    tipo = db.Column(db.String(50), nullable=True, default='Inicial') # Para 'Inicial' ou 'Periódico'
    conteudo_programatico = db.Column(db.Text, nullable=True)

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    turmas = db.relationship('TurmaTreinamento', back_populates='treinamento', lazy='dynamic')

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "capacidade_maxima": self.capacidade_maxima,
            "carga_horaria": self.carga_horaria,
            "tem_pratica": self.tem_pratica,
            "links_materiais": self.links_materiais or [],
            "tipo": self.tipo,
            "conteudo_programatico": self.conteudo_programatico,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
        }

    def __repr__(self):
        return f"<Treinamento {self.codigo}>"


class TurmaTreinamento(db.Model):
    """Turmas associadas a um treinamento."""

    __tablename__ = "turmas_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(
        db.Integer, db.ForeignKey("treinamentos.id"), nullable=False
    )
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)

    # Novos campos
    local_realizacao = db.Column(db.String(100))
    horario = db.Column(db.String(50))
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=True)
    teoria_online = db.Column(
        db.Boolean, nullable=False, server_default=text('FALSE'), default=False
    )

    # Relacionamentos
    treinamento = db.relationship(
        "Treinamento", back_populates='turmas'
    )
    instrutor = db.relationship('Instrutor')
    inscricoes = db.relationship('InscricaoTreinamento', backref='turma', lazy='dynamic')

    def to_dict(self):
        return {
            "id": self.id,
            "treinamento_id": self.treinamento_id,
            "data_inicio": self.data_inicio.isoformat() if self.data_inicio else None,
            "data_fim": (
                self.data_fim.isoformat() if self.data_fim else None
            ),
            "local_realizacao": self.local_realizacao,
            "horario": self.horario,
            "instrutor_id": self.instrutor_id,
            "instrutor_nome": self.instrutor.nome if self.instrutor else None,
            "teoria_online": self.teoria_online,
        }

    def __repr__(self):
        return f"<TurmaTreinamento {self.id} - Treinamento {self.treinamento_id}>"


class InscricaoTreinamento(db.Model):
    """Inscricoes de usuarios em turmas de treinamento."""

    __tablename__ = "inscricoes_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    turma_id = db.Column(
        db.Integer, db.ForeignKey("turmas_treinamento.id"), nullable=False
    )
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date)
    empresa = db.Column(db.String(150))
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

    # --- NOVOS CAMPOS ADICIONADOS AQUI ---
    nota_teoria = db.Column(db.Float, nullable=True)
    nota_pratica = db.Column(db.Float, nullable=True)
    status_aprovacao = db.Column(db.String(20), nullable=True)
    # --- NOVOS CAMPOS DE PRESENCA ---
    presenca_teoria = db.Column(db.Boolean, default=False, nullable=False)
    presenca_pratica = db.Column(db.Boolean, default=False, nullable=False)
    # ------------------------------------

    convocado_em = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship("User", backref="inscricoes_treinamento")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "turma_id": self.turma_id,
            "nome": self.nome,
            "email": self.email,
            "cpf": self.cpf,
            "data_nascimento": (
                self.data_nascimento.isoformat() if self.data_nascimento else None
            ),
            "empresa": self.empresa,
            "data_inscricao": (
                self.data_inscricao.isoformat() if self.data_inscricao else None
            ),
            # --- NOVOS CAMPOS ADICIONADOS AO DICIONÁRIO ---
            "nota_teoria": self.nota_teoria,
            "nota_pratica": self.nota_pratica,
            "status_aprovacao": self.status_aprovacao,
            "presenca_teoria": self.presenca_teoria,
            "presenca_pratica": self.presenca_pratica,
            "convocado_em": self.convocado_em.isoformat() if self.convocado_em else None,
            # ---------------------------------------------
        }

    def __repr__(self):
        return f"<InscricaoTreinamento {self.id} - Turma {self.turma_id}>"
