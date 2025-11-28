from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime
from conecta_senai.models import db


class InscricaoTreinamentoFormulario(db.Model):
    """Dados enviados pelo formulário público de inscrição em treinamentos.

    Essa classe coexistia com ``InscricaoTreinamento`` definida em
    ``treinamento.py``. Ambas compartilham o mesmo nome de classe e,
    consequentemente, o mesmo identificador dentro do registro do
    SQLAlchemy, o que causava o erro ``Multiple classes found for path`` ao
    inicializar os mapeamentos. Renomear a classe elimina o conflito e
    permite que os dois modelos representem tabelas distintas.
    """

    __tablename__ = 'inscricoes_treinamento_portal'
    id = Column(Integer, primary_key=True)
    treinamento_id = Column(Integer, nullable=True)
    nome_treinamento = Column(String(255), nullable=False)
    matricula = Column(String(50), nullable=False)
    tipo_treinamento = Column(String(100), nullable=False)
    nome_completo = Column(String(255), nullable=False)
    naturalidade = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    cpf = Column(String(14), nullable=False)
    empresa = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
