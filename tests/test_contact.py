import threading
from unittest.mock import patch

from app.routes import EMAIL_THREAD_NAME

VALID = {"name": "Test User", "email": "test@example.com", "message": "Hello there"}


def test_success_returns_json(client):
    resp = client.post("/contact", data=VALID)
    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}


def join_email_thread(timeout=2):
    """The send is fire-and-forget; wait for it before asserting on the mock."""
    for thread in threading.enumerate():
        if thread.name == EMAIL_THREAD_NAME:
            thread.join(timeout)


def test_sends_when_api_key_is_configured(mail_client):
    with patch("app.routes.resend.Emails.send") as send:
        resp = mail_client.post("/contact", data=VALID)
        join_email_thread()
    assert resp.status_code == 200
    send.assert_called_once()
    payload = send.call_args[0][0]
    assert payload["to"] == "to@example.com"
    assert payload["from"] == "from@example.com"
    assert payload["reply_to"] == "test@example.com"


def test_dev_fallback_does_not_send(client):
    """With no API key, submissions are logged instead of emailed."""
    with patch("app.routes.resend.Emails.send") as send:
        resp = client.post("/contact", data=VALID)
    assert resp.status_code == 200
    send.assert_not_called()


def test_send_failure_is_logged_but_still_returns_success(mail_client, caplog):
    """A Resend outage must not surface as an error to the person submitting."""
    with patch("app.routes.resend.Emails.send", side_effect=RuntimeError("boom")):
        resp = mail_client.post("/contact", data=VALID)
        join_email_thread()
    assert resp.status_code == 200
    assert "Failed to send contact email" in caplog.text


def test_missing_name(client):
    resp = client.post("/contact", data={k: v for k, v in VALID.items() if k != "name"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_missing_email(client):
    resp = client.post("/contact", data={k: v for k, v in VALID.items() if k != "email"})
    assert resp.status_code == 400


def test_missing_message(client):
    resp = client.post("/contact", data={k: v for k, v in VALID.items() if k != "message"})
    assert resp.status_code == 400


def test_all_empty(client):
    resp = client.post("/contact", data={"name": "", "email": "", "message": ""})
    assert resp.status_code == 400


def test_whitespace_only_is_rejected(client):
    resp = client.post("/contact", data={"name": "   ", "email": "  ", "message": "\t"})
    assert resp.status_code == 400


def test_malformed_email_is_rejected(client):
    for bad in ("not-an-email", "missing@tld", "@example.com", "two@@example.com"):
        resp = client.post("/contact", data={**VALID, "email": bad})
        assert resp.status_code == 400, f"{bad!r} should be rejected"


def test_valid_email_shapes_are_accepted(client):
    for good in ("a@b.co", "first.last+tag@sub.example.com"):
        resp = client.post("/contact", data={**VALID, "email": good})
        assert resp.status_code == 200, f"{good!r} should be accepted"
