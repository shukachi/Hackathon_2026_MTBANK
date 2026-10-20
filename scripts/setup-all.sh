#!/usr/bin/env bash
# Полная установка проекта для нового разработчика в команде.
#
#   bash scripts/setup-all.sh
#
# Порядок шагов важен: Ollama с моделью ставится ПЕРВОЙ, потому что от неё
# зависит AI-слой демо (шаг 1 — обязательный, идёт до python/npm).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m  ✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --- 1. Ollama + qwen2.5:1.5b (обязательный шаг) -----------------------------

log "Шаг 1/5: Ollama + модель qwen2.5:1.5b"
bash scripts/setup-ollama.sh
ok "Ollama готова"

# --- 2. Backend --------------------------------------------------------------

log "Шаг 2/5: backend-зависимости"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python -m venv .venv
  ok "Создан venv"
else
  ok "venv уже существует, переиспользуем"
fi

# Активировать venv и поставить зависимости
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
ok "Python-зависимости установлены"

# --- 3. Конфиги --------------------------------------------------------------

log "Шаг 3/5: конфигурация (.env)"
if [ ! -f .env ]; then
  cp .env.example .env
  ok "Создан backend/.env из .env.example"
else
  ok "backend/.env уже существует"
fi

cd "$ROOT/frontend"
if [ ! -f .env ]; then
  cp .env.example .env
  ok "Создан frontend/.env из .env.example"
else
  ok "frontend/.env уже существует"
fi

# --- 4. Frontend -------------------------------------------------------------

log "Шаг 4/5: frontend-зависимости"
npm install --no-fund --no-audit
ok "Node-зависимости установлены"

# --- 5. Проверка -------------------------------------------------------------

log "Шаг 5/5: проверка"
cd "$ROOT/backend"
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

PYTHONIOENCODING=utf-8 python - <<'PY'
import sys
try:
    import fastapi, sqlalchemy, pydantic, httpx  # noqa: F401
    print("  OK  Python-зависимости импортируются")
except ImportError as exc:
    print(f"  FAIL Не хватает зависимости: {exc}")
    sys.exit(1)
PY

cd "$ROOT"
ok "Ollama: модель $(curl -fsS http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4) на http://localhost:11434"

cat <<'EOF'

──────────────────────────────────────────────────────────────
Установка завершена. Дальше — три терминала:

  1) ollama serve
  2) cd backend && source .venv/Scripts/activate && uvicorn app.main:app --reload --port 8000
  3) cd frontend && npm run dev

Демо-данные (один раз):  cd backend && python -m app.seed
Проверка готовности AI:  curl http://127.0.0.1:8000/health   →  "ai_ready": true
──────────────────────────────────────────────────────────────
EOF
