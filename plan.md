# Twinbrooks Band Website — Build Plan

Marketing site for the band: a homepage that shows prospective clients what we do,
plus dedicated pages for members, videos, shows, and booking.

## Progress

| Phase | Status |
|---|---|
| 1 — Scaffolding & repo hygiene | ✅ Done |
| 2 — App core | ✅ Done |
| 3 — Templates & styling | ✅ Done |
| 4 — CI/CD | ✅ Done — PR #1 merged to `main` 2026-08-23, branch protection live |
| 5 — Content | 🔶 In progress — the lineup is real; band copy, shows, videos, links, and the hero clip still placeholder |

Phases 1–4 are merged to `main`. The site runs end to end on placeholder content: 113
tests pass, `app/` is at 100% coverage, and both CI legs are green. What remains is real
content and the Render deploy, both of which need input rather than code.

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

## Phase 1 — Scaffolding & repo hygiene ✅

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

Then create the `dev` branch. (Branch protection moved to Phase 4 — requiring a status
check that does not exist yet would block every merge.)

## Phase 2 — App core ✅

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

## Phase 3 — Templates & styling ✅

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
    ├── socials.html         # inline Instagram + Facebook SVGs, shared by nav and footer
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
so colors change in one block. Hamburger nav under 768px, driven by `static/js/main.js`,
which also submits both forms via `fetch()`.

**Graceful placeholders** — `static/assets/` is empty until Phase 5, so templates call an
`asset_exists()` Jinja global before referencing media: no hero file means the gradient
shows, no member photo means a designed placeholder shows. Dropping a real file in upgrades
the page with no template edit. Static URLs carry a `?v=<mtime>` stamp so a replaced file
busts the year-long cache.

**Hero video** — `<video muted autoplay loop playsinline preload="metadata">` with WebM +
MP4 sources and a JPG poster, plus an `ffmpeg` command to cut and compress the source clip
to ~1.5 MB. The poster shows instantly, so nothing looks broken on slow connections or
when iOS declines to autoplay.

### Tests

`test_templates.py`, grown one assertion at a time as each template is written — the
rendered HTML contains the Instagram and Facebook links, the hero `<video>` element, each
homepage section heading, and a show card per upcoming show.

`test_assets.py` came in alongside it, covering the two pieces the templates lean on:
`asset_exists()` (missing file, empty/`None` path, a directory) and the cache stamp
(present on real static files, changes with mtime, absent for unknown files).

## Phase 4 — CI/CD ✅

`.github/workflows/ci.yml` — on `pull_request` to `[main, dev]`: checkout →
setup-python (pip cache) → `pip install -r requirements-dev.txt` →
`flake8 app/ tests/ --max-line-length=100` → `pytest`.

Runs as a matrix over Python 3.10 and 3.12 — the version the site is developed on and the
one Render runs — which settles the version-drift open item without forcing a choice.

Branch protection on `main` lands here, once CI has reported once and the check names are
known: require a pull request and both CI legs passing.

**Outcome.** PR #1 (`dev` → `main`, phases 1–4) ran CI green on both legs and merged
2026-08-23 with a merge commit; `dev` was fast-forwarded to match. Protection on `main`
requires a pull request and the `Python 3.10` and `Python 3.12` contexts, and has
conversation resolution on. Both workflows are registered on the default branch — which is
what the merge was needed for, since GitHub only schedules `cron:` from `main`.

Because tests were written alongside each phase, the first CI run is a confirmation rather
than a discovery — the suite is already green locally.

`.github/workflows/keep_alive.yml` — hourly `curl` of `/health`, pointed at the real
domain once Render is live. Render's free tier sleeps after 15 minutes idle and takes
~50s to wake; this keeps the first visitor from waiting.

It reads the `SITE_URL` repository variable, which is deliberately unset: with no value it
logs a notice and exits 0 rather than failing hourly against a site that doesn't exist yet.
Verified by a manual `workflow_dispatch` run — succeeded, took the skip path. Setting
`SITE_URL` after the deploy is the only step needed to arm it.

Render deployment is deferred, but a `render.yaml` stub lands now and the env vars are
documented in the README so it's a five-minute job later.

## Phase 5 — Content ⬜

Everything ships with realistic placeholder YAML so the site runs end-to-end from day one,
then real content replaces it. Because `test_data.py` validates the shape rather than the
values, swapping placeholders for real content is checked automatically. Needed:

- [x] Band name, tagline, hero heading/subheading, and the "who are we" copy → `band.yaml`
- [x] Members: name, instrument, short bio, photo → `members.yaml` — all six, scraped
      from twinbrooks.band/the-members; photos in `app/static/assets/members/`
- [x] Shows: date, venue, city, set time, ticket link → `shows.yaml` — the three
      dates the live site lists; it gives no set times, and no city but Reston
- [~] Services and "what sets us apart" — in our own words → `services.yaml`,
      `differentiators.yaml`. The live site names four event types but carries no
      copy for them, so the descriptions are assembled from the band's own
      sentences and member credentials. Still wants a pass in their voice.
- [x] Instagram + booking email → `links.yaml`. No Facebook page and no phone
      number exist, so both keys are optional now rather than invented.
- [x] YouTube links for the Videos tab → `videos.yaml` — all four embeds
- [x] Band photos and the hero clip → `app/static/assets/`. The clip is the
      band's own landing-page loop: 1920x1080 and 39.8 MB at source, shipped at
      1280x720 / CRF 30 / no audio, 2.6 MB. An earlier `avconvert` pass got it to
      1.8 MB but only at 568x320, which was visibly soft stretched across the
      hero — the extra 0.7 MB buys back the resolution.
- [ ] A logo — the live site sets the wordmark in type, so there is no image to take

Then the Render deploy: create the Blueprint from `render.yaml`, fill the three
`sync: false` env vars, and set the `SITE_URL` repository variable to arm keep-alive.

---

## Open items

**Resend needs a verified domain.** Sending as `booking@twinbrooksband.com` requires
owning and verifying that domain with Resend. Until then it falls back to Resend's
`onboarding@resend.dev` sender (what `.env.example` ships with), and in dev everything logs
to the console — so nothing blocks the build.

**Python version drift is settled but not zero-cost.** Local dev is 3.10.20
(`.tool-versions`), Render is pinned to 3.12.7 (`render.yaml`), and CI runs both. Anything
that passes locally but not on 3.12 gets caught in the PR rather than in a deploy.
