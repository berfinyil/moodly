"""Tests for streak calculation and achievement unlocking."""

from datetime import date, timedelta


def _write_day(client, headers, days_ago: int, **overrides):
    payload = {
        "entry_date": (date.today() - timedelta(days=days_ago)).isoformat(),
        "mood_score": 3,
        "emotions": [],
    }
    payload.update(overrides)
    response = client.post("/journal", json=payload, headers=headers)
    assert response.status_code == 201


def test_streak_empty(client, auth_headers):
    body = client.get("/streak", headers=auth_headers).json()
    assert body == {"current_streak": 0, "longest_streak": 0}


def test_streak_counts_consecutive_days(client, auth_headers):
    # Today + the 2 previous days, then a gap, then 5 older days
    for days_ago in [0, 1, 2, 5, 6, 7, 8, 9]:
        _write_day(client, auth_headers, days_ago)

    body = client.get("/streak", headers=auth_headers).json()
    assert body["current_streak"] == 3
    assert body["longest_streak"] == 5


def test_streak_allows_missing_today(client, auth_headers):
    """If today isn't written yet, the streak counts from yesterday."""
    for days_ago in [1, 2, 3]:
        _write_day(client, auth_headers, days_ago)
    body = client.get("/streak", headers=auth_headers).json()
    assert body["current_streak"] == 3


def test_first_entry_achievement(client, auth_headers):
    _write_day(client, auth_headers, 0)
    achievements = client.get("/achievements", headers=auth_headers).json()
    by_code = {a["achievement"]["code"]: a for a in achievements}
    assert by_code["first_entry"]["unlocked_at"] is not None
    assert by_code["entries_30"]["unlocked_at"] is None


def test_week_streak_achievement(client, auth_headers):
    for days_ago in range(7):
        _write_day(client, auth_headers, days_ago)
    achievements = client.get("/achievements", headers=auth_headers).json()
    by_code = {a["achievement"]["code"]: a for a in achievements}
    assert by_code["week_streak"]["unlocked_at"] is not None


def test_sport_achievement(client, auth_headers):
    for days_ago in range(10):
        _write_day(client, auth_headers, days_ago, did_sport=True)
    achievements = client.get("/achievements", headers=auth_headers).json()
    by_code = {a["achievement"]["code"]: a for a in achievements}
    assert by_code["sport_10"]["unlocked_at"] is not None


def test_achievement_not_unlocked_twice(client, auth_headers):
    _write_day(client, auth_headers, 0)
    first = {
        a["achievement"]["code"]: a["unlocked_at"]
        for a in client.get("/achievements", headers=auth_headers).json()
    }
    # Trigger another check via an update-like action (new entry yesterday)
    _write_day(client, auth_headers, 1)
    second = {
        a["achievement"]["code"]: a["unlocked_at"]
        for a in client.get("/achievements", headers=auth_headers).json()
    }
    assert first["first_entry"] == second["first_entry"]  # timestamp unchanged


def test_achievements_are_user_scoped(client, auth_headers):
    _write_day(client, auth_headers, 0)

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

    achievements = client.get("/achievements", headers=other_headers).json()
    assert all(a["unlocked_at"] is None for a in achievements)
    assert client.get("/streak", headers=other_headers).json()["current_streak"] == 0
