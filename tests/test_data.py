"""Validates the shape of app/data/*.yaml.

These are the checks that pay off day to day: content edits are the most
frequent change to this repo, and a typo here is what would otherwise reach
production. They assert structure, never specific copy, so swapping placeholder
content for real content doesn't break them.
"""
import re
from datetime import date

import pytest

from app.data.loader import FILES, load_all

URL_RE = re.compile(r"^https://\S+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


@pytest.fixture(scope="module")
def data():
    return load_all()


def test_every_declared_file_loads(data):
    assert set(data) == set(FILES)
    assert all(value is not None for value in data.values())


# --- band.yaml ---------------------------------------------------------------

def test_band_has_required_fields(data):
    band = data["band"]
    for key in ("name", "tagline", "hero_heading", "hero_subheading"):
        assert band.get(key), f"band.yaml is missing {key}"


def test_band_sections_have_headings_and_body(data):
    band = data["band"]
    assert band["who_we_are"]["heading"]
    assert len(band["who_we_are"]["paragraphs"]) >= 1
    assert all(p.strip() for p in band["who_we_are"]["paragraphs"])
    assert band["contact"]["heading"]
    assert band["contact"]["blurb"].strip()


# --- links.yaml --------------------------------------------------------------

def test_social_links_are_https_urls(data):
    links = data["links"]
    assert URL_RE.match(links["instagram"])
    assert URL_RE.match(links["facebook"])


def test_links_point_at_the_right_platforms(data):
    assert "instagram.com" in data["links"]["instagram"]
    assert "facebook.com" in data["links"]["facebook"]


def test_booking_email_is_well_formed(data):
    assert EMAIL_RE.match(data["links"]["email"])


# --- members.yaml ------------------------------------------------------------

def test_members_have_required_fields(data):
    assert len(data["members"]) >= 1
    for member in data["members"]:
        for key in ("name", "instrument", "bio"):
            assert member.get(key), f"member {member.get('name')!r} is missing {key}"


# --- shows.yaml --------------------------------------------------------------

def test_shows_have_required_fields(data):
    for show in data["shows"]:
        for key in ("date", "venue", "city", "time"):
            assert show.get(key), f"show at {show.get('venue')!r} is missing {key}"


def test_show_dates_parse_as_real_dates(data):
    """An unquoted YYYY-MM-DD becomes a date object; a typo stays a string."""
    for show in data["shows"]:
        assert isinstance(show["date"], date), (
            f"{show['venue']}: date {show['date']!r} is not a valid YYYY-MM-DD date"
        )


def test_show_times_are_strings(data):
    """Unquoted times like 8:00 are parsed as sexagesimal numbers by YAML."""
    for show in data["shows"]:
        assert isinstance(show["time"], str), (
            f"{show['venue']}: quote the time value in shows.yaml"
        )


def test_show_ticket_urls_are_valid_when_present(data):
    for show in data["shows"]:
        if "ticket_url" in show:
            assert URL_RE.match(show["ticket_url"]), f"{show['venue']}: bad ticket_url"


# --- videos.yaml -------------------------------------------------------------

def test_videos_have_required_fields(data):
    assert len(data["videos"]) >= 1
    for video in data["videos"]:
        assert video.get("title")
        assert video.get("description")


def test_youtube_ids_are_plausible(data):
    """Catches pasting a whole URL instead of just the ID."""
    for video in data["videos"]:
        assert YOUTUBE_ID_RE.match(str(video["youtube_id"])), (
            f"{video['title']}: youtube_id should be the 11-character ID only"
        )


# --- services.yaml / differentiators.yaml ------------------------------------

def test_services_have_name_and_description(data):
    assert len(data["services"]) >= 1
    for service in data["services"]:
        assert service.get("name")
        assert service.get("description")


def test_differentiators_have_title_and_description(data):
    assert len(data["differentiators"]) >= 1
    for item in data["differentiators"]:
        assert item.get("title")
        assert item.get("description")
