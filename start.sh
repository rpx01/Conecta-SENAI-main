#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP="${FLASK_APP:-conecta_senai.main}"

wait_for_database() {
  if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "[start] DATABASE_URL não definido; pulando espera pelo banco (SQLite?)."
    return 0
  fi

  if ! command -v pg_isready >/dev/null 2>&1; then
    echo "[start] pg_isready indisponível; não foi possível verificar o banco."
    return 0
  fi

  host_port=$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL", "")
parsed = urlparse(url)
if parsed.scheme.startswith("postgres"):
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    print(f"{host}:{port}")
else:
    raise SystemExit(1)
PY
  ) || {
    echo "[start] URL do banco não é Postgres; pulando espera."
    return 0
  }

  DB_HOST="${host_port%%:*}"
  DB_PORT="${host_port##*:}"

  for attempt in $(seq 1 30); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; then
      echo "[start] Banco disponível em ${DB_HOST}:${DB_PORT}."
      return 0
    fi
    echo "[start] Aguardando banco de dados... (${attempt}/30)"
    sleep 2
  done

  echo "[start] Banco não respondeu a tempo." >&2
  return 1
}

wait_for_database
echo "[start] Running DB migrations..."
ls -la migrations/versions
SCHEDULER_ENABLED=${SCHEDULER_ENABLED:-0} flask db upgrade
echo "[start] Starting Gunicorn..."
exec gunicorn "conecta_senai.main:create_app()" \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 1 \
  --threads 1 \
  --max-requests 200 \
  --max-requests-jitter 50 \
  --timeout 30 \
  --graceful-timeout 30 \
  --keep-alive 2 \
  --log-level info
