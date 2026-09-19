"""Tests for registration, login and protected routes."""


def test_register_returns_user_without_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "neu@example.com",
            "username": "neuernutzer",
            "password": "supersecret123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "neu@example.com"
    assert body["username"] == "neuernutzer"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_fails(client, registered_user):
    response = client.post(
        "/auth/register",
        json={
            "email": registered_user["email"],
            "username": "andererName",
            "password": "supersecret123",
        },
    )
    assert response.status_code == 409


def test_register_short_password_fails(client):
    response = client.post(
        "/auth/register",
        json={"email": "a@b.de", "username": "kurz", "password": "123"},
    )
    assert response.status_code == 422


def test_login_returns_token(client, registered_user):
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password_fails(client, registered_user):
    response = client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": "falschesPasswort"},
    )
    assert response.status_code == 401


def test_users_me_returns_profile(client, registered_user, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]


def test_users_me_without_token_fails(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_users_me_with_invalid_token_fails(client):
    response = client.get(
        "/users/me", headers={"Authorization": "Bearer kein.echter.token"}
    )
    assert response.status_code == 401
