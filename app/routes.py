import os
import re
import threading
from datetime import date

import resend
from flask import (
    Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
)

main = Blueprint("main", __name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Named so tests can wait on the fire-and-forget send deterministically.
EMAIL_THREAD_NAME = "contact-email"

# Which page a submission came from, so a no-JS visitor is sent back to it.
# A fixed map rather than the Referer header — no open redirect.
_FORM_SOURCES = {
    "index": ("main.index", "#contact"),
    "book": ("main.book", ""),
}

# Extra fields the Book Us form sends. Absent on the homepage contact form.
_BOOKING_FIELDS = (
    ("event_date", "Event date"),
    ("event_type", "Event type"),
    ("venue", "Venue"),
    ("budget", "Budget"),
)


def split_shows(shows, today=None):
    """Partition shows into (upcoming, past) around today.

    Upcoming is ascending so the next show is first; past is descending so the
    most recent show is first. A show happening today counts as upcoming.
    """
    today = today or date.today()
    upcoming = sorted((s for s in shows if s["date"] >= today), key=lambda s: s["date"])
    past = sorted((s for s in shows if s["date"] < today), key=lambda s: s["date"], reverse=True)
    return upcoming, past


def build_email(form):
    """Turn a submitted form into an (subject, body) pair.

    The same endpoint serves the homepage contact form and the booking form;
    booking fields are included only when the form actually carried them.
    """
    name = form.get("name", "").strip()
    email = form.get("email", "").strip()
    message = form.get("message", "").strip()

    details = [(label, form.get(key, "").strip()) for key, label in _BOOKING_FIELDS]
    details = [(label, value) for label, value in details if value]

    subject = f"Booking inquiry from {name}" if details else f"Contact from {name}"

    lines = [f"Name: {name}", f"Email: {email}"]
    lines += [f"{label}: {value}" for label, value in details]
    lines += ["", message]
    return subject, "\n".join(lines)


def asset_exists(relpath):
    """True when a file exists under static/assets.

    Photos and the hero clip arrive with real content (Phase 5). Until then the
    templates fall back to a designed placeholder instead of a broken image, and
    upgrade on their own the moment a file is dropped in.
    """
    if not relpath:
        return False
    full = os.path.join(current_app.static_folder, "assets", relpath)
    return os.path.isfile(full)


def _site_data():
    return current_app.config["SITE_DATA"]


@main.route("/")
def index():
    data = _site_data()
    upcoming, _ = split_shows(data["shows"])
    return render_template("index.html", upcoming_shows=upcoming[:3], **data)


@main.route("/members")
def members():
    return render_template("members.html", **_site_data())


@main.route("/videos")
def videos():
    return render_template("videos.html", **_site_data())


@main.route("/shows")
def shows():
    data = _site_data()
    upcoming, past = split_shows(data["shows"])
    return render_template("shows.html", upcoming_shows=upcoming, past_shows=past, **data)


@main.route("/book")
def book():
    return render_template("book.html", **_site_data())


@main.route("/contact", methods=["POST"])
def contact():
    """Serves both the homepage contact form and the Book Us form.

    Answers JSON to the fetch() submit in main.js, and falls back to a
    flash-and-redirect for visitors without JavaScript.
    """
    wants_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def respond(message, category, status):
        if wants_json:
            key = "success" if category == "success" else "error"
            return jsonify({key: True if key == "success" else message}), status
        flash(message, category)
        endpoint, anchor = _FORM_SOURCES.get(
            request.form.get("source", ""), _FORM_SOURCES["index"]
        )
        return redirect(url_for(endpoint) + anchor, code=303)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return respond("Name, email, and message are all required.", "error", 400)

    if not _EMAIL_RE.match(email):
        return respond("Please enter a valid email address.", "error", 400)

    subject, body = build_email(request.form)

    if current_app.config.get("RESEND_API_KEY"):
        from_addr = current_app.config["MAIL_FROM"]
        to_addr = current_app.config["MAIL_RECIPIENT"]
        app = current_app._get_current_object()

        def send_async():
            try:
                resend.Emails.send({
                    "from": from_addr,
                    "to": to_addr,
                    "reply_to": email,
                    "subject": subject,
                    "text": body,
                })
            except Exception:
                app.logger.exception("Failed to send contact email")

        threading.Thread(target=send_async, name=EMAIL_THREAD_NAME, daemon=True).start()
    else:
        current_app.logger.info("[DEV] %s\n%s", subject, body)

    return respond("Thanks — we got your message and will be in touch soon.", "success", 200)


@main.route("/health")
def health():
    return jsonify({"status": "ok"})
