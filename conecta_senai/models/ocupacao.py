"""Modelo de ocupacao de sala."""
from datetime import datetime, date, time, timedelta

from conecta_senai.models import db
from .mixins import SerializerMixin

# Mapeamento padrão de turnos utilizado em diversos pontos do sistema
TURNOS_PADRAO = {
    'Manhã': (time.fromisoformat('08:00'), time.fromisoformat('12:00')),
    'Tarde': (time.fromisoformat('13:30'), time.fromisoformat('17:30')),
    'Noite': (time.fromisoformat('18:30'), time.fromisoformat('22:30')),
}

class Ocupacao(SerializerMixin, db.Model):
    """
    Modelo para representar as ocupações/agendamentos das salas de aula.
    """
    __tablename__ = 'ocupacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id'), nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    curso_evento = db.Column(db.String(200), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    grupo_ocupacao_id = db.Column(db.String(36), index=True)
    tipo_ocupacao = db.Column(db.String(50))  # aula_regular, evento_especial, reuniao, etc.
    recorrencia = db.Column(db.String(20), default='unica')  # unica, semanal, mensal
    status = db.Column(db.String(20), default='confirmado')  # confirmado, pendente, cancelado
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usuario = db.relationship('User', backref='ocupacoes_salas', lazy=True)
    
    def __init__(self, sala_id, usuario_id, curso_evento, data, horario_inicio, horario_fim,
                 instrutor_id=None, tipo_ocupacao=None, recorrencia='unica', status='confirmado', observacoes=None,
                 grupo_ocupacao_id=None):
        self.sala_id = sala_id
        self.instrutor_id = instrutor_id
        self.usuario_id = usuario_id
        self.curso_evento = curso_evento
        self.data = data if isinstance(data, date) else datetime.strptime(data, '%Y-%m-%d').date()
        self.horario_inicio = horario_inicio if isinstance(horario_inicio, time) else datetime.strptime(horario_inicio, '%H:%M').time()
        self.horario_fim = horario_fim if isinstance(horario_fim, time) else datetime.strptime(horario_fim, '%H:%M').time()
        self.tipo_ocupacao = tipo_ocupacao
        self.recorrencia = recorrencia
        self.status = status
        self.observacoes = observacoes
        self.grupo_ocupacao_id = grupo_ocupacao_id
    
    def get_duracao_minutos(self):
        """
        Calcula a duração da ocupação em minutos.
        """
        inicio_datetime = datetime.combine(date.today(), self.horario_inicio)
        fim_datetime = datetime.combine(date.today(), self.horario_fim)
        
        # Se o horário de fim for menor que o de início, assume que é no dia seguinte
        if fim_datetime <= inicio_datetime:
            fim_datetime = datetime.combine(date.today(), self.horario_fim) + timedelta(days=1)
        
        duracao = fim_datetime - inicio_datetime
        return int(duracao.total_seconds() / 60)
    
    def get_dia_semana(self):
        """
        Retorna o dia da semana da ocupação.
        """
        dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        return dias[self.data.weekday()]

    def get_turno(self):
        """Retorna o nome do turno baseado nos horários padrão."""
        for nome, (inicio, fim) in TURNOS_PADRAO.items():
            if self.horario_inicio == inicio and self.horario_fim == fim:
                return nome
        return None
    
    def is_conflito_com(self, outra_ocupacao):
        """
        Verifica se há conflito com outra ocupação.
        
        Parâmetros:
            outra_ocupacao: Outra instância de Ocupacao
        
        Retorna:
            bool: True se há conflito, False caso contrário
        """
        if (self.sala_id != outra_ocupacao.sala_id or 
            self.data != outra_ocupacao.data or
            self.id == outra_ocupacao.id):
            return False
        
        # Verifica sobreposição de horários
        return (
            (self.horario_inicio <= outra_ocupacao.horario_inicio < self.horario_fim) or
            (self.horario_inicio < outra_ocupacao.horario_fim <= self.horario_fim) or
            (outra_ocupacao.horario_inicio <= self.horario_inicio and outra_ocupacao.horario_fim >= self.horario_fim)
        )
    
    def pode_ser_editada_por(self, usuario):
        """
        Verifica se um usuário pode editar esta ocupação.
        
        Parâmetros:
            usuario: Instância de User
        
        Retorna:
            bool: True se pode editar, False caso contrário
        """
        if not usuario:
            return False
        
        # Administradores podem editar qualquer ocupação
        if usuario.is_admin():
            return True
        
        # Usuários comuns só podem editar suas próprias ocupações
        return self.usuario_id == usuario.id
    
    def get_cor_tipo(self):
        """
        Retorna a cor associada ao tipo de ocupação.
        """
        cores = {
            'aula_regular': '#006837',      # Verde FIEMG
            'evento_especial': '#FFB612',   # Amarelo FIEMG
            'reuniao': '#00539F',           # Azul FIEMG
            'manutencao': '#D50032',        # Vermelho FIEMG
            'reserva_especial': '#9C27B0'   # Roxo
        }
        return cores.get(self.tipo_ocupacao, '#888888')  # Cinza como padrão
    
    def to_dict(self, include_relations=True):
        """Converte a ocupação para dicionário serializável.

        Args:
            include_relations: inclui dados relacionados (sala, instrutor, usuário).
        """
        result = super().to_dict()
        result.update(
            {
                "duracao_minutos": self.get_duracao_minutos(),
                "dia_semana": self.get_dia_semana(),
                "turno": self.get_turno(),
                "cor_tipo": self.get_cor_tipo(),
            }
        )

        if include_relations:
            if self.sala:
                result.update(
                    {
                        "sala_nome": self.sala.nome,
                        "sala_capacidade": self.sala.capacidade,
                        "sala_localizacao": self.sala.localizacao,
                    }
                )
            if self.instrutor:
                result.update(
                    {
                        "instrutor_nome": self.instrutor.nome,
                        "instrutor_email": self.instrutor.email,
                    }
                )
            if self.usuario:
                result["usuario_nome"] = self.usuario.nome

        return result
    
    @staticmethod
    def buscar_conflitos(sala_id, data, horario_inicio, horario_fim, ocupacao_id=None, grupo_ocupacao_id=None):
        """
        Busca ocupações que conflitam com os parâmetros fornecidos.
        
        Parâmetros:
            sala_id: ID da sala
            data: Data da ocupação
            horario_inicio: Horário de início
            horario_fim: Horário de fim
            ocupacao_id: ID da ocupação a ser excluída (para edição)
            grupo_ocupacao_id: Grupo de ocupações a ser ignorado (edição de período)
        
        Retorna:
            list: Lista de ocupações conflitantes
        """
        query = Ocupacao.query.filter(
            Ocupacao.sala_id == sala_id,
            Ocupacao.data == data,
            Ocupacao.status.in_(['confirmado', 'pendente']),
            db.or_(
                db.and_(Ocupacao.horario_inicio <= horario_inicio, Ocupacao.horario_fim > horario_inicio),
                db.and_(Ocupacao.horario_inicio < horario_fim, Ocupacao.horario_fim >= horario_fim),
                db.and_(Ocupacao.horario_inicio >= horario_inicio, Ocupacao.horario_fim <= horario_fim)
            )
        )
        
        if ocupacao_id:
            query = query.filter(Ocupacao.id != ocupacao_id)

        if grupo_ocupacao_id:
            query = query.filter(Ocupacao.grupo_ocupacao_id != grupo_ocupacao_id)
        
        return query.all()
    
    @staticmethod
    def get_ocupacoes_periodo(data_inicio, data_fim, sala_id=None, instrutor_id=None):
        """
        Retorna ocupações em um período específico com filtros opcionais.
        
        Parâmetros:
            data_inicio: Data de início do período
            data_fim: Data de fim do período
            sala_id: ID da sala (opcional)
            instrutor_id: ID do instrutor (opcional)
        
        Retorna:
            list: Lista de ocupações no período
        """
        query = Ocupacao.query.filter(
            Ocupacao.data >= data_inicio,
            Ocupacao.data <= data_fim,
            Ocupacao.status.in_(['confirmado', 'pendente'])
        )
        
        if sala_id:
            query = query.filter(Ocupacao.sala_id == sala_id)
        
        if instrutor_id:
            query = query.filter(Ocupacao.instrutor_id == instrutor_id)
        
        return query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()
    
    def __repr__(self):
        return f'<Ocupacao {self.curso_evento} - {self.data} {self.horario_inicio}-{self.horario_fim}>'

