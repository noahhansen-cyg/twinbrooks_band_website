import pytest

PAGES = ["/", "/members", "/videos", "/shows", "/book"]


@pytest.mark.parametrize("path", PAGES)
def test_page_returns_200(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", PAGES)
def test_page_renders_html(client, path):
    resp = client.get(path)
    assert "text/html" in resp.content_type
    assert b"<html" in resp.data


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_unknown_route_renders_404_page(client):
    resp = client.get("/no-such-page")
    assert resp.status_code == 404
    assert b"Page Not Found" in resp.data


def test_contact_rejects_get(client):
    assert client.get("/contact").status_code == 405


def test_homepage_shows_at_most_three_upcoming(app, client):
    """The homepage previews the next few shows; /shows carries the full list."""
    from app.routes import split_shows

    upcoming, _ = split_shows(app.config["SITE_DATA"]["shows"])
    resp = client.get("/")
    shown = [s for s in upcoming[:3] if s["venue"].encode() in resp.data]
    assert len(shown) == min(3, len(upcoming))
    if len(upcoming) > 3:
        assert upcoming[3]["venue"].encode() not in resp.data
