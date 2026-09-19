"""Tests for the analytics endpoints."""

from datetime import date, timedelta


def _create_entries(client, headers, count: int, sport_mood: int = 4, rest_mood: int = 3):
    """Create `count` entries ending yesterday; every 2nd day is a sport day."""
    today = date.today()
    for offset in range(1, count + 1):
        entry_date = today - timedelta(days=offset)
        did_sport = offset % 2 == 0
        response = client.post(
            "/journal",
            json={
                "entry_date": entry_date.isoformat(),
                "mood_score": sport_mood if did_sport else rest_mood,
                "did_sport": did_sport,
                "emotions": [{"emotion_id": 1, "intensity": 3}],
            },
            headers=headers,
        )
        assert response.status_code in (201, 409)  # 409 = day already seeded


def test_summary_data_levels(client, auth_headers):
    response = client.get("/analytics/summary", headers=auth_headers)
    assert response.json()["data_level"] == "insufficient"

    _create_entries(client, auth_headers, 10)
    body = client.get("/analytics/summary", headers=auth_headers).json()
    assert body["data_level"] == "basic"
    assert body["total_entries"] == 10


def test_mood_trend(client, auth_headers):
    _create_entries(client, auth_headers, 10)
    body = client.get("/analytics/mood?days=30", headers=auth_headers).json()
    assert len(body["points"]) == 10
    assert body["average"] == 3.5  # half 4s, half 3s
    assert body["average_last_7_days"] is not None


def test_weekday_requires_enough_data(client, auth_headers):
    _create_entries(client, auth_headers, 3)
    body = client.get("/analytics/weekday", headers=auth_headers).json()
    assert body["weekdays"] == []

    _create_entries_more = 20  # bring total above threshold
    _create_entries(client, auth_headers, _create_entries_more + 3)  # skips existing days
    body = client.get("/analytics/weekday", headers=auth_headers).json()
    assert len(body["weekdays"]) > 0
    assert all(w["weekday_name"] for w in body["weekdays"])


def test_sport_vs_mood(client, auth_headers):
    _create_entries(client, auth_headers, 12)
    body = client.get("/analytics/sport", headers=auth_headers).json()
    assert body["sport_days"] == 6
    assert body["no_sport_days"] == 6
    assert body["average_mood_sport_days"] == 4.0
    assert body["average_mood_no_sport_days"] == 3.0
    assert body["difference"] == 1.0
    assert "1,0 Punkte höher" in body["statement"]  # deutsches Komma


def test_sport_statement_needs_enough_days(client, auth_headers):
    _create_entries(client, auth_headers, 3)  # only 1 sport day
    body = client.get("/analytics/sport", headers=auth_headers).json()
    assert body["difference"] is None
    assert "genügend Daten" in body["statement"]


def test_habit_completion(client, auth_headers):
    habit = client.post(
        "/habits", json={"name": "Lesen"}, headers=auth_headers
    ).json()
    today = date.today()
    for offset in range(1, 5):
        client.post(
            f"/habits/{habit['id']}/logs",
            json={
                "log_date": (today - timedelta(days=offset)).isoformat(),
                "completed": offset != 2,  # one missed day
            },
            headers=auth_headers,
        )

    body = client.get("/analytics/habits?days=30", headers=auth_headers).json()
    assert len(body) == 1
    assert body[0]["days_tracked"] == 4
    assert body[0]["days_completed"] == 3


def test_emotion_frequencies(client, auth_headers):
    _create_entries(client, auth_headers, 5)
    body = client.get("/analytics/emotions", headers=auth_headers).json()
    assert len(body) == 1
    assert body[0]["emotion_id"] == 1
    assert body[0]["count"] == 5


def test_analytics_are_user_scoped(client, auth_headers):
    _create_entries(client, auth_headers, 10)

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

    body = client.get("/analytics/summary", headers=other_headers).json()
    assert body["total_entries"] == 0
