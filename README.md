# Eldorado Automated Repricing System

Automated price management system for Eldorado.gg listings — monitors competitor
prices and repositions the client's price one cent below the lowest active
seller, within min/max limits set by the client, through Eldorado's official
Seller API.

## Architecture

```
User dashboard (Next.js)  <-- WebSocket -->  Backend API (FastAPI)  --->  Eldorado Seller API
        |                                          |
        | REST (listings, rules, history,          |
        |  notifications)                          v
        |                                   PostgreSQL database
        v                                          ^
  Live price updates +                             |
  follow-up notifications                    Scheduler (runs every minute,
  pushed instantly, no polling                processes each listing on its
                                               own configured interval, and
                                               pushes a WebSocket event +
                                               a saved Notification for
                                               every price change or error)
```

### Real-time updates & follow-up messages

- The dashboard opens one WebSocket connection (`/ws?token=<jwt>`) per session.
- Every time the scheduler reprices a listing (or fails to), it:
  1. saves a `price_history` row (always, for the audit trail),
  2. saves a `Notification` row when something the user should know about happened (a real price change, held-at-limit, or an error — not for silent "no change" cycles),
  3. pushes both events live over WebSocket to any open tab for that user.
- If the user isn't online when it happens, nothing is lost — the notification and history row are still in the database and appear next time they open the dashboard (bell icon shows the unread count).
- The frontend auto-reconnects with backoff if the WebSocket drops (network blip, backend restart), and shows a small "Live" / "Reconnecting…" indicator in the header so the user always knows whether they're seeing live data.

## Before you start — the one thing that isn't done yet

**`backend/app/market_client.py` talks to a placeholder marketplace API.**
Eldorado.gg does not publish public developer docs for its Seller API,
so this file was written against the *general shape* every seller repricing
API has (fetch offers, push a price) rather than Eldorado's exact contract.

Once the client shares their official Seller API documentation:
1. Update `marketplace_base_url` in `backend/app/config.py`.
2. Fix the three `TODO` comments in `market_client.py` — the real endpoint
   paths, the auth header name, and the response field names.
3. Re-run the tests in `backend/tests/` to confirm nothing broke.

Nothing else in the codebase needs to change — every other module talks to
`EldoradoClient`, never to the marketplace directly.

## Project layout

```
backend/
  app/
    main.py            FastAPI app, startup/shutdown, router registration
    config.py           All settings, loaded from .env
    database.py         Async SQLAlchemy engine/session
    models.py            users, listings, automation_rules, price_history, notifications
    schemas.py           Pydantic request/response models
    security.py          Password hashing, JWT, API-key encryption
    market_client.py     Eldorado API wrapper (see note above)
    pricing_engine.py    Pure pricing logic — no I/O, fully unit tested
    scheduler.py          Background job: reprices due listings, saves notifications, pushes WebSocket events
    realtime.py            WebSocket connection manager (per-user push)
    logging_config.py      Structured logging setup
    routers/
      auth.py            Signup, login, submit marketplace API key
      listings.py        CRUD for tracked listings
      rules.py            Get/update per-listing pricing rules
      history.py          Price change audit log
      notifications.py    Follow-up messages: list, unread count, mark read
      ws.py                 WebSocket endpoint for live updates
  migrations/             Alembic migrations (initial schema included)
  tests/
    test_pricing_engine.py   6 unit tests — undercut/clamp/no-change logic
    test_auth.py              Signup/login/token flow, credential secrecy
    test_listings.py          CRUD + per-user data isolation
    test_notifications.py     Unread count / mark-read
    conftest.py                In-memory SQLite test database + fixtures
  requirements.txt / requirements-dev.txt
  entrypoint.sh            Runs `alembic upgrade head` in production, then starts uvicorn
  Dockerfile
  .env.example

frontend/
  pages/
    login.js            Sign in
    listings.js          Main dashboard — set min/max, undercut step, on/off, live price updates
    history.js            Price change log per listing, live-updating
    connect.js             Paste your Eldorado Seller API key here (encrypted on save)
  components/
    Layout.js             Sidebar nav + top bar with live connection status
    NotificationBell.js   Bell icon, unread badge, live-updating dropdown
  lib/
    api.js                 Axios client with JWT attached automatically
    useRealtime.js          WebSocket hook with auto-reconnect
  Dockerfile

docker-compose.yml       Runs db + backend + frontend together
```

## Running locally

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt   # includes requirements.txt + test tools
cp .env.example .env
# generate a real encryption key and paste it into .env:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Development: tables auto-create on startup (ENVIRONMENT=development in .env, the default).
uvicorn app.main:app --reload

# Production: run migrations yourself first, then set ENVIRONMENT=production in .env
alembic upgrade head
```

Run the full test suite any time you touch the backend:
```bash
pytest tests/ -v
```
19 tests total: 6 on the pricing engine logic, the rest end-to-end against a real (in-memory) database — signup/login, listing CRUD with per-user data isolation, rule validation, and notifications.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`.

### 3. Or run everything with Docker Compose

```bash
docker compose up --build
```

- Backend: `http://localhost:8000` (docs at `/docs`)
- Frontend: `http://localhost:3000`
- Database: `localhost:5432`

## API endpoints (auto-documented at `/docs` once running)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create a client account |
| POST | `/auth/login` | Get a JWT |
| POST | `/auth/marketplace-credentials` | Submit the Eldorado Seller API key (encrypted at rest) |
| GET/POST | `/listings` | List / add tracked listings |
| DELETE | `/listings/{id}` | Stop tracking a listing |
| GET/PUT | `/listings/{id}/rule` | View / update pricing rule (min, max, step, interval, on/off) |
| GET | `/listings/{id}/history` | Price change audit log |
| GET | `/notifications` | Follow-up messages (price changes, held-at-limit, errors) |
| GET | `/notifications/unread-count` | Badge count for the bell icon |
| PATCH | `/notifications/{id}/read` / `POST /notifications/mark-all-read` | Mark read |
| WS | `/ws?token=<jwt>` | Live push — price updates + new notifications |

## Known issues / things to double-check before going live

- **Next.js dependency:** the frontend runs on Next.js 14.2.35, the final patched release of the 14.x line (14.x reached end-of-life in Oct 2025). All *critical* CVEs are patched. `npm audit` will still show a couple of moderate/high advisories that only get fully resolved by upgrading to Next 15/16, which is a bigger breaking change (different build output, some API changes). Recommend planning that upgrade separately once the client's core repricing flow is live and stable — not worth doing in the same pass as the first real API integration.
- **`market_client.py` is still built against a placeholder API contract** — see the note near the top of this README. This is the one piece that needs the client's real Eldorado Seller API documentation before it can go live.

## Deployment (matches the budget document)

- **Server:** DigitalOcean Droplet, 2 GiB / 1 vCPU, $12/month
- **Database:** self-hosted PostgreSQL on the same Droplet (Docker Compose handles this)
- **Domain + SSL:** point a `.com` domain at the Droplet, add Nginx + Let's Encrypt in front of the frontend/backend containers
- **CI/CD:** push to `main` → GitHub Actions → SSH deploy → `docker compose up --build -d`

## Security notes

- The client's Eldorado API key is encrypted with Fernet before it touches the database — never logged, never returned in any API response.
- All dashboard endpoints require a JWT; a user can only ever see their own listings (enforced at the query level, not just the UI).
- The bot only prices through the official API and only within the min/max limits the client sets — it does not attempt to exceed Eldorado's own update-frequency rules.
