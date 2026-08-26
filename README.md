# Twinbrooks Band Website

Marketing site for Twinbrooks — a homepage that shows prospective clients what we do,
plus pages for the members, videos, upcoming shows, and booking.

> **Status:** phases 1–4 are done and merged to `main` — the app, templates, test suite,
> and CI/CD are all in place. What's left is Phase 5: swapping the placeholder YAML in
> `app/data/` for real content and doing the first Render deploy. See [plan.md](plan.md).

## Stack

| Piece | Choice |
|---|---|
| Framework | Flask 3 + Jinja2 (server-rendered) |
| Content | YAML files in `app/data/` — no database |
| Email | [Resend](https://resend.com) API, with a dev fallback that logs instead of sends |
| Server | gunicorn |
| Hosting | Render (deferred — see [Deployment](#deployment)) |
| CI | GitHub Actions: flake8 + pytest on Python 3.10 and 3.12, 85% coverage gate |

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
| `make format` | black over `app/` and `tests/` |

## Project structure

```
├── wsgi.py                 # gunicorn entrypoint
├── config.py               # environment-driven config classes
├── render.yaml             # Render blueprint (deploy settings, in review-able form)
├── plan.md                 # build plan
├── app/
│   ├── __init__.py         # create_app() factory, static cache busting, 404
│   ├── routes.py           # page routes, POST /contact, /health, split_shows()
│   ├── data/               # ← all site content lives here (YAML)
│   ├── templates/
│   │   ├── base.html       # banner nav, footer
│   │   └── partials/       # homepage sections + socials.html (inline SVG icons)
│   └── static/
│       ├── css/main.css    # single mobile-first stylesheet
│       ├── js/main.js      # hamburger nav + fetch() form submit
│       └── assets/         # logo, photos, hero video — empty until Phase 5
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

`links.yaml` needs `instagram` and `email`. `facebook` and `phone` are optional —
add either key and it appears on its own (the Facebook icon in the nav and footer, the
phone on the contact and booking forms).

### Adding a show

Append an entry to `app/data/shows.yaml`:

```yaml
- date: 2026-09-12          # YYYY-MM-DD — must be a real date, CI checks this
  venue: The Bluebird
  city: Nashville, TN       # optional
  time: "8:00 PM"           # optional — quote it, or YAML reads it as a number
  ticket_url: https://example.com/tickets   # optional
  note: 21+                 # optional
```

Only `date` and `venue` are required; the card leaves out whatever is missing.

Shows are sorted by date automatically, and anything in the past drops off the Upcoming
list on its own — no cleanup needed.

### Media is optional until you have it

`static/assets/` is empty right now, and nothing looks broken because of it. Templates ask
`asset_exists()` before referencing a file: the hero falls back to a gradient, and a member
without a `photo` gets a designed placeholder rather than a broken image. Drop `hero.mp4`
or a member photo into `app/static/assets/` and that section upgrades itself on the next
request — no template edit.

Static URLs also carry a `?v=<mtime>` stamp, so a replaced file busts the year-long browser
cache on its own.

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
performance video. Aim for under ~3 MB at 1280px wide; dropping the resolution to hit a
smaller number reads as blurry once it is stretched full-bleed. To convert a raw clip:

```bash
# Silent loop scaled to 1280px wide — the settings the current hero.mp4 uses.
# Add -ss 00:00:12 -t 8 before -i to cut a shorter section out of a long clip.
ffmpeg -i raw.mov -an -vf scale=1280:-2 \
       -c:v libx264 -profile:v high -crf 30 -preset slow -pix_fmt yuv420p \
       -movflags +faststart \
       app/static/assets/hero.mp4

# smaller WebM version browsers prefer when they support it
ffmpeg -i app/static/assets/hero.mp4 -an -c:v libvpx-vp9 -crf 36 -b:v 0 \
       app/static/assets/hero.webm

# poster frame shown before the video loads
ffmpeg -i app/static/assets/hero.mp4 -vframes 1 app/static/assets/hero.jpg
```

Full performances belong on the Videos page as YouTube embeds, not here — they cost us
nothing to serve that way.

### Changing the colors

The palette is a light, warm scheme — cream page, white cards, rust accent — and every
color is a custom property in the `:root` block at the top of
`app/static/css/main.css`. Change a value there and it propagates everywhere; nothing else
in the file hardcodes a color except the two hero gradients.

| Token | Used for |
|---|---|
| `--bg` / `--bg-alt` | Page background, and the alternating band on every other section |
| `--surface` | Cards, show rows, form fields |
| `--text` / `--muted` | Body copy and secondary copy |
| `--accent` / `--accent-hover` | Links, buttons, eyebrows, active nav |
| `--accent-ink` | Text sitting on an accent fill |
| `--accent-soft` | Tinted chips — the date block on a show card |

The site is light-only on purpose: `color-scheme: light` is declared so browsers don't
invert form controls in dark mode. If you swap the accent, check it still clears 4.5:1
both as text on `--bg` and under `--accent-ink` as a button fill.

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
show date logic, the rendered templates, and the asset placeholder/cache-stamping
behaviour. It also validates the YAML content itself — required fields present, dates
parseable, social URLs well-formed — which is the check that catches most real mistakes,
since content edits are the most frequent change.

Coverage must stay at or above 85% or the run fails; it currently sits at 100% on
`app/`.

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

CI runs flake8 and pytest on every PR to `main` or `dev`. `main` is branch-protected: a
pull request is required, and both CI legs (`Python 3.10` and `Python 3.12`) must be green
before `gh pr merge` will go through. `main` is the deploy branch — nothing lands there
unchecked.

## Deployment

Not yet live, but the settings are already committed in `render.yaml`, so it's a short job:

1. Render dashboard → **New → Blueprint**, point it at this repo. It picks up the build
   command (`pip install -r requirements.txt`), start command (`gunicorn wsgi:app`),
   health check path (`/health`), and Python version from `render.yaml`.
2. Fill in the three values marked `sync: false` — `RESEND_API_KEY`, `MAIL_RECIPIENT`,
   `MAIL_FROM`. `SECRET_KEY` is generated by Render; `FLASK_ENV` is already set to
   `production`.
3. Set the `SITE_URL` repository variable (**Settings → Secrets and variables → Actions →
   Variables**) to the live URL. This switches on the keep-alive ping.

Render deploys from `main` only, so a deploy is whatever the last merged PR contained.

### Keep-alive

`.github/workflows/keep_alive.yml` pings `/health` hourly, because Render's free tier
sleeps after 15 minutes idle and takes roughly 50 seconds to wake — long enough that a
prospective client assumes the site is broken. Until `SITE_URL` is set it logs a notice and
exits 0, so it doesn't fail hourly before the deploy exists.
