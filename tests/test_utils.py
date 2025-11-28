from conecta_senai.utils.audit import log_action
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.schemas.user import _is_cpf_valid
from conecta_senai.models.audit_log import AuditLog


def test_is_cpf_valid():
    assert _is_cpf_valid('52998224725')
    assert not _is_cpf_valid('12345678900')


def test_log_action_creates_entry(app):
    with app.app_context():
        log_action(1, 'create', 'Entidade', 123, {'info': 'ok'})
        entry = AuditLog.query.filter_by(entity='Entidade', entity_id=123).first()
        assert entry is not None
        assert entry.details == {'info': 'ok'}


def test_handle_internal_error_returns_json(app):
    with app.app_context():
        resp, status = handle_internal_error(Exception('boom'))
        assert status == 500
        data = resp.get_json()
        assert data['erro'] == 'Ocorreu um erro interno do servidor'
        assert 'correlation_id' in data
