from app import create_app


def test_create_app_returns_app():
    app = create_app("development")
    assert app is not None
    assert app.config["DEBUG"] is True


def test_create_app_production_config():
    app = create_app("production")
    assert app.config["DEBUG"] is False


def test_create_app_defaults_without_config_name(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    app = create_app()
    assert app.config["DEBUG"] is True
