# Twin Brooks Band Website

Marketing site for Twin Brooks — a homepage that shows prospective clients what we do,
plus pages for the members, videos, upcoming shows, and booking.

> **Status:** scaffolding in progress. See [plan.md](plan.md) for the full build plan and
> what's left to do.

## Stack

| Piece | Choice |
|---|---|
| Framework | Flask 3 + Jinja2 (server-rendered) |
| Content | YAML files in `app/data/` — no database |
| Email | [Resend](https://resend.com) API, with a dev fallback that logs instead of sends |
| Server | gunicorn |
| Hosting | Render (deferred — see [Deployment](#deployment)) |
| CI | GitHub Actions: flake8 + pytest with an 85% coverage gate |

## Quick start

```bash
make install          # creates .venv and installs dev dependencies
cp .env.example .env  # fill in as needed — all optional for local dev
make run              # http://127.0.0.1:5000
```

`make install` is a one-time step. After that, `make run` is all you need.

### Make targets

| Command | Does |
|---|---|
| `make install` | Create `.venv` and install from `requirements-dev.txt` |
| `make run` | Start the dev server with auto-reload |
| `make test` | Run the full pytest suite with coverage |
| `make lint` | flake8 over `app/` and `tests/` |

## Project structure

```
├── wsgi.py                 # gunicorn entrypoint
├── config.py               # environment-driven config classes
├── plan.md                 # build plan
├── app/
│   ├── __init__.py         # create_app() factory
│   ├── routes.py           # page routes, POST /contact, /health
│   ├── data/               # ← all site content lives here (YAML)
│   ├── templates/
│   │   ├── base.html       # banner nav with Instagram + Facebook links
│   │   └── partials/       # homepage sections
│   └── static/
│       ├── css/main.css
│       ├── js/main.js
│       └── assets/         # logo, photos, hero video
├── tests/
└── .github/workflows/      # ci.yml, keep_alive.yml
```

## Editing site content

**You do not need to touch HTML to update the site.** Everything that changes regularly
lives in `app/data/*.yaml`. Edit the file, commit, and the change is live on the next
deploy.

| File | Controls |
|---|---|
| `band.yaml` | Band name, tagline, the "who are we" copy |
| `members.yaml` | The Meet the Members page |
| `shows.yaml` | Upcoming Shows page and the homepage preview |
| `videos.yaml` | The Videos page |
| `services.yaml` | The Services section |
| `differentiators.yaml` | The "What Sets Us Apart" section |
| `links.yaml` | Social links, booking email, phone |

### Adding a show

Append an entry to `app/data/shows.yaml`:

```yaml
- date: 2026-09-12          # YYYY-MM-DD — must be a real date, CI checks this
  venue: The Bluebird
  city: Nashville, TN
  time: "8:00 PM"           # quote it, or YAML reads it as a number
  ticket_url: https://example.com/tickets
  note: 21+                 # optional
```

Shows are sorted by date automatically, and anything in the past drops off the Upcoming
list on its own — no cleanup needed.

### Adding a video

Grab the ID from the YouTube URL (`youtube.com/watch?v=`**`dQw4w9WgXcQ`**) and add it to
`app/data/videos.yaml`:

```yaml
- title: Live at The Basement
  youtube_id: dQw4w9WgXcQ
  description: Full set, March 2026
```

### Replacing the hero video

The homepage hero is a short, **silent, looping** clip — think moving wallpaper, not a
performance video. Keep it under ~2 MB. To convert a raw clip:

```bash
# 8-second silent loop starting at 0:12, scaled to 1280px wide
ffmpeg -ss 00:00:12 -t 8 -i raw.mov -an -vf scale=1280:-2 \
       -c:v libx264 -crf 28 -preset slow -movflags +faststart \
       app/static/assets/hero.mp4

# smaller WebM version browsers prefer when they support it
ffmpeg -i app/static/assets/hero.mp4 -an -c:v libvpx-vp9 -crf 36 -b:v 0 \
       app/static/assets/hero.webm

# poster frame shown before the video loads
ffmpeg -i app/static/assets/hero.mp4 -vframes 1 app/static/assets/hero.jpg
```

Full performances belong on the Videos page as YouTube embeds, not here — they cost us
nothing to serve that way.

## Environment variables

Copy `.env.example` to `.env`. **All of these are optional locally** — with no
`RESEND_API_KEY` set, contact and booking submissions are printed to the console instead
of emailed, so the forms are fully testable without any account.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing. Required in production. |
| `RESEND_API_KEY` | Resend API key. Blank = log submissions instead of sending. |
| `MAIL_RECIPIENT` | Where booking inquiries are delivered. |
| `MAIL_FROM` | Sender address. Requires a domain verified with Resend. |
| `FLASK_ENV` | `development` or `production`. |

`.env` is gitignored — never commit real keys.

## Testing

```bash
make test
```

The suite covers every route, the contact and booking endpoints (with Resend mocked), the
show date logic, and the rendered templates. It also validates the YAML content itself —
required fields present, dates parseable, social URLs well-formed — which is the check
that catches most real mistakes, since content edits are the most frequent change.

Coverage must stay at or above 85% or the run fails.

## Workflow

Work happens on `dev` and reaches `main` through a pull request:

```bash
git checkout dev
# ...make changes...
make lint && make test
git commit -am "Add September shows"
git push origin dev
gh pr create --base main
```

CI runs flake8 and pytest on every PR to `main` or `dev`, and must pass before merging.
`main` is the deploy branch — nothing lands there unreviewed.

## Deployment

Not yet live. Render will build from `main` with:

- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn wsgi:app`
- **Health check:** `/health`
- **Env vars:** the production values from the table above

A scheduled GitHub Action pings `/health` hourly, because Render's free tier sleeps after
15 minutes idle and takes roughly 50 seconds to wake — long enough that a prospective
client would assume the site is broken.
