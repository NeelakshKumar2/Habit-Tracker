# Habit Tracker

A habit tracker for people who finish: streaks, 21 to 365 day challenges, a grit score, daily notes and a weekly review.
Every person has their own private account.

**Accounts:** register, sign in, sign out (this device or all devices), forgot password by email, change password,
profile picture on the dashboard, export your data, and permanently delete your account.

## Run it on your computer

```bash
./start-grit.sh        # or:  pip install -r requirements.txt && python run.py
```
Open http://localhost:8765, choose **Create account**. (Dev mode uses plain-HTTP cookies and prints reset emails to the log.)

## Deploy for real users (HTTPS in one command)

You need a server with Docker and a domain name pointing at it.

```bash
cp .env.example .env     # set GRIT_DOMAIN and GRIT_PUBLIC_URL (and SMTP for reset emails)
docker compose up -d
```
Caddy fetches and renews the HTTPS certificate. The app runs under gunicorn as a non-root user, data lives in the
`grit-data` volume, and the app container is not exposed to the internet directly.

Without Docker: `pip install -r requirements.txt` then
`GRIT_ENV=production GRIT_DB=/var/lib/grit/grit.db GRIT_PUBLIC_URL=https://your.domain GRIT_TRUST_PROXY=1 gunicorn -c deploy/gunicorn.conf.py wsgi:app`
behind any HTTPS reverse proxy.

| Variable | Meaning |
|---|---|
| `GRIT_ENV` | `production` (default: secure cookies, HSTS) or `development` |
| `GRIT_DB` | Path of the SQLite file |
| `GRIT_PUBLIC_URL` | Your public address. Reset-email links are built from this, never from the request's Host header |
| `GRIT_TRUST_PROXY` | Number of reverse proxies in front (1 for the bundled Caddy). Needed so rate limits see real client addresses |
| `GRIT_SMTP_HOST/PORT/USER/PASSWORD/FROM` | Mail server for password reset links. Empty means no reset emails are sent |
| `GRIT_SESSION_DAYS` | How long a sign-in lasts (default 30, sliding) |
| `WEB_CONCURRENCY`, `PORT` | gunicorn workers and port |

**Backups:** `python -m tools.backup /backups --keep 14` makes a consistent copy while the app runs. Schedule it with cron
and copy the files off the machine.

**Health:** `GET /api/health` (alive) and `GET /api/ready` (database reachable).

## How it is protected

- Passwords: scrypt (N=2^15, r=8, p=3, OWASP-listed), per-password salt, parameters stored with the hash and upgraded on login.
- Sessions: random 256-bit token in an `HttpOnly`, `SameSite=Lax`, `Secure` (`__Host-` prefixed) cookie. Only the SHA-256 of the token is stored.
- CSRF: every state-changing request needs a custom header and a same-site `Origin`.
- Brute force: sign-in failures are throttled per (address, email), per email and per address; sign-ups and reset requests are limited too. Counters live in the database so they hold across workers.
- Data isolation: every query is scoped by the signed-in user id; a primary key of (user, id) means two people can use the same challenge id.
- Profile pictures: decoded and re-encoded to a 256 px WebP (drops EXIF/GPS and any hidden payload), size and pixel limits, served with a sandboxing CSP.
- Browser: strict CSP (`script-src 'self'`), no inline scripts, all user text escaped before display.
- Delete account: needs the password, removes every row in one transaction, zeroes freed pages (`secure_delete`) and checkpoints the log.
- Limits per account: 100 challenges, 5 MB of stored data.

## API

All JSON, all under `/api`. Unsafe methods need the header `X-Requested-With: grit`.

| Method and path | Purpose |
|---|---|
| `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/logout-all` | Account session |
| `POST /auth/forgot`, `/auth/reset` | Forgotten password |
| `POST /auth/change-password` | Needs the current password; ends other sessions |
| `GET /auth/me` | Who am I |
| `DELETE /account` | Permanent delete (password required) |
| `GET /account/export` | Download all your data |
| `GET /state`, `PUT /profile` | Load everything, save name and intent |
| `PUT/DELETE /challenges/<id>` | Save or remove a challenge |
| `PUT/GET/DELETE /me/avatar` | Profile picture |
| `GET /score`, `GET /review` | Grit score and weekly review |

## Tests and quality gates

```bash
python -m unittest discover -s tests -t . -v     # 80+ tests, including the browser code run in Node
python tools/coverage_report.py --min 90          # line coverage of server/
python tools/mutation_check.py                    # break the code on purpose; the tests must notice
python tools/loadtest.py --users 120 --workers 4  # multi-process load test on one shared database
```
The score is computed in the browser (`web/js/core/domain.js`) and on the server (`server/scoring.py`); a test runs both on
400 random data sets and requires identical results.

## Honest limits

- SQLite with WAL on one machine suits thousands of active users. For multiple servers move to PostgreSQL (the SQL is plain, but that port is not done or tested).
- Passwords are the only sign-in method. There is no email verification at sign-up and no two-factor sign-in yet.
- Registration reveals whether an email is already registered (it is rate-limited). Sign-in and password reset do not.
- Password hashing costs about a quarter of a CPU-second per sign-in by design. Plan CPU cores for sign-up bursts.
- The Docker and compose files were not built in the environment this was written in; the app, gunicorn config and wsgi entry were run and tested.
- The screenshots in `docs/` show the previous single-user version.

## Layout

`server/` Flask app (config, db, security, auth, api, avatar, mail, validators, scoring, review) ·
`web/` static front end (landing, auth page, app, modules) · `tests/` · `tools/` · `deploy/` · `Dockerfile` · `docker-compose.yml`
