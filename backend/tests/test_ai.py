"""Tests for the AI endpoints (template provider, no external API)."""

from datetime import date, timedelta

from app.services.ai_service import DAILY_QUESTIONS


def test_daily_question(client, auth_headers):
    response = client.get("/ai/daily-question", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["question"] in DAILY_QUESTIONS


def test_weekly_summary_empty_week(client, auth_headers):
    response = client.post("/ai/weekly-summary", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "noch keinen Eintrag" in body["summary"]
    assert body["facts"]["days_written"] == 0


def test_weekly_summary_with_entries(client, auth_headers):
    # Write entries for this week (today and up to 2 days back, within the week)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    days = [d for d in (today - timedelta(days=i) for i in range(3)) if d >= week_start]
    for day in days:
        response = client.post(
            "/journal",
            json={
                "entry_date": day.isoformat(),
                "mood_score": 4,
                "stress_level": 2,
                "did_sport": True,
                "emotions": [{"emotion_id": 5, "intensity": 4}],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    body = client.post("/ai/weekly-summary", headers=auth_headers).json()
    facts = body["facts"]
    assert facts["days_written"] == len(days)
    assert facts["average_mood"] == 4.0
    assert facts["sport_days"] == len(days)
    assert facts["top_emotions"] == ["motiviert"]

    # Template text contains the backend-computed numbers (German comma)
    assert f"an {len(days)} von 7 Tagen" in body["summary"]
    assert "4,0 von 5" in body["summary"]
    assert "motiviert" in body["summary"]


def test_weekly_summary_excludes_sensitive_fields(client, auth_headers):
    """The facts payload (= what an external provider would see) must not
    contain sensitive fields or free-text content."""
    client.post(
        "/journal",
        json={
            "entry_date": date.today().isoformat(),
            "mood_score": 3,
            "had_sex": True,
            "cried": True,
            "had_pain": True,
            "pain_level": 7,
            "pain_location": "Nacken",
            "notes": "Sehr privater Text",
            "emotions": [],
        },
        headers=auth_headers,
    )
    body = client.post("/ai/weekly-summary", headers=auth_headers).json()
    serialized = str(body)
    assert "had_sex" not in serialized
    assert "cried" not in serialized
    assert "pain" not in serialized
    assert "Sehr privater Text" not in serialized
    assert "Nacken" not in serialized


def test_ai_requires_auth(client):
    assert client.get("/ai/daily-question").status_code == 401
    assert client.post("/ai/weekly-summary").status_code == 401
