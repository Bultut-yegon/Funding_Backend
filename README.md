# FundingHub

FundingHub is a funding-opportunity discovery platform. It combines a FastAPI
backend, PostgreSQL, a React frontend, opportunity scrapers, profile-aware
recommendations, bookmarks, notifications, and proposal tools.

This README is intentionally **terminal-first**. Follow the commands in order,
or copy the workflow that matches what you are trying to do. Commands assume
you are standing at the repository root.

## 0. Ask the terminal what is available

Before changing anything, run:

```bash
pwd
git status --short
find . -maxdepth 2 -type f | sort | sed -n '1,160p'
```

Expected top-level areas:

```text
backend/      FastAPI application, migrations, recommendation engine
frontend/     React application
docker-compose.yml
```

## 1. Choose a workflow

### I want the complete stack with Docker

```bash
docker compose up --build
```

Open:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
```

Stop the stack without deleting the database volume:

```bash
docker compose down
```

Stop it and delete local PostgreSQL data:

```bash
docker compose down -v
```

### I want backend hot reload

Start PostgreSQL first:

```bash
docker compose up -d db
```

Create a backend environment file:

```bash
cd backend
cp .env.example .env 2>/dev/null || touch .env
```

If `.env.example` is not present, create the minimum local configuration:

```bash
cat > .env <<'EOF'
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/funding_db
SECRET_KEY=replace-this-with-a-long-local-secret
ALGORITHM=HS256
ENVIRONMENT=development
EOF
```

Create or reuse a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Apply migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:8000/ && printf '\n'
curl -fsS http://127.0.0.1:8000/docs >/dev/null && echo "API docs are available"
```

### I want frontend hot reload

```bash
cd frontend
npm ci
npm start
```

Open `http://localhost:3000`.

The frontend uses the API URL configured in its environment/service settings.
If requests go to the wrong server, inspect:

```bash
grep -R "baseURL\|REACT_APP\|localhost:8000" src .env* 2>/dev/null
```

## 2. Configure secrets safely

Never commit `.env` files, API keys, mail passwords, or database passwords.
The backend reads settings from `backend/.env`.

Useful settings:

```dotenv
DATABASE_URL=postgresql://user:password@host:5432/database
SECRET_KEY=long-random-signing-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=http://localhost:3000

# Optional email delivery
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Optional AI and monitoring integrations
GROQ_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
SENTRY_DSN=
```

Generate a local secret without putting it in shell history:

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

## 3. Database workflow

Run all migration commands from `backend/`:

```bash
cd backend
. .venv/bin/activate
alembic current
alembic upgrade head
```

Create a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe the schema change"
alembic upgrade head
```

Inspect migration history:

```bash
alembic history --verbose
```

Do not use `Base.metadata.create_all()` as a replacement for migrations in a
shared or deployed database.

## 4. API smoke test from the command line

Set the API address:

```bash
export API="http://127.0.0.1:8000/api"
```

Register a local test user:

```bash
curl -i -X POST "$API/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "CLI Tester",
    "email": "cli-tester@example.com",
    "password": "change-me-now"
  }'
```

Log in and store the access token:

```bash
TOKEN="$(
  curl -fsS -X POST "$API/auth/login" \
    -H 'Content-Type: application/json' \
    -d '{"email":"cli-tester@example.com","password":"change-me-now"}' |
  python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)"
export TOKEN
```

Read and update the profile:

```bash
curl -fsS "$API/profile/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

curl -fsS -X PUT "$API/profile/" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "education_level": "Bachelor'\''s",
    "interests": "agriculture, climate",
    "industry": "Agriculture",
    "country": "Kenya",
    "skills": "soil science, data analysis"
  }' | python -m json.tool
```

Fetch opportunities and recommendations:

```bash
curl -fsS "$API/opportunities/?limit=5" | python -m json.tool

curl -fsS "$API/recommendations/?top_k=10" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

The recommendation flow normalizes profile values, ignores literal null
strings, favors skills/interests/industry, respects opportunity country
eligibility, allows global opportunities, and removes low-relevance matches.

## 5. Populate and refresh opportunities

Trigger the scraper through the API:

```bash
curl -fsS -X POST "$API/opportunities/scrape" | python -m json.tool
```

The scraper collects opportunities from configured feeds and enriches them
with category, deadline, eligibility, and country metadata. Review scraped
records before relying on them in production:

```bash
curl -fsS "$API/opportunities/?limit=20" |
  python -c 'import json,sys; [print(x["id"], x["country"], x["title"]) for x in json.load(sys.stdin)]'
```

## 6. Notifications

The API starts the scheduler during application startup. Email delivery is
skipped when `MAIL_USERNAME` is empty.

To inspect notification records:

```bash
curl -fsS "$API/notifications/" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

For local development, leave mail credentials empty unless you explicitly
want to test delivery. Do not use a personal account password; use a provider
app password or a development mail sandbox.

## 7. Validate before opening a pull request

Run the smallest relevant checks first:

```bash
git diff --check
```

Backend syntax/import check:

```bash
cd backend
. .venv/bin/activate
python -m compileall -q app
python -c 'from app.main import app; print(app.title)'
```

Frontend production build:

```bash
cd frontend
npm ci
npm run build
```

Frontend tests:

```bash
npm test -- --watchAll=false
```

Review the final change:

```bash
git status --short
git diff --stat
git diff -- backend frontend
```

## 8. Pull request workflow

Start from an up-to-date branch:

```bash
git fetch origin
git switch main
git pull --ff-only
git switch -c feat/short-description
```

Work in small, reviewable commits:

```bash
git add backend frontend
git diff --cached --check
git commit -m "feat: describe the change"
```

Push and open the pull request:

```bash
git push -u origin HEAD
```

Before requesting review, paste the exact commands you ran and their results
into the pull request description.

## 9. Troubleshooting by command

```bash
# Is PostgreSQL listening?
docker compose ps
docker compose logs db --tail=100

# Is the API listening?
curl -i http://127.0.0.1:8000/

# Why did the API fail to start?
docker compose logs backend --tail=200

# Which migration is active?
cd backend && alembic current

# Which process owns a development port?
lsof -i :8000
lsof -i :3000

# What changed locally?
git status --short
git diff --check
```

If a command fails, keep the full command and error output. That output is
usually more useful than a screenshot when diagnosing the issue.

## Project map

```text
backend/app/api/                 HTTP routes
backend/app/models/              SQLAlchemy models
backend/app/schemas/             Pydantic request/response models
backend/app/services/            Application services and scheduled work
backend/app/ml/                  Enrichment and recommendation logic
backend/alembic/                 Database migrations
frontend/src/pages/              React pages
frontend/src/services/           Frontend API client
docker-compose.yml               Local multi-container stack
```

## License and security

Treat scraped opportunity text and user profile data as untrusted input.
Report security issues privately to the project maintainers. Do not include
credentials, access tokens, or production data in issues, logs, commits, or
pull requests.
