"""AI features: daily reflection questions and weekly summaries.

Privacy rules implemented here:
- All numbers come from analytics_service / streak_service (backend-computed).
  The language model may rephrase them but never invents statistics.
- Sensitive fields (had_sex, cried, pain details) and free-text journal
  content are NEVER included in prompts sent to an external provider.
- Statements stay descriptive ("in deinen dokumentierten Daten") — no
  diagnoses, no causal claims.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.services import analytics_service, streak_service
from app.services.ai_providers import AIProvider, TemplateProvider, get_provider

DAILY_QUESTIONS = [
    "Wofür bist du heute dankbar?",
    "Was hat dich heute besonders beschäftigt?",
    "Was war heute dein schönster Moment?",
    "Was möchtest du von heute mitnehmen?",
    "Gab es heute etwas, das dich überrascht hat?",
    "Was hast du heute gelernt?",
    "Was möchtest du morgen anders machen?",
]

SUMMARY_SYSTEM_PROMPT = (
    "Du bist ein unterstützender Journal-Begleiter. Formuliere aus den "
    "gegebenen, bereits berechneten Zahlen eine kurze, freundliche "
    "Wochenzusammenfassung auf Deutsch (max. 6 Sätze, direkte Anrede 'du'). "
    "Wichtig: Erfinde keine Zahlen. Keine Diagnosen, keine Kausalaussagen — "
    "beschreibe nur Muster in den dokumentierten Daten."
)


def get_daily_question(for_date: date | None = None) -> dict:
    """Deterministic daily question — same question for everyone on a day."""
    day = for_date or date.today()
    question = DAILY_QUESTIONS[day.toordinal() % len(DAILY_QUESTIONS)]
    return {"question": question}


def _week_range(reference: date | None = None) -> tuple[date, date]:
    """Monday..Sunday of the week containing `reference` (default: today)."""
    ref = reference or date.today()
    start = ref - timedelta(days=ref.weekday())
    return start, start + timedelta(days=6)


def _collect_week_facts(db: Session, user_id: int) -> dict:
    """Aggregate the numbers for the weekly summary (privacy-filtered)."""
    start, end = _week_range()
    entries = list(
        db.scalars(
            select(JournalEntry).where(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start,
                JournalEntry.entry_date <= end,
            )
        )
    )
    moods = [e.mood_score for e in entries if e.mood_score is not None]
    stress = [e.stress_level for e in entries if e.stress_level is not None]

    emotion_counts: dict[str, int] = {}
    for entry in entries:
        for link in entry.emotions:
            emotion_counts[link.emotion.name] = (
                emotion_counts.get(link.emotion.name, 0) + 1
            )
    top_emotions = sorted(
        emotion_counts, key=emotion_counts.get, reverse=True
    )[:3]

    return {
        "week_start": start,
        "week_end": end,
        "days_written": len(entries),
        "average_mood": round(sum(moods) / len(moods), 1) if moods else None,
        "average_stress": round(sum(stress) / len(stress), 1) if stress else None,
        "sport_days": sum(1 for e in entries if e.did_sport),
        "top_emotions": top_emotions,
        "current_streak": streak_service.get_streaks(db, user_id)["current_streak"],
        # Deliberately NOT included: had_sex, cried, pain fields, note texts
    }


def _facts_to_template_text(facts: dict) -> str:
    """Deterministic German fallback text built purely from the numbers."""
    parts = [
        f"Diese Woche hast du an {facts['days_written']} von 7 Tagen geschrieben."
    ]
    if facts["average_mood"] is not None:
        mood = f"{facts['average_mood']:.1f}".replace(".", ",")
        parts.append(f"Deine durchschnittliche Stimmung lag bei {mood} von 5.")
    if facts["top_emotions"]:
        emotions = "“, „".join(facts["top_emotions"])
        parts.append(
            f"Besonders häufig hast du die Emotionen „{emotions}“ dokumentiert."
        )
    if facts["sport_days"] > 0:
        day_word = "Tag" if facts["sport_days"] == 1 else "Tagen"
        parts.append(f"Du hast an {facts['sport_days']} {day_word} Sport gemacht.")
    if facts["average_stress"] is not None:
        stress = f"{facts['average_stress']:.1f}".replace(".", ",")
        parts.append(f"Dein durchschnittliches Stresslevel lag bei {stress} von 5.")
    if facts["current_streak"] >= 2:
        parts.append(
            f"Deine aktuelle Streak liegt bei {facts['current_streak']} Tagen 🔥"
        )
    return " ".join(parts)


def generate_weekly_summary(
    db: Session, user_id: int, provider: AIProvider | None = None
) -> dict:
    """Weekly summary: numbers from the backend, wording from the provider."""
    facts = _collect_week_facts(db, user_id)

    if facts["days_written"] == 0:
        return {
            "week_start": facts["week_start"],
            "week_end": facts["week_end"],
            "summary": (
                "Diese Woche hast du noch keinen Eintrag geschrieben. "
                "Starte mit dem heutigen Tag! 🌱"
            ),
            "facts": facts,
        }

    provider = provider or get_provider()
    template_text = _facts_to_template_text(facts)

    if isinstance(provider, TemplateProvider):
        summary = template_text
    else:
        # External provider gets ONLY the aggregated numbers, phrased as text
        summary = provider.generate_text(SUMMARY_SYSTEM_PROMPT, template_text)

    return {
        "week_start": facts["week_start"],
        "week_end": facts["week_end"],
        "summary": summary,
        "facts": facts,
    }
