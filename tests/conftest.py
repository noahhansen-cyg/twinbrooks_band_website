import pytest

from app import create_app


@pytest.fixture
def app():
    """App with mail disabled, so tests never depend on the developer's env."""
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["RESEND_API_KEY"] = ""
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mail_client(app):
    """Client with mail enabled, for asserting that sends are attempted."""
    app.config["RESEND_API_KEY"] = "test-key"
    app.config["MAIL_FROM"] = "from@example.com"
    app.config["MAIL_RECIPIENT"] = "to@example.com"
    return app.test_client()


@pytest.fixture
def site_data(app):
    return app.config["SITE_DATA"]
