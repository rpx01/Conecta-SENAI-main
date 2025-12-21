#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP="${FLASK_APP:-conecta_senai.main}"

wait_for_db() {
  local db_url="${DATABASE_URL:-}"
  if [[ -z "${db_url}" || "${db_url}" == sqlite:* ]]; then
    echo "[start] DATABASE_URL aponta para SQLite ou não está definido; ignorando espera pelo banco."
    return 0
  fi

  # Extrai host/porta/usuário/senha da DATABASE_URL usando Python para suportar URLs completas.
  read -r DB_HOST DB_PORT DB_USER DB_PASSWORD < <(
    python - <<'PY'
import os
from urllib.parse import urlparse

url = os.getenv("DATABASE_URL", "")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
parsed = urlparse(url or "postgresql://postgres:postgres@localhost:5432/postgres")
host = parsed.hostname or "localhost"
port = parsed.port or 5432
user = parsed.username or "postgres"
password = parsed.password or ""
print(host, port, user, password)
PY
  )

  export PGPASSWORD="${DB_PASSWORD}"
  echo "[start] Aguardando banco de dados em ${DB_HOST}:${DB_PORT}..."
  for attempt in $(seq 1 30); do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" ${DB_USER:+-U "${DB_USER}"} >/dev/null 2>&1; then
      echo "[start] Banco de dados pronto!"
      unset PGPASSWORD
      return 0
    fi
    echo "[start] Tentativa ${attempt}/30: banco indisponível, tentando novamente em 2s..."
    sleep 2
  done

  echo "[start] Falha ao conectar ao banco de dados após múltiplas tentativas."
  return 1
}

wait_for_db

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
