set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starte Datenbank (Docker)..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d db

echo "Warte auf Datenbank..."
until docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db pg_isready -U moodly >/dev/null 2>&1; do
  sleep 1
done

cd "$ROOT_DIR/backend"
source .venv/bin/activate

echo "Wende Migrationen an..."
alembic upgrade head

echo "Starte Backend..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd "$ROOT_DIR/frontend"
echo "Starte Frontend..."
python3 -m http.server 3000 &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Beende Backend und Frontend..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

echo ""
echo "Moodly läuft:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000/docs"
echo ""
echo "Zum Beenden: Ctrl+C"

wait
