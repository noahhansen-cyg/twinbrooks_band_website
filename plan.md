# Twin Brooks Band Website — Build Plan

Marketing site for the band: a homepage that shows prospective clients what we do,
plus dedicated pages for members, videos, shows, and booking.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Stack | Flask 3 + Jinja2 | Server-rendered, minimal boilerplate, easy Render deploy via gunicorn |
| Content | YAML files in `app/data/` | Edit a text file and commit — no database, no admin login |
| Contact/booking | Resend API, async send, dev logging fallback | Mirrors `noahhansen_dev_website`; nothing to configure in dev |
| Hero video | Self-hosted silent looping MP4/WebM | GIF-like feel at ~1/10 the size (see note below) |
| Video gallery | YouTube embeds | Zero bandwidth cost from our server |
| Git flow | `dev` → PR → `main`, CI gates the merge | Same as the dev site; Render later deploys `main` only |
| Tests | Written alongside each phase, not batched at the end | Nothing ships untested; the suite is already green when CI first runs |

### Why not GIF

A 10-second 720p clip is roughly 8–15 MB as a GIF and 0.5–1.5 MB as an MP4. GIF is
capped at 256 colors, carries no audio, and uses 1980s compression. A
`<video muted autoplay loop playsinline>` tag behaves exactly like a GIF — silent,
looping, no controls — at a fraction of the bandwidth.

## Stack

Flask 3, Jinja2, PyYAML, flask-compress, resend, gunicorn. No database, no JS framework.

---

## Phase 1 — Scaffolding & repo hygiene

The repo and `origin` already exist, so this phase is files, not `git init`.

```
twinbrooks_band_website/
├── wsgi.py                     # create_app() entrypoint for gunicorn
├── config.py                   # Config / Development / Production
├── requirements.txt            # Flask, flask-compress, gunicorn, PyYAML, resend
├── requirements-dev.txt        # + pytest, pytest-cov, black, flake8
├── pyproject.toml              # pytest addopts, --cov-fail-under=85
├── Makefile                    # install / run / test / lint
├── .env.example                # RESEND_API_KEY, MAIL_RECIPIENT, MAIL_FROM, SECRET_KEY
├── .gitignore                  # .venv, .env, __pycache__, .coverage, .DS_Store
├── .tool-versions
└── README.md
```

### Tests

The harness goes in with the scaffolding so every later phase has somewhere to add to:

```
tests/
├── __init__.py
├── conftest.py         # app + client fixtures
└── test_smoke.py       # create_app() returns an app; /health → 200
```

`make test` must be green before Phase 1 is done. The coverage gate switches on at the end
of this phase, once there's real code to measure.

Then create the `dev` branch and enable branch protection on `main` requiring the CI check.

## Phase 2 — App core

```
app/
├── __init__.py         # create_app(): config, Compress, load_all() → SITE_DATA, blueprint, 404
├── routes.py           # page routes + POST /contact + /health
└── data/
    ├── loader.py              # _load(filename) → load_all() dict
    ├── band.yaml             # name, tagline, who-we-are copy, hero text
    ├── members.yaml          # name, instrument, photo, bio
    ├── shows.yaml            # date, venue, city, time, ticket_url, note
    ├── videos.yaml           # title, youtube_id, description
    ├── services.yaml         # weddings, corporate, private events, etc.
    ├── differentiators.yaml  # "what sets us apart"
    └── links.yaml            # instagram, facebook, email, phone
```

### Routes

| Route | Page |
|---|---|
| `GET /` | Home — hero video, who we are, upcoming shows, what sets us apart, services, contact |
| `GET /members` | Meet the members |
| `GET /videos` | Video gallery |
| `GET /shows` | Upcoming shows (full list + past archive) |
| `GET /book` | Book us — booking form |
| `POST /contact` | Form handler → JSON |
| `GET /health` | Render health check |

**Shows logic** — one helper, `split_shows()`, partitions `shows.yaml` on today's date
into upcoming (ascending) and past (descending), so an outdated show falls off the
homepage automatically without any edit.

**Contact/booking** — validate required fields → if `RESEND_API_KEY` is set, send the
email on a daemon thread so the request returns instantly; otherwise `logger.info` the
submission. Returns JSON so the form posts via `fetch()` without a page reload. The
booking form carries extra fields (event date, event type, venue, budget) formatted into
the email body.

### Tests

Written against each piece as it lands, not after the phase:

| File | Covers | Written with |
|---|---|---|
| `test_data.py` | Each YAML parses; required keys on every entry; dates are real dates; social URLs well-formed | `data/loader.py` + the YAML files |
| `test_shows.py` | `split_shows()` sorting, and the today-boundary case | `split_shows()` |
| `test_routes.py` | Every route → 200, unknown → 404, `/health` payload | each route as it's added |
| `test_contact.py` | Success with resend mocked; each missing field → 400; whitespace-only → 400; dev fallback doesn't call resend | `POST /contact` |
| `test_booking.py` | Booking-specific fields land in the email body | the booking form handler |

`test_data.py` is the one that pays off daily — it's what stops a typo'd show date from
reaching production, and content edits are the most frequent change to this repo.

Routes get a placeholder template early so `test_routes.py` can assert on them before
Phase 3 makes them look like anything.

## Phase 3 — Templates & styling

```
app/templates/
├── base.html           # banner nav + Instagram/Facebook SVG logos, footer
├── index.html
├── members.html
├── videos.html
├── shows.html
├── book.html
├── 404.html
└── partials/
    ├── hero.html            # <video muted autoplay loop playsinline poster=...>
    ├── who_we_are.html
    ├── shows_preview.html   # next 3 shows
    ├── differentiators.html
    ├── services.html
    ├── contact.html
    └── show_card.html       # shared by shows_preview + shows page
```

Banner socials are inline SVG (Instagram glyph + Facebook `f`) wrapped in
`<a target="_blank" rel="noopener noreferrer">`, URLs pulled from `links.yaml`, each with
an `aria-label`. Inline SVG rather than image files so they recolor on hover via CSS and
cost zero extra requests.

`static/css/main.css` — mobile-first, single file, CSS custom properties for the palette
so colors change in one block. Hamburger nav under 768px.

**Hero video** — `<video muted autoplay loop playsinline preload="metadata">` with WebM +
MP4 sources and a JPG poster, plus an `ffmpeg` command to cut and compress the source clip
to ~1.5 MB. The poster shows instantly, so nothing looks broken on slow connections or
when iOS declines to autoplay.

### Tests

`test_templates.py`, grown one assertion at a time as each template is written — the
rendered HTML contains the Instagram and Facebook links, the hero `<video>` element, each
homepage section heading, and a show card per upcoming show.

## Phase 4 — CI/CD

`.github/workflows/ci.yml` — on `pull_request` to `[main, dev]`: checkout →
setup-python 3.12 (pip cache) → `pip install -r requirements-dev.txt` →
`flake8 app/ tests/ --max-line-length=100` → `pytest tests/`.

Because tests were written alongside each phase, the first CI run is a confirmation rather
than a discovery — the suite is already green locally.

`.github/workflows/keep_alive.yml` — hourly `curl` of `/health`, pointed at the real
domain once Render is live. Render's free tier sleeps after 15 minutes idle and takes
~50s to wake; this keeps the first visitor from waiting.

Render deployment is deferred, but a `render.yaml` stub lands now and the env vars are
documented in the README so it's a five-minute job later.

## Phase 5 — Content

Everything ships with realistic placeholder YAML so the site runs end-to-end from day one,
then real content replaces it. Because `test_data.py` validates the shape rather than the
values, swapping placeholders for real content is checked automatically. Needed:

- [ ] Band name, tagline, and the "who are we" copy
- [ ] Members: name, instrument, short bio, photo
- [ ] Shows: date, venue, city, set time, ticket link
- [ ] Services and "what sets us apart" — in our own words
- [ ] Instagram + Facebook URLs, booking email, phone
- [ ] Logo, band photos, the hero clip (raw is fine — it gets compressed)
- [ ] YouTube links for the Videos tab

---

## Open items

**Python version drift.** Local is 3.10.20; the dev site's CI runs 3.12. Code will run on
both and CI pins 3.12 (Render's default), but matching the two is safer long-term.

**Resend needs a verified domain.** Sending as `booking@twinbrooksband.com` requires
owning and verifying that domain with Resend. Until then it falls back to Resend's
`onboarding@resend.dev` sender, and in dev everything logs to the console — so nothing
blocks the build.
