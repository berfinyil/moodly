"""Tests for habit CRUD, daily check-off and user isolation."""


def _create_habit(client, headers, **overrides) -> dict:
    payload = {"name": "Lesen", "target_value": 20, "unit": "Minuten"}
    payload.update(overrides)
    response = client.post("/habits", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_create_and_list_habits(client, auth_headers):
    _create_habit(client, auth_headers)
    _create_habit(client, auth_headers, name="Meditation", target_value=None, unit=None)

    response = client.get("/habits", headers=auth_headers)
    assert response.status_code == 200
    names = [h["name"] for h in response.json()]
    assert names == ["Lesen", "Meditation"]


def test_log_habit_upsert(client, auth_headers):
    habit = _create_habit(client, auth_headers)

    # First check-off
    response = client.post(
        f"/habits/{habit['id']}/logs",
        json={"log_date": "2026-08-10", "completed": True, "value": 25},
        headers=auth_headers,
    )
    assert response.status_code == 200
    first_id = response.json()["id"]

    # Same day again -> updates instead of creating a duplicate
    response = client.post(
        f"/habits/{habit['id']}/logs",
        json={"log_date": "2026-08-10", "completed": False, "value": None},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == first_id
    assert response.json()["completed"] is False

    logs = client.get(
        f"/habits/{habit['id']}/logs", headers=auth_headers
    ).json()
    assert len(logs) == 1


def test_daily_status(client, auth_headers):
    habit = _create_habit(client, auth_headers)
    _create_habit(client, auth_headers, name="Wasser trinken")

    client.post(
        f"/habits/{habit['id']}/logs",
        json={"log_date": "2026-08-10", "completed": True, "value": 30},
        headers=auth_headers,
    )

    response = client.get(
        "/habits/daily", params={"for_date": "2026-08-10"}, headers=auth_headers
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    by_name = {item["name"]: item for item in items}
    assert by_name["Lesen"]["today_log"]["value"] == 30
    assert by_name["Wasser trinken"]["today_log"] is None


def test_update_and_deactivate_habit(client, auth_headers):
    habit = _create_habit(client, auth_headers)

    response = client.put(
        f"/habits/{habit['id']}",
        json={"name": "Lesen", "is_active": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Inactive habits disappear from the default list and daily view
    assert client.get("/habits", headers=auth_headers).json() == []
    assert (
        client.get("/habits?include_inactive=true", headers=auth_headers).json()
    ) != []


def test_delete_habit(client, auth_headers):
    habit = _create_habit(client, auth_headers)
    assert (
        client.delete(f"/habits/{habit['id']}", headers=auth_headers)
    ).status_code == 204
    assert client.get("/habits", headers=auth_headers).json() == []


def test_other_users_habits_are_not_accessible(client, auth_headers):
    habit = _create_habit(client, auth_headers)

    client.post(
        "/auth/register",
        json={
            "email": "andere@example.com",
            "username": "andere",
            "password": "nochEinPasswort1",
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": "andere@example.com", "password": "nochEinPasswort1"},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/habits", headers=other_headers).json() == []
    assert (
        client.post(
            f"/habits/{habit['id']}/logs",
            json={"log_date": "2026-08-10", "completed": True},
            headers=other_headers,
        )
    ).status_code == 404
    assert (
        client.delete(f"/habits/{habit['id']}", headers=other_headers)
    ).status_code == 404


def test_habits_require_auth(client):
    assert client.get("/habits").status_code == 401
