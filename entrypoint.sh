#!/bin/sh
set -e

echo "⏳ Waiting for database..."

# Utilise DATABASE_URL (pas de mot de passe en dur).
# On ne réessaie que si la base n'est pas encore joignable ;
# une erreur d'authentification fait échouer le démarrage tout de suite.
until python - <<'PY'
import os, sys, psycopg2

try:
    psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=3).close()
except psycopg2.OperationalError as e:
    msg = str(e)
    if "password authentication failed" in msg:
        print("FATAL: " + msg.strip(), file=sys.stderr)
        sys.exit(2)          # erreur de config : inutile de réessayer
    sys.exit(1)              # base pas prête : on réessaie
PY
do
  code=$?
  if [ "$code" -eq 2 ]; then
    echo "Authentication error: check DATABASE_URL and POSTGRES_PASSWORD"
    exit 1
  fi
  echo "DB not ready... retrying"
  sleep 2
done

echo "Database ready"

echo "Running seeds..."
python -m seed_initial_data

echo "Starting FastAPI"
exec uvicorn main:app --host 0.0.0.0 --port 8000