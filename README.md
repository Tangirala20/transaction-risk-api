# Transaction Risk Scoring API

A corporate-style FastAPI portfolio project demonstrating typed API contracts, request validation, API-key authentication, a transparent risk engine, SQLAlchemy persistence, idempotency keys, request correlation IDs, health checks, metrics, and automated tests.

> **Important:** The risk engine uses illustrative rules and is not a validated fraud model. Do not use it for real financial decisions.

## Architecture

Client → FastAPI/Pydantic → Risk Engine → SQLAlchemy/SQLite → Response

Operational features include API-key protection, `X-Request-ID`, liveness/readiness endpoints, metrics, and idempotency replay.

## Run locally (Windows CMD)

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
set API_KEY=local-dev-key-change-me
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive Swagger docs.

## Score a transaction

```cmd
curl -X POST "http://127.0.0.1:8000/v1/transactions/score" -H "Content-Type: application/json" -H "X-API-Key: local-dev-key-change-me" -H "Idempotency-Key: payment-123" -d "{\"transaction_id\":\"txn-001\",\"user_id\":\"user-001\",\"amount\":\"125000.00\",\"currency\":\"INR\",\"country\":\"US\",\"merchant_category\":\"electronics\"}"
```

## Endpoints

- `GET /health/live` — process liveness.
- `GET /health/ready` — checks database access.
- `POST /v1/transactions/score` — validate, score and persist transaction.
- `GET /v1/transactions/{transaction_id}` — retrieve a scored transaction.
- `GET /v1/transactions?limit=50&offset=0` — list recent transactions.
- `GET /metrics` — basic transaction decision counts.

Protected endpoints require `X-API-Key`. Set `API_KEY` in the environment. This demo uses a static API key; production systems should use an identity provider or a robust OAuth2/JWT design, secret management, TLS, rate limiting, and key rotation.

## Run tests

```cmd
python -m pytest -v
```

## Production hardening checklist

- Replace `create_all` with Alembic migrations.
- Use PostgreSQL and managed secrets.
- Add OAuth2/JWT or service-to-service identity.
- Add structured logging and distributed tracing.
- Add rate limiting, timeouts and request-size limits.
- Define retention, privacy, audit and access-control policies.
- Add CI, coverage, dependency scanning, and container vulnerability scanning.
- Replace the demo rules with a validated model and monitored decision thresholds.
