# 🌤️ Moodly

Persönliche Journal-, Mood-, Habit- und Analytics-Web-App.

Ein Nutzer dokumentiert jeden Tag Stimmung, Emotionen, Gesundheit, Sport und
Reflexionen. Daraus entstehen Statistiken, Trends, Streaks, Achievements und
KI-gestützte Wochenzusammenfassungen — alle Daten bleiben privat und sind
strikt einem Benutzerkonto zugeordnet.

---

## Features

| Bereich | Umfang |
|---|---|
| **Journal** | Ein Eintrag pro Tag: Stimmung, Energie, Stress, Schlaf, Sport, Sex, Weinen, Kopfschmerzen, Schmerzen (0–10, Ort), Notizen, Dankbarkeit, positive/negative Ereignisse, Reflexion |
| **Emotionen** | 14 Emotionen als Chips, Mehrfachauswahl mit Intensität (Many-to-Many) |
| **Kalender** | Monatsansicht mit Stimmungs-Emoji pro Tag, Klick öffnet den Eintrag |
| **Habits** | Eigene Gewohnheiten (Ja/Nein oder numerisch mit Ziel), tägliches Abhaken |
| **Analytics** | Stimmungsverlauf, Stimmung pro Wochentag, Sport vs. Stimmung, Habit-Erfolgsquote, häufigste Emotionen (Chart.js) |
| **Gamification** | Aktuelle & längste Streak, 8 regelbasierte Achievements |
| **KI** | Tägliche Reflexionsfrage, Wochenzusammenfassung (anbieterunabhängig) |
| **Dashboard** | Streak, heutige Stimmung, Wochenübersicht, Habits, Wochenrückblick |
| **UX** | Responsive, Dark Mode, Toasts, Empty States, automatische Login-Umleitung |

---

## Technologien

- **Backend:** Python 3, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, JWT (PyJWT), bcrypt
- **Datenbank:** SQLite (Entwicklung) → PostgreSQL (Produktion)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6-Module, Fetch API), Chart.js
- **Analytics:** pandas, NumPy
- **Tests:** pytest (54 Tests)

---

## Architektur

Klare Schichtentrennung — jede Ebene hat genau eine Aufgabe:

```text
Router      →  HTTP: Endpunkte, Statuscodes, Request/Response-Schemas
Service     →  Business-Logik, Validierung, Regeln
Repository  →  Datenbankzugriffe (immer user-scoped)
Model       →  SQLAlchemy-Tabellen
```

Wichtige Entwurfsentscheidungen:

- **User-Isolation im Repository:** Fremde Datensätze werden als „nicht
  vorhanden“ behandelt (404 statt 403) — sie verraten nicht einmal ihre Existenz.
- **Statistik getrennt von Sprache:** `analytics_service` rechnet alle Zahlen mit
  pandas; die KI darf sie nur sprachlich verpacken, niemals erfinden.
- **Achievements regelbasiert:** Definitionen in der Datenbank, Regeln als
  Funktionen in einem Dict — ein neues Achievement = ein Eintrag + eine Funktion.
- **KI anbieterunabhängig:** `AIProvider`-Interface mit Template- und
  Anthropic-Implementierung; die Business-Logik kennt keinen konkreten Anbieter.

### Projektstruktur

```text
Moodly/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI-App, CORS, Fehlerformat, /health
│   │   ├── core/                # config, security (JWT/bcrypt), dependencies, errors
│   │   ├── database/            # Engine, Session, Base, Seed-Daten
│   │   ├── models/              # User, JournalEntry, Emotion, Habit, Achievement …
│   │   ├── schemas/             # Pydantic-Schemas (Validierung)
│   │   ├── routers/             # auth, users, journal, emotions, habits,
│   │   │                        #   analytics, achievements, ai
│   │   ├── services/            # Business-Logik inkl. analytics/ai/achievement
│   │   ├── repositories/        # user, journal, habit
│   │   └── utils/
│   ├── alembic/                 # Datenbankmigrationen
│   ├── tests/                   # 54 pytest-Tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html · login.html · register.html · dashboard.html
│   ├── journal.html · calendar.html · habits.html
│   ├── analytics.html · achievements.html
│   ├── css/main.css             # CSS-Variablen inkl. Dark Mode
│   └── js/                      # config, api, auth, dashboard, journal,
│                                #   calendar, habits, analytics, achievements, utils
├── docker-compose.yml           # PostgreSQL + Backend
└── README.md
```

---

## Installation & Start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # dann SECRET_KEY setzen (siehe unten)
alembic upgrade head               # Datenbank anlegen
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Health-Check: http://localhost:8000/health
- **Swagger-Doku: http://localhost:8000/docs**

Einen sicheren `SECRET_KEY` erzeugen:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Frontend

Das Frontend ist statisch — ein einfacher Webserver genügt:

```bash
cd frontend
python3 -m http.server 3000
```

Dann http://localhost:3000 öffnen, registrieren und loslegen.

> Die Startseite zeigt an, ob das Backend erreichbar ist. Läuft dein Frontend
> auf einem anderen Port, ergänze ihn in `CORS_ORIGINS` in der `.env`.

---

## Datenbank & Migrationen

Änderungen am Schema laufen immer über Alembic — die Datenbank muss nie
gelöscht werden:

```bash
alembic revision --autogenerate -m "beschreibung"   # Migration erzeugen
alembic upgrade head                                # anwenden
alembic downgrade -1                                # letzte zurücknehmen
alembic history                                     # Verlauf ansehen
```

### Testdaten

Für Analytics braucht es Daten. Das Seed-Script erzeugt 90 Tage klar
gekennzeichnete Testeinträge (überschreibt niemals echte Tage):

```bash
python -m app.database.seed_dev_data deine@email.de
```

---

## Tests

```bash
cd backend && source .venv/bin/activate
python -m pytest              # 54 Tests
python -m pytest -v           # ausführlich
```

Abgedeckt sind u. a. Registrierung/Login, JWT-Schutz, Journal-CRUD,
**dass fremde Einträge nicht lesbar sind**, Habit-Upsert, Analytics-Schwellenwerte,
Streak-Berechnung, Achievement-Auslösung und dass sensible Felder nicht in
KI-Prompts landen.

Jeder Test läuft gegen eine frische In-Memory-Datenbank — deine echten Daten
werden nie berührt.

---

## Environment Variables

| Variable | Beschreibung |
|---|---|
| `DATABASE_URL` | `sqlite:///./moodly.db` oder `postgresql+psycopg://user:pw@host:5432/db` |
| `SECRET_KEY` | Signierschlüssel für JWTs — lang und zufällig |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token-Gültigkeit (Standard 60) |
| `ENVIRONMENT` | `development` oder `production` |
| `CORS_ORIGINS` | Kommagetrennte Liste erlaubter Frontend-Domains |
| `AI_API_KEY` | Optional. Leer = deterministische Texte ohne externen Anbieter |

`.env` steht in `.gitignore` und darf **niemals** committet werden.

---

## API-Dokumentation

Vollständig interaktiv unter `/docs`. Überblick:

| Methode & Pfad | Zweck |
|---|---|
| `POST /auth/register` · `POST /auth/login` | Konto anlegen, Token erhalten |
| `GET /users/me` | Eigenes Profil |
| `POST /journal` · `GET /journal` | Eintrag anlegen / auflisten |
| `GET /journal/today` · `GET /journal/date/{datum}` | Eintrag laden |
| `PUT /journal/{id}` · `DELETE /journal/{id}` | Ändern / löschen |
| `GET /journal/calendar` | Leichtgewichtig: Datum + Stimmung |
| `GET /emotions` | Emotionskatalog |
| `POST/GET/PUT/DELETE /habits` | Gewohnheiten verwalten |
| `GET /habits/daily` | Habits inkl. Tagesstatus |
| `POST/GET /habits/{id}/logs` | Abhaken / Historie |
| `GET /analytics/summary` · `/mood` · `/weekday` · `/sport` · `/habits` · `/emotions` | Statistiken |
| `GET /achievements` · `GET /streak` | Gamification |
| `GET /ai/daily-question` · `POST /ai/weekly-summary` | KI-Funktionen |
| `GET /health` | Health-Check (API + Datenbank) |

Alle Endpunkte außer `/auth/*` und `/health` erfordern den Header
`Authorization: Bearer <token>`.

**Einheitliches Fehlerformat:**

```json
{ "error": true, "message": "Journaleintrag nicht gefunden." }
```

---

## Datenschutz

Die App verarbeitet sehr sensible Daten. Was technisch dafür getan wird:

- Passwörter werden mit **bcrypt** gehasht — nie im Klartext gespeichert oder geloggt.
- Login-Fehler nennen nie, ob die E-Mail existiert (kein User-Enumeration).
- Jede Datenbankabfrage ist an die eingeloggte `user_id` gebunden.
- **Journaltexte, Sex-, Weinen- und Schmerzdaten werden nie geloggt** und
  **nie an einen externen KI-Anbieter geschickt** — der Wochenrückblick nutzt
  ausschließlich aggregierte Zahlen (Tage, Durchschnitte, Emotionsnamen).
  Ein eigener Test sichert das ab.
- Fehlermeldungen enthalten keine internen Details und keine Eingabewerte.
- Secrets ausschließlich über `.env`, niemals im Code.

**Analytics beschreiben, sie diagnostizieren nicht.** Aussagen sind bewusst
formuliert als „In deinen dokumentierten Daten …“ / „war um 0,8 Punkte höher“ —
niemals als Ursache-Wirkung oder medizinische Einschätzung. Bei zu wenig Daten
erscheint „Noch nicht genügend Daten für eine zuverlässige Auswertung.“

---

## Deployment

### 1. Lokal produktionsnah (Docker Compose, mit PostgreSQL)

```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  docker compose up --build
```

Startet PostgreSQL und das Backend, wendet Migrationen automatisch an.

### 2. Backend hosten (Render, Railway, Fly.io)

1. Repository verbinden, `backend/Dockerfile` als Build-Quelle wählen.
2. PostgreSQL-Datenbank des Anbieters anlegen.
3. Environment Variables setzen:
   - `DATABASE_URL` (von der Datenbank des Anbieters — `postgres://` wird
     automatisch in das von SQLAlchemy erwartete Format übersetzt)
   - `SECRET_KEY` (neu erzeugen, nicht den Entwicklungswert)
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://deine-frontend-domain`

Migrationen laufen beim Start automatisch (`alembic upgrade head`).

> Sicherheitsnetz: In `production` verweigert der Server den Start, wenn
> `SECRET_KEY` noch der Standardwert ist.

### 3. Frontend hosten (Netlify, Vercel, GitHub Pages)

Den Ordner `frontend/` deployen und in **`frontend/js/config.js`** die URL des
deployten Backends eintragen — das ist die einzige Datei, die sich ändert:

```javascript
export const API_BASE_URL = "https://dein-backend.onrender.com";
```

---

## Entwicklungsphasen

| Phase | Inhalt | Status |
|---|---|---|
| 1 | Projektsetup, DB-Verbindung, Health-Endpoint | ✅ |
| 2 | Authentication (User, JWT, geschützte Routen) | ✅ |
| 3 | Journal & Emotionen (CRUD, Unique Constraint) | ✅ |
| 4 | Frontend: Login, Dashboard, Tagesformular | ✅ |
| 5 | Habits & HabitLogs | ✅ |
| 6 | Analytics mit pandas & Chart.js | ✅ |
| 7 | Gamification: Streaks & Achievements | ✅ |
| 8 | KI: Tagesfrage & Wochenzusammenfassung | ✅ |
| 9 | UX: Kalender, Dark Mode, Session-Handling | ✅ |
| 10 | Deployment: Docker, PostgreSQL, Fehlerformat | ✅ |

---

## Mögliche nächste Schritte

Die Architektur ist auf Erweiterung ausgelegt:

- **Naheliegend:** Monatszusammenfassung (Wochenlogik ist wiederverwendbar),
  Ziele-Seite (Modell fehlt noch), Autosave im Journal, Habit deaktivieren
  statt löschen, CSV-/JSON-Export.
- **Weitere Tracking-Felder** (Schlafdauer, Wasser, Zyklus, Koffein …): neue
  Spalte im Modell + Alembic-Migration + Feld im Formular — die Analytics-
  Struktur nimmt sie ohne Umbau auf.
- **Mehrere Schmerzarten pro Tag:** eigene Tabelle analog zu den Emotionen.
- **KI-Follow-up-Fragen:** braucht Notiztexte im Prompt — bewusst noch nicht
  gebaut, da es eine explizite Einwilligung im UI erfordert.
