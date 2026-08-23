"""Asserts on rendered HTML.

These guard the things a redesign can quietly break: the social links in the
banner, the hero video element, and every homepage section actually appearing.
"""
import pytest
from markupsafe import escape

from app.routes import split_shows


@pytest.fixture
def home(client):
    return client.get("/").data.decode()


# --- Banner and socials -------------------------------------------------------

def test_banner_links_to_both_socials(home, site_data):
    assert site_data["links"]["instagram"] in home
    assert site_data["links"]["facebook"] in home


def test_social_links_are_labelled_for_screen_readers(home, site_data):
    """Label text follows band.name, so renaming the band is a YAML edit only."""
    name = escape(site_data["band"]["name"])
    assert 'aria-label="%s on Instagram"' % name in home
    assert 'aria-label="%s on Facebook"' % name in home


def test_social_links_open_safely_in_a_new_tab(home):
    """target=_blank without rel=noopener hands the new tab control of ours."""
    assert home.count('rel="noopener noreferrer"') >= 2


def test_socials_are_inline_svg_not_images(home):
    assert "<svg" in home
    assert "<title>Instagram</title>" in home
    assert "<title>Facebook</title>" in home


@pytest.mark.parametrize("path,label", [
    ("/members", "Meet the Members"),
    ("/videos", "Videos"),
    ("/shows", "Upcoming Shows"),
    ("/book", "Book Us"),
])
def test_every_page_is_reachable_from_the_banner(home, path, label):
    assert f'href="{path}"' in home
    assert label in home


def test_current_page_is_marked_in_the_nav(client):
    body = client.get("/book").data.decode()
    assert 'aria-current="page"' in body


def test_mobile_nav_toggle_is_wired_for_accessibility(home):
    assert 'aria-expanded="false"' in home
    assert 'aria-controls="site-nav"' in home


# --- Hero ---------------------------------------------------------------------

def test_hero_renders_band_copy(home, site_data):
    assert site_data["band"]["hero_heading"] in home
    assert site_data["band"]["hero_subheading"] in home
    assert site_data["band"]["tagline"] in home


def test_hero_falls_back_to_gradient_when_no_clip_is_present(home):
    """No hero.mp4 yet — the section must render without a broken <video>."""
    assert "hero__scrim" in home
    assert "<video" not in home


def test_hero_video_renders_when_the_clip_exists(app, client, monkeypatch):
    monkeypatch.setitem(
        app.jinja_env.globals, "asset_exists", lambda p: p in ("hero.mp4", "hero.jpg")
    )
    body = client.get("/").data.decode()
    assert "<video" in body
    assert "muted" in body and "autoplay" in body and "loop" in body and "playsinline" in body
    assert "assets/hero.mp4" in body
    assert "poster=" in body


def test_hero_omits_poster_when_no_still_exists(app, client, monkeypatch):
    monkeypatch.setitem(app.jinja_env.globals, "asset_exists", lambda p: p == "hero.mp4")
    body = client.get("/").data.decode()
    assert "<video" in body
    assert "poster=" not in body


# --- Homepage sections --------------------------------------------------------

@pytest.mark.parametrize("heading", [
    "Who We Are", "Upcoming Shows", "What Sets Us Apart", "Our Services", "Get In Touch",
])
def test_homepage_has_every_section(home, heading):
    assert heading in home


def test_homepage_renders_the_bio_paragraphs(home, site_data):
    for paragraph in site_data["band"]["who_we_are"]["paragraphs"]:
        assert paragraph.strip()[:60] in home


def test_homepage_lists_services_and_differentiators(home, site_data):
    # Compare against escaped copy — an ampersand in a service name renders
    # as &amp;, which is Jinja doing the right thing.
    for service in site_data["services"]:
        assert str(escape(service["name"])) in home
    for item in site_data["differentiators"]:
        assert str(escape(item["title"])) in home


def test_homepage_has_a_contact_form_posting_to_contact(home):
    assert 'action="/contact"' in home
    assert 'name="name"' in home and 'name="email"' in home and 'name="message"' in home


# --- Shows --------------------------------------------------------------------

def test_shows_page_renders_a_card_per_upcoming_show(client, site_data):
    upcoming, _ = split_shows(site_data["shows"])
    body = client.get("/shows").data.decode()
    for show in upcoming:
        assert show["venue"] in body


def test_shows_page_separates_past_shows(client, site_data):
    upcoming, past = split_shows(site_data["shows"])
    body = client.get("/shows").data.decode()
    assert ("Past Shows" in body) == bool(past)
    assert body.count("show--past") == len(past)


def test_ticket_link_only_shown_when_a_show_has_one(client, site_data):
    upcoming, _ = split_shows(site_data["shows"])
    body = client.get("/shows").data.decode()
    for show in upcoming:
        if show.get("ticket_url"):
            assert show["ticket_url"] in body
    assert body.count(">Tickets<") == sum(1 for s in upcoming if s.get("ticket_url"))


def test_empty_state_when_nothing_is_scheduled(app, client):
    app.config["SITE_DATA"] = {**app.config["SITE_DATA"], "shows": []}
    body = client.get("/shows").data.decode()
    assert "No public shows on the books" in body
    assert "Past Shows" not in body


# --- Members ------------------------------------------------------------------

def test_members_page_lists_everyone(client, site_data):
    body = client.get("/members").data.decode()
    for member in site_data["members"]:
        assert str(escape(member["name"])) in body
        # Escaped: a role like "Lead Guitar / Sound & Lights" renders as &amp;.
        assert str(escape(member["instrument"])) in body


def test_members_fall_back_to_initials_without_a_photo(app, client, site_data, monkeypatch):
    """Every member has a photo today, so force the missing-file case.

    Asserting on the real asset folder would make this test flip whenever a
    photo is added or removed; the fallback itself is what needs guarding.
    """
    monkeypatch.setitem(app.jinja_env.globals, "asset_exists", lambda p: False)
    body = client.get("/members").data.decode()
    assert "member__initials" in body
    assert "member__photo" not in body
    for member in site_data["members"]:
        initials = "".join(word[0] for word in member["name"].split()[:2]).upper()
        assert initials in body


def test_member_photo_is_used_when_present(app, client, monkeypatch):
    monkeypatch.setitem(app.jinja_env.globals, "asset_exists", lambda p: True)
    body = client.get("/members").data.decode()
    assert "member__photo" in body
    assert 'loading="lazy"' in body
    assert "member__initials" not in body


# --- Videos -------------------------------------------------------------------

def test_videos_page_embeds_every_video(client, site_data):
    body = client.get("/videos").data.decode()
    for video in site_data["videos"]:
        assert f"embed/{video['youtube_id']}" in body
        assert video["title"] in body


def test_video_embeds_are_lazy_and_cookieless(client):
    body = client.get("/videos").data.decode()
    assert "youtube-nocookie.com" in body
    assert body.count('loading="lazy"') >= 1


# --- Book Us ------------------------------------------------------------------

def test_book_page_has_every_booking_field(client):
    body = client.get("/book").data.decode()
    for field in ("event_date", "event_type", "venue", "budget"):
        assert f'name="{field}"' in body


def test_book_page_event_types_come_from_services(client, site_data):
    body = client.get("/book").data.decode()
    for service in site_data["services"]:
        assert f'<option value="{escape(service["name"])}">' in body


def test_forms_carry_their_source_for_the_no_js_redirect(client):
    assert 'name="source" value="book"' in client.get("/book").data.decode()
    assert 'name="source" value="index"' in client.get("/").data.decode()


# --- Shared -------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/", "/members", "/videos", "/shows", "/book"])
def test_every_page_has_a_unique_title_and_the_stylesheet(client, path):
    body = client.get(path).data.decode()
    assert "css/main.css" in body
    assert "<title>" in body


def test_404_page_uses_the_site_chrome(client):
    body = client.get("/nope").data.decode()
    assert "Page Not Found" in body
    assert "banner__brand" in body
