#!/bin/sh
set -e

# Démarré en root : on rend le volume d'uploads accessible à "app",
# puis on abandonne les privilèges pour tout le reste.
if [ "$(id -u)" = "0" ] && id app >/dev/null 2>&1 && command -v setpriv >/dev/null; then
  UPLOADS="${UPLOAD_DIR:-uploads}"
  mkdir -p "$UPLOADS"
  chown -R app:app "$UPLOADS"
  exec setpriv --reuid=app --regid=app --init-groups "$0" "$@"
fi

echo "Waiting for database..."

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

echo "Running migrations..."
python migrate.py

echo "Running seeds..."
python -m seed_initial_data

echo "Starting FastAPI"
# --proxy-headers : l'IP réelle du client (X-Forwarded-For) est utilisée,
# indispensable pour la limitation de débit derrière un reverse proxy.
# Restreindre FORWARDED_ALLOW_IPS à l'IP du proxy si le port 8000 est exposé.
exec uvicorn main:app --host 0.0.0.0 --port 8000 \
  --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
