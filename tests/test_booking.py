"""The Book Us form posts to the same /contact endpoint with extra fields."""
from unittest.mock import patch

from tests.test_contact import AJAX, join_email_thread

BOOKING = {
    "name": "Dana Reed",
    "email": "dana@example.com",
    "message": "Looking for a band for our reception.",
    "event_date": "2027-06-19",
    "event_type": "Wedding",
    "venue": "Union Station Hotel",
    "budget": "$3,000-4,000",
}


def build(**overrides):
    from app.routes import build_email

    return build_email({**BOOKING, **overrides})


def test_booking_fields_appear_in_the_body():
    _, body = build()
    assert "Event date: 2027-06-19" in body
    assert "Event type: Wedding" in body
    assert "Venue: Union Station Hotel" in body
    assert "Budget: $3,000-4,000" in body


def test_body_always_carries_name_email_and_message():
    _, body = build()
    assert "Name: Dana Reed" in body
    assert "Email: dana@example.com" in body
    assert "Looking for a band for our reception." in body


def test_booking_subject_identifies_it_as_a_booking():
    subject, _ = build()
    assert subject == "Booking inquiry from Dana Reed"


def test_plain_contact_subject_when_no_booking_fields():
    from app.routes import build_email

    subject, body = build_email({
        "name": "Sam", "email": "sam@example.com", "message": "Hi",
    })
    assert subject == "Contact from Sam"
    assert "Event date" not in body


def test_blank_booking_fields_are_omitted_not_printed_empty():
    _, body = build(venue="", budget="   ")
    assert "Venue:" not in body
    assert "Budget:" not in body
    assert "Event type: Wedding" in body


def test_partial_booking_still_counts_as_a_booking():
    subject, body = build(event_date="", venue="", budget="")
    assert subject == "Booking inquiry from Dana Reed"
    assert "Event type: Wedding" in body


def test_booking_fields_are_trimmed():
    _, body = build(venue="  The Grand Hall  ")
    assert "Venue: The Grand Hall" in body


def test_booking_post_reaches_the_email(mail_client):
    with patch("app.routes.resend.Emails.send") as send:
        resp = mail_client.post("/contact", data=BOOKING, headers=AJAX)
        join_email_thread()
    assert resp.status_code == 200
    payload = send.call_args[0][0]
    assert payload["subject"] == "Booking inquiry from Dana Reed"
    assert "Venue: Union Station Hotel" in payload["text"]
    assert payload["reply_to"] == "dana@example.com"


def test_booking_still_requires_the_core_fields(client):
    resp = client.post("/contact", data={**BOOKING, "message": ""}, headers=AJAX)
    assert resp.status_code == 400
