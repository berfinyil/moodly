"""Tests for the unified error format and deployment-related config."""

import pytest
from fastapi.testclient import TestClient

import app.main
from app.core.config import INSECURE_SECRET_KEY, Settings


def test_error_format_is_consistent(client, auth_headers):
    response = client.get("/journal/999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {
        "error": True,
        "message": "Journaleintrag nicht gefunden.",
    }


def test_validation_error_names_field_without_echoing_value(client, auth_headers):
    response = client.post(
        "/journal",
        json={
            "entry_date": "2026-08-10",
            "mood_score": 99,
            "notes": "Sehr privater Text",
            "emotions": [],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"] is True
    assert "mood_score" in body["message"]
    # The submitted (possibly private) content must not be echoed back
    assert "Sehr privater Text" not in str(body)


def test_unauthenticated_error_uses_same_format(client):
    response = client.get("/journal")
    assert response.status_code == 401
    assert response.json()["error"] is True


def test_production_refuses_to_start_with_default_secret_key(monkeypatch):
    """Never sign tokens with a key that is public in the repository."""
    unsafe = Settings(
        _env_file=None,
        environment="production",
        secret_key=INSECURE_SECRET_KEY,
    )
    monkeypatch.setattr(app.main, "settings", unsafe)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        with TestClient(app.main.app):
            pass


def test_postgres_url_is_normalized_for_sqlalchemy():
    """Hosting providers hand out postgres://, SQLAlchemy 2.x needs postgresql://."""
    settings = Settings(database_url="postgres://user:pw@host:5432/db")
    assert settings.resolved_database_url == "postgresql://user:pw@host:5432/db"


def test_cors_origins_accept_comma_separated_env_var(monkeypatch):
    """Must go through the *environment* path, like a real deployment does.

    Constructing Settings(cors_origins=...) directly bypasses pydantic's
    env parsing and would pass even if the env path were broken.
    """
    monkeypatch.setenv(
        "CORS_ORIGINS", "https://a.example.com, https://b.example.com"
    )
    settings = Settings(_env_file=None)
    assert settings.cors_origins == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_settings_work_without_env_file(monkeypatch):
    """In Docker there is no .env file — everything comes from the environment."""
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    monkeypatch.setenv("SECRET_KEY", "x" * 64)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

    settings = Settings(_env_file=None)
    assert settings.is_production is True
    assert settings.resolved_database_url == "postgresql://u:p@host:5432/db"
    assert settings.cors_origins == ["https://app.example.com"]
