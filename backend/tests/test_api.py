import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.schemas import RegisterRequest, ScanRequest

client = TestClient(app)


def test_health_returns_status():
    response = client.get("/health")
    assert response.status_code in (200, 503)
    body = response.json()
    assert body["api"] == "ok"
    assert "postgres" in body
    assert "redis" in body


def test_scan_requires_authentication():
    response = client.post("/v1/scan", json={"ingredient_text": "water, salt"})
    assert response.status_code == 401


def test_register_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RegisterRequest.model_validate(
            {
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test",
                "is_admin": True,
            }
        )


def test_scan_request_requires_at_least_one_input():
    with pytest.raises(ValidationError):
        ScanRequest.model_validate({"product_hint": "Juice"})
