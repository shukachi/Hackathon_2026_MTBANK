#!/usr/bin/env bash
#
# git-commit-push.sh —ステージ все изменения, сделать коммит и запушить в текущую ветку.
#
# Использование:
#   ./scripts/git-commit-push.so "сообщение коммита"
#   ./scripts/git-commit-push.sh        (сообщение запросится интерактивно)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ветка по умолчанию — main. Если мы на main, советуем создать feature-ветку,
# но не блокируем (пользователь сам решит).
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" == "main" ]]; then
  echo "Внимание: вы находитесь на ветке main."
  read -rp "Продолжить коммит на main? (y/N) " -n 1 REPLY
  echo
  if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    echo "Отменено. Создайте feature-ветку и повторите."
    exit 1
  fi
fi

# Показываем текущий статус
echo "=== git status ==="
git status --short

# Сообщение коммита
if [[ $# -ge 1 ]]; then
  COMMIT_MSG="$*"
else
  read -rp "Введите сообщение коммита: " COMMIT_MSG
  if [[ -z "$COMMIT_MSG" ]]; then
    echo "Ошибка: пустое сообщение коммита."
    exit 1
  fi
fi

# Добавляем стандартную атрибуцию Claude Code
FULL_MSG="${COMMIT_MSG}

Co-Authored-By: Claude Code <noreply@anthropic.com>"

echo "=== git add -A ==="
git add -A

echo "=== git commit ==="
git commit -m "$FULL_MSG"

echo "=== git push ==="
git push origin "$CURRENT_BRANCH"

echo "Готово: закоммичено и запушено в ветку '$CURRENT_BRANCH'."
