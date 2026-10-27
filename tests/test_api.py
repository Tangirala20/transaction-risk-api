import os
from pathlib import Path
from fastapi.testclient import TestClient

# Use an isolated test DB before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///./test_risk_api.db"
os.environ["API_KEY"] = "test-key"

from app.main import app  # noqa: E402

client = TestClient(app)
HEADERS = {"X-API-Key": "test-key"}

def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

def test_requires_api_key():
    response = client.get("/v1/transactions")
    assert response.status_code == 401

def test_score_and_fetch_transaction():
    payload = {
        "transaction_id": "test-txn-001",
        "user_id": "user-001",
        "amount": "125000.00",
        "currency": "INR",
        "country": "US",
        "merchant_category": "electronics",
    }
    response = client.post("/v1/transactions/score", json=payload, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "BLOCK"
    assert body["risk_score"] == 1.0

    fetched = client.get("/v1/transactions/test-txn-001", headers=HEADERS)
    assert fetched.status_code == 200
    assert fetched.json()["transaction_id"] == "test-txn-001"

def test_idempotency_replay():
    payload = {
        "transaction_id": "test-txn-idempotent",
        "user_id": "user-002",
        "amount": "100.00",
        "currency": "INR",
        "country": "IN",
        "merchant_category": "groceries",
    }
    headers = {**HEADERS, "Idempotency-Key": "idem-test-001"}
    first = client.post("/v1/transactions/score", json=payload, headers=headers)
    second = client.post("/v1/transactions/score", json=payload, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.headers.get("idempotency-replayed") == "true"

def test_invalid_amount_rejected():
    payload = {
        "transaction_id": "test-bad",
        "user_id": "user-003",
        "amount": "-1",
        "currency": "INR",
        "country": "IN",
        "merchant_category": "groceries",
    }
    response = client.post("/v1/transactions/score", json=payload, headers=HEADERS)
    assert response.status_code == 422
