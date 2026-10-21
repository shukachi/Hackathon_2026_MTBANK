#!/usr/bin/env bash
# Обязательный шаг установки: Ollama + локальная модель qwen3:8b.
#
# Скрипт идемпотентен: если Ollama уже установлена и модель уже скачана —
# ничего не переустанавливает, только проверяет. Запуск:
#
#   bash scripts/setup-ollama.sh
#
# Поддерживаются Windows (git bash), Linux, macOS.
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen3:8b}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

log()  { printf '\033[1;34m[ollama]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m  ✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --- 1. Найти или установить Ollama -----------------------------------------

find_ollama() {
  if command -v ollama >/dev/null 2>&1; then
    command -v ollama
    return 0
  fi
  # Стандартный путь установщика Ollama на Windows
  for candidate in \
    "$LOCALAPPDATA/Programs/Ollama/ollama.exe" \
    "/c/Users/$USERNAME/AppData/Local/Programs/Ollama/ollama.exe" \
    "/usr/local/bin/ollama" \
    "/opt/homebrew/bin/ollama"; do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

install_ollama() {
  log "Ollama не найдена — устанавливаю..."

  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      local installer="$TEMP/ollama-setup.exe"
      log "Скачиваю https://ollama.com/download/OllamaSetup.exe"
      curl -fsSL https://ollama.com/download/OllamaSetup.exe -o "$installer"
      # Установщик Ollama ставится в %LOCALAPPDATA%\Programs\Ollama и сам добавляет
      # путь в PATH пользователя. /S — тихая установка.
      "$installer" /S || die "Не удалось установить Ollama. Запусти установщик вручную: $installer"
      ok "Ollama установлена"
      ;;
    *)
      log "Устанавливаю через официальный скрипт https://ollama.com/install.sh"
      curl -fsSL https://ollama.com/install.sh | sh
      ok "Ollama установлена"
      ;;
  esac
}

OLLAMA_BIN="$(find_ollama || true)"

if [ -z "$OLLAMA_BIN" ]; then
  install_ollama
  # После установки путь может не попасть в текущую сессию PATH
  OLLAMA_BIN="$(find_ollama || true)"
  [ -n "$OLLAMA_BIN" ] || die "Ollama установилась, но ollama.exe не найден в PATH. Перезапусти терминал и повтори."
fi

ok "Ollama найдена: $OLLAMA_BIN"
"$OLLAMA_BIN" --version 2>/dev/null | head -1 || true

# --- 2. Поднять сервер Ollama ------------------------------------------------

server_up() {
  curl -fsS -m 2 "http://localhost:${OLLAMA_PORT}/api/tags" >/dev/null 2>&1
}

if server_up; then
  ok "Сервер Ollama уже отвечает на порту ${OLLAMA_PORT}"
else
  log "Запускаю сервер Ollama в фоне..."
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) "$OLLAMA_BIN" serve >/dev/null 2>&1 & ;;
    *)                   nohup "$OLLAMA_BIN" serve >/dev/null 2>&1 & ;;
  esac

  for _ in $(seq 1 30); do
    if server_up; then break; fi
    sleep 1
  done

  if server_up; then
    ok "Сервер Ollama поднят на порту ${OLLAMA_PORT}"
  else
    die "Сервер Ollama не поднялся. Запусти вручную в отдельном терминале: ollama serve"
  fi
fi

# --- 3. Скачать модель -------------------------------------------------------

model_present() {
  curl -fsS -m 5 "http://localhost:${OLLAMA_PORT}/api/tags" 2>/dev/null \
    | grep -q "\"${MODEL}\""
}

if model_present; then
  ok "Модель ${MODEL} уже скачана"
else
  log "Скачиваю модель ${MODEL} (это ~5 ГБ, один раз)..."
  "$OLLAMA_BIN" pull "$MODEL"
  ok "Модель ${MODEL} скачана"
fi

# --- 4. Проверить, что модель реально отвечает ------------------------------

log "Проверяю инференс (8B на CPU думает ~15 секунд, это нормально)..."
REPLY="$(curl -fsS -m 300 "http://localhost:${OLLAMA_PORT}/api/chat" \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"stream\":false,\"think\":false}" \
  | tr -d '\n' | sed -n 's/.*"content":"\([^"]*\)".*/\1/p' || true)"

if [ -z "$REPLY" ]; then
  die "Модель не ответила. Проверь вручную: ollama run ${MODEL} \"Say OK\""
fi

ok "Модель отвечает: ${REPLY}"
echo
printf '\033[1;32mOllama готова.\033[0m Модель: %s, endpoint: http://localhost:%s\n' "$MODEL" "$OLLAMA_PORT"
echo "Проверить вручную:  curl http://localhost:${OLLAMA_PORT}/api/tags"
