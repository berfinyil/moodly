"""Tests for journal entry CRUD, validation and user isolation."""


def _entry_payload(**overrides) -> dict:
    payload = {
        "entry_date": "2026-08-10",
        "mood_score": 4,
        "energy_level": 3,
        "stress_level": 2,
        "sleep_quality": 4,
        "did_sport": True,
        "sport_type": "Fitness",
        "sport_duration_minutes": 60,
        "cried": False,
        "had_headache": False,
        "notes": "Guter Tag heute.",
        "gratitude": "Sonne und Kaffee.",
        "emotions": [
            {"emotion_id": 1, "intensity": 4},
            {"emotion_id": 5, "intensity": 3},
        ],
    }
    payload.update(overrides)
    return payload


def test_create_and_read_entry(client, auth_headers):
    response = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["mood_score"] == 4
    assert len(body["emotions"]) == 2
    assert body["emotions"][0]["emotion"]["name"]  # joined catalog data

    response = client.get("/journal/date/2026-08-10", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == body["id"]


def test_duplicate_date_fails(client, auth_headers):
    assert (
        client.post("/journal", json=_entry_payload(), headers=auth_headers)
    ).status_code == 201
    response = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    )
    assert response.status_code == 409


def test_invalid_mood_score_fails(client, auth_headers):
    response = client.post(
        "/journal", json=_entry_payload(mood_score=6), headers=auth_headers
    )
    assert response.status_code == 422


def test_invalid_pain_level_fails(client, auth_headers):
    response = client.post(
        "/journal",
        json=_entry_payload(had_pain=True, pain_level=11),
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_unknown_emotion_fails(client, auth_headers):
    response = client.post(
        "/journal",
        json=_entry_payload(emotions=[{"emotion_id": 999, "intensity": 3}]),
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_update_entry_replaces_emotions(client, auth_headers):
    entry_id = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    ).json()["id"]

    response = client.put(
        f"/journal/{entry_id}",
        json=_entry_payload(
            mood_score=2, emotions=[{"emotion_id": 2, "intensity": 5}]
        ),
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mood_score"] == 2
    assert len(body["emotions"]) == 1
    assert body["emotions"][0]["emotion_id"] == 2


def test_update_keeps_overlapping_emotion(client, auth_headers):
    """Regression: updating while keeping the same emotion must not crash."""
    entry_id = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    ).json()["id"]

    response = client.put(
        f"/journal/{entry_id}",
        json=_entry_payload(
            emotions=[
                {"emotion_id": 1, "intensity": 5},  # kept from creation
                {"emotion_id": 3, "intensity": 2},  # new
            ]
        ),
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()["emotions"]) == 2


def test_delete_entry(client, auth_headers):
    entry_id = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    ).json()["id"]

    assert (
        client.delete(f"/journal/{entry_id}", headers=auth_headers)
    ).status_code == 204
    assert (
        client.get(f"/journal/{entry_id}", headers=auth_headers)
    ).status_code == 404


def test_list_and_calendar(client, auth_headers):
    client.post("/journal", json=_entry_payload(), headers=auth_headers)
    client.post(
        "/journal",
        json=_entry_payload(entry_date="2026-08-09", mood_score=3),
        headers=auth_headers,
    )

    response = client.get("/journal", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get(
        "/journal/calendar",
        params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    days = response.json()
    assert len(days) == 2
    assert {"entry_date", "mood_score"} == set(days[0].keys())


def test_other_users_entries_are_not_accessible(client, auth_headers):
    """A user must never be able to read someone else's journal."""
    entry_id = client.post(
        "/journal", json=_entry_payload(), headers=auth_headers
    ).json()["id"]

    # Second user
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

    assert (
        client.get(f"/journal/{entry_id}", headers=other_headers)
    ).status_code == 404
    assert (client.get("/journal", headers=other_headers)).json() == []
    assert (
        client.delete(f"/journal/{entry_id}", headers=other_headers)
    ).status_code == 404
    # Original owner still has their entry
    assert (
        client.get(f"/journal/{entry_id}", headers=auth_headers)
    ).status_code == 200


def test_journal_requires_auth(client):
    assert client.get("/journal").status_code == 401
    assert client.post("/journal", json=_entry_payload()).status_code == 401


def test_emotion_catalog(client, auth_headers):
    response = client.get("/emotions", headers=auth_headers)
    assert response.status_code == 200
    emotions = response.json()
    assert len(emotions) == 14
    assert {"id", "name", "emoji"} == set(emotions[0].keys())
