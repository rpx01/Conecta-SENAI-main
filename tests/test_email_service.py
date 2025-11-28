import importlib
from unittest.mock import patch

import pytest
from resend.exceptions import ResendError

import conecta_senai.services.email_service as email_service


def reload_service(
    monkeypatch,
    reply_to="reply@example.com",
    from_addr="no-reply@example.com",
):
    monkeypatch.setenv("RESEND_FROM", from_addr)
    monkeypatch.setenv("RESEND_REPLY_TO", reply_to)
    importlib.reload(email_service)
    return email_service


def test_address_normalization(monkeypatch):
    svc = reload_service(monkeypatch)
    with patch("conecta_senai.services.email_service.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "1"}
        svc.send_email(
            "a@example.com",
            "Oi",
            "<p>hi</p>",
            cc="c@example.com",
            bcc=["b@example.com"],
        )
        params = mock_send.call_args[0][0]
        assert params["to"] == ["a@example.com"]  # nosec B101
        assert params["cc"] == ["c@example.com"]  # nosec B101
        assert params["bcc"] == ["b@example.com"]  # nosec B101
        assert params["reply_to"] == "reply@example.com"  # nosec B101


def test_attachments(monkeypatch):
    svc = reload_service(monkeypatch)
    with patch("conecta_senai.services.email_service.resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "1"}
        attachments = [
            {"filename": "man.pdf", "path": "https://ex.com/man.pdf"},
            {"filename": "img.png", "content": "BASE64"},
        ]
        svc.send_email(
            ["a@example.com"],
            "Oi",
            "<p>hi</p>",
            attachments=attachments,
        )
        params = mock_send.call_args[0][0]
        assert params["attachments"] == attachments  # nosec B101


def test_error_propagation(monkeypatch):
    svc = reload_service(monkeypatch)

    class Boom(Exception):
        pass

    with patch(
        "conecta_senai.services.email_service.resend.Emails.send",
        side_effect=Boom("bad"),
    ):
        with pytest.raises(Boom):
            svc.send_email("a@example.com", "Oi", "<p>hi</p>")


def test_send_email_retries_on_rate_limit(monkeypatch, app):
    svc = reload_service(monkeypatch)
    monkeypatch.setattr(email_service.time_module, "sleep", lambda *_: None)

    calls = {"n": 0}

    def fake_send(params):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ResendError(
                code=429,
                error_type="rate_limit",
                message="Too many requests",
                suggested_action="",
            )
        return {"id": "123"}

    with patch(
        "conecta_senai.services.email_service.resend.Emails.send", side_effect=fake_send
    ) as mock_send:
        with app.app_context():
            result = svc.send_email("a@example.com", "Oi", "<p>oi</p>")
        assert result["id"] == "123"  # nosec B101
        assert mock_send.call_count == 2  # nosec B101
