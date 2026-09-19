"""Shared test fixtures: in-memory database and API test client."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register models on Base.metadata)
from app.database.base import Base
from app.database.database import get_db
from app.database.seed import seed_emotions
from app.services.achievement_service import seed_achievements
from app.main import app


@pytest.fixture
def client():
    """TestClient backed by a fresh in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)

    with TestingSessionLocal() as seed_db:
        seed_emotions(seed_db)
        seed_achievements(seed_db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client) -> dict:
    """Register a default user and return their credentials."""
    credentials = {
        "email": "berfin@example.com",
        "username": "berfin",
        "password": "supersecret123",
    }
    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 201
    return credentials


@pytest.fixture
def auth_headers(client, registered_user) -> dict:
    """Log the default user in and return Authorization headers."""
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
