import threading
from unittest.mock import patch

from app.routes import EMAIL_THREAD_NAME

VALID = {"name": "Test User", "email": "test@example.com", "message": "Hello there"}

# main.js sets this header; the endpoint answers JSON when it is present and
# falls back to flash-and-redirect when it is not.
AJAX = {"X-Requested-With": "XMLHttpRequest"}


def post(client, data=None, **kwargs):
    return client.post("/contact", data=data if data is not None else VALID,
                       headers=AJAX, **kwargs)


def join_email_thread(timeout=2):
    """The send is fire-and-forget; wait for it before asserting on the mock."""
    for thread in threading.enumerate():
        if thread.name == EMAIL_THREAD_NAME:
            thread.join(timeout)


# --- JSON path (with JavaScript) ---------------------------------------------

def test_success_returns_json(client):
    resp = post(client)
    assert resp.status_code == 200
    assert resp.get_json() == {"success": True}


def test_sends_when_api_key_is_configured(mail_client):
    with patch("app.routes.resend.Emails.send") as send:
        resp = post(mail_client)
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
        resp = post(client)
    assert resp.status_code == 200
    send.assert_not_called()


def test_send_failure_is_logged_but_still_returns_success(mail_client, caplog):
    """A Resend outage must not surface as an error to the person submitting."""
    with patch("app.routes.resend.Emails.send", side_effect=RuntimeError("boom")):
        resp = post(mail_client)
        join_email_thread()
    assert resp.status_code == 200
    assert "Failed to send contact email" in caplog.text


# --- Validation ---------------------------------------------------------------

def test_missing_name(client):
    resp = post(client, {k: v for k, v in VALID.items() if k != "name"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_missing_email(client):
    resp = post(client, {k: v for k, v in VALID.items() if k != "email"})
    assert resp.status_code == 400


def test_missing_message(client):
    resp = post(client, {k: v for k, v in VALID.items() if k != "message"})
    assert resp.status_code == 400


def test_all_empty(client):
    resp = post(client, {"name": "", "email": "", "message": ""})
    assert resp.status_code == 400


def test_whitespace_only_is_rejected(client):
    resp = post(client, {"name": "   ", "email": "  ", "message": "\t"})
    assert resp.status_code == 400


def test_malformed_email_is_rejected(client):
    for bad in ("not-an-email", "missing@tld", "@example.com", "two@@example.com"):
        resp = post(client, {**VALID, "email": bad})
        assert resp.status_code == 400, f"{bad!r} should be rejected"


def test_valid_email_shapes_are_accepted(client):
    for good in ("a@b.co", "first.last+tag@sub.example.com"):
        resp = post(client, {**VALID, "email": good})
        assert resp.status_code == 200, f"{good!r} should be accepted"


# --- Redirect path (no JavaScript) -------------------------------------------

def test_without_js_success_redirects_instead_of_showing_json(client):
    resp = client.post("/contact", data={**VALID, "source": "index"})
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/#contact")


def test_without_js_booking_returns_to_the_book_page(client):
    resp = client.post("/contact", data={**VALID, "source": "book"})
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/book")


def test_without_js_unknown_source_falls_back_to_homepage(client):
    """A tampered or missing source must not become an open redirect."""
    for source in ("", "https://evil.example.com", "nonsense"):
        resp = client.post("/contact", data={**VALID, "source": source})
        assert resp.status_code == 303
        assert resp.headers["Location"].endswith("/#contact")


def test_without_js_validation_error_redirects_with_a_message(client):
    resp = client.post("/contact", data={**VALID, "email": "bad", "source": "book"},
                       follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please enter a valid email address." in resp.data


def test_without_js_success_message_is_shown_after_redirect(client):
    resp = client.post("/contact", data={**VALID, "source": "index"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"we got your message" in resp.data
