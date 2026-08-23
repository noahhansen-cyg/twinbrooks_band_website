"""asset_exists() decides whether a template shows real media or a placeholder."""
import os

from app.routes import asset_exists


def test_missing_file_is_false(app):
    with app.test_request_context():
        assert asset_exists("does-not-exist.mp4") is False


def test_existing_file_is_true(app, tmp_path):
    with app.test_request_context():
        assets = os.path.join(app.static_folder, "assets")
        os.makedirs(assets, exist_ok=True)
        probe = os.path.join(assets, "_probe.tmp")
        open(probe, "w").close()
        try:
            assert asset_exists("_probe.tmp") is True
        finally:
            os.remove(probe)


def test_empty_or_missing_path_is_false(app):
    """members.yaml may omit `photo` entirely — that must not raise."""
    with app.test_request_context():
        assert asset_exists("") is False
        assert asset_exists(None) is False


def test_a_directory_is_not_an_asset(app):
    with app.test_request_context():
        assert asset_exists("") is False
        assert asset_exists(".") is False


# --- Static cache busting -----------------------------------------------------

def test_static_urls_carry_a_version_stamp(client):
    """Without this, a year-long cache would pin visitors to stale CSS."""
    body = client.get("/").data.decode()
    assert "css/main.css?v=" in body
    assert "js/main.js?v=" in body


def test_version_stamp_changes_when_the_file_changes(app):
    from flask import url_for

    css = os.path.join(app.static_folder, "css", "main.css")
    with app.test_request_context():
        before = url_for("static", filename="css/main.css")
        stat = os.stat(css)
        os.utime(css, (stat.st_atime, stat.st_mtime + 60))
        try:
            after = url_for("static", filename="css/main.css")
        finally:
            os.utime(css, (stat.st_atime, stat.st_mtime))
    assert before != after


def test_unknown_static_file_is_not_stamped(app):
    from flask import url_for

    with app.test_request_context():
        assert "?v=" not in url_for("static", filename="css/nope.css")
