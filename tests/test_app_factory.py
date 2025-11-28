from conecta_senai import create_app


def test_create_app(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "testing")
    monkeypatch.setenv("SCHEDULER_ENABLED", "0")
    app = create_app()
    assert app is not None
    with app.app_context():
        pass


def test_create_app_inicia_scheduler_por_padrao(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "testing")
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)

    chamado = {"valor": False}

    def fake_start(app):
        chamado["valor"] = True

    monkeypatch.setattr("conecta_senai.start_scheduler", fake_start)

    app = create_app()

    assert app.config["SCHEDULER_ENABLED"] is True
    assert chamado["valor"] is True


def test_create_app_nao_inicia_scheduler_quando_desativado(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "testing")
    monkeypatch.setenv("SCHEDULER_ENABLED", "0")
    monkeypatch.delenv("FLASK_ENV", raising=False)

    chamado = {"valor": False}

    def fake_start(app):
        chamado["valor"] = True

    monkeypatch.setattr("conecta_senai.start_scheduler", fake_start)

    app = create_app()

    assert app.config["SCHEDULER_ENABLED"] is False
    assert chamado["valor"] is False


def test_create_app_nao_inicia_scheduler_em_modo_teste(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "testing")
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)
    monkeypatch.setenv("FLASK_ENV", "testing")

    chamado = {"valor": False}

    def fake_start(app):
        chamado["valor"] = True

    monkeypatch.setattr("conecta_senai.start_scheduler", fake_start)

    app = create_app()

    assert app.config["SCHEDULER_ENABLED"] is False
    assert chamado["valor"] is False
