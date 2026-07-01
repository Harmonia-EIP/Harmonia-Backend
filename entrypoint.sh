#!/bin/sh

echo "⏳ Waiting for database..."

until python -c "
import psycopg2
import time
try:
    psycopg2.connect(
        host='db',
        database='harmonia',
        user='harmonia',
        password='harmonia123'
    )
except:
    time.sleep(1)
    raise
"; do
  echo "DB not ready... retrying"
  sleep 2
done

echo "✅ Database ready"

echo "🌱 Running seeds..."
python -m seed_initial_data

echo "🚀 Starting FastAPI"
uvicorn main:app --host 0.0.0.0 --port 8000
