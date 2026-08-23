from datetime import date

from app.routes import split_shows

TODAY = date(2026, 8, 20)


def show(d, venue="Venue"):
    return {"date": d, "venue": venue, "city": "City", "time": "8:00 PM"}


def test_upcoming_is_ascending_so_next_show_is_first():
    shows = [show(date(2026, 12, 1)), show(date(2026, 9, 1)), show(date(2026, 10, 1))]
    upcoming, _ = split_shows(shows, today=TODAY)
    assert [s["date"] for s in upcoming] == [
        date(2026, 9, 1), date(2026, 10, 1), date(2026, 12, 1)
    ]


def test_past_is_descending_so_most_recent_is_first():
    shows = [show(date(2026, 1, 1)), show(date(2026, 7, 1)), show(date(2026, 4, 1))]
    _, past = split_shows(shows, today=TODAY)
    assert [s["date"] for s in past] == [
        date(2026, 7, 1), date(2026, 4, 1), date(2026, 1, 1)
    ]


def test_show_today_counts_as_upcoming():
    """A show tonight must stay on the homepage all day, not vanish at midnight."""
    upcoming, past = split_shows([show(TODAY)], today=TODAY)
    assert len(upcoming) == 1
    assert past == []


def test_yesterday_is_past():
    upcoming, past = split_shows([show(date(2026, 8, 19))], today=TODAY)
    assert upcoming == []
    assert len(past) == 1


def test_tomorrow_is_upcoming():
    upcoming, past = split_shows([show(date(2026, 8, 21))], today=TODAY)
    assert len(upcoming) == 1
    assert past == []


def test_partitions_a_mixed_list():
    shows = [show(date(2026, 5, 1)), show(date(2026, 9, 1)), show(TODAY)]
    upcoming, past = split_shows(shows, today=TODAY)
    assert len(upcoming) == 2
    assert len(past) == 1


def test_empty_list():
    assert split_shows([], today=TODAY) == ([], [])


def test_defaults_to_real_today_when_not_given():
    upcoming, past = split_shows([show(date(1999, 1, 1))])
    assert upcoming == []
    assert len(past) == 1


def test_does_not_mutate_input():
    shows = [show(date(2026, 12, 1)), show(date(2026, 9, 1))]
    original = list(shows)
    split_shows(shows, today=TODAY)
    assert shows == original
