# Moby Family — «Детско-семейный банкинг в Moby»

Прототип хакатона МТБанк: веб-приложение семейного банкинга с локальным AI-ассистентом.
Фронтенд — React + TypeScript + Vite, backend — FastAPI + SQLAlchemy, AI-слой — **локальная
Ollama** с моделью `qwen2.5:1.5b` (данные не покидают машину разработчика).

Подробности концепции — в [`plan.md`](plan.md), материалы презентации — в [`docs/`](docs/).

---

## Обязательные шаги установки

Полный чеклист, который должен пройти каждый разработчик в команде. Пункты 1–4 — обязательные,
без них демо не запустится в заявленном виде (шаг 1 — чтобы AI-сценарии шли через реальную
модель, а не через rule-based fallback).

Быстрый путь — одна команда, делает всё по порядку:

```bash
bash scripts/setup-all.sh
```

| # | Что | Команда | Проверка |
|---|---|---|---|
| 1 | **Ollama + модель `qwen2.5:1.5b`** | `bash scripts/setup-ollama.sh` (Windows git bash) или `powershell -ExecutionPolicy Bypass -File scripts/setup-ollama.ps1` | `curl http://localhost:11434/api/tags` — в списке `qwen2.5:1.5b` |
| 2 | Python 3.11+ | `python --version` | версия 3.11 или новее |
| 3 | Backend-зависимости | `cd backend && python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt` | `python -c "import fastapi"` без ошибок |
| 4 | Frontend-зависимости | `cd frontend && npm install` | `npm run build` проходит |
| 5 | Конфиг | `cp backend/.env.example backend/.env` и `cp frontend/.env.example frontend/.env` | в `.env` заданы `OLLAMA_URL` и `MODEL_NAME=qwen2.5:1.5b` |
| 6 | Seed демо-данных | `cd backend && python -m app.seed` | сообщение о создании демо-семьи |
| 7 | Ollama-сервис запущен | `ollama serve` (в отдельном терминале; на Windows трей Ollama делает это сам) | `curl http://localhost:11434/api/tags` отвечает |

### Шаг 1 подробно

```bash
bash scripts/setup-ollama.sh
```

Скрипт идемпотентен: найдёт уже установленную Ollama, поднимет сервер, скачает
`qwen2.5:1.5b` (~1 ГБ, один раз) и проверит, что модель реально отвечает. Если Ollama
не установлена — скачает и поставит её сам (Windows: `OllamaSetup.exe` из
`https://ollama.com/download/`; Linux/macOS: `https://ollama.com/install.sh`).

Ручной вариант, если скрипт недоступен:

```bash
# 1) установить Ollama с https://ollama.com/download/
# 2) поднять сервис
ollama serve
# 3) скачать модель
ollama pull qwen2.5:1.5b
# 4) проверить
ollama run qwen2.5:1.5b "Say OK"
```

---

## Запуск

Три терминала:

```bash
# 1) Ollama
ollama serve

# 2) Backend
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --port 8000

# 3) Frontend
cd frontend
npm run dev
```

- Фронтенд: http://localhost:5173
- Swagger UI: http://127.0.0.1:8000/docs
- Health-check (в т.ч. готовность AI-слоя): http://127.0.0.1:8000/health

Ответ `/health` показывает, готов ли AI-слой:

```json
{
  "status": "ok",
  "ai_ready": true,
  "ollama": {
    "url": "http://localhost:11434",
    "model": "qwen2.5:1.5b",
    "available": true,
    "model_present": true
  }
}
```

Если `ai_ready: false` — Ollama не поднята или модель не скачана: backend работает,
но AI-роуты отдают rule-based fallback (демо не падает).

## Система орешков

Баллы в интерфейсе называются **орешками**:

- **10 орешков = 1 рубль** — орешки конвертируются в рубли на счёт в профиле;
- **кешбэк 5%** — на операции в семейных категориях (еда, сладости, игрушки,
  образование, развлечения); игры и подписки без кешбэка;
- **награды за квесты** — родитель задаёт квест и указывает награду орешками;
- орешки копятся **раздельно** у ребёнка и у родителя (ТЗ п.4.3).

Страницы: «Мои орешки» у ребёнка (`/child/nuts`) и «Орешки» у родителя
(`/parent/nuts`) — с историей начислений и кнопкой конвертации.

## Карты и баланс

У ребёнка может быть несколько карт — родитель выпускает дополнительные из
кабинета и задаёт им стартовый баланс (карманные деньги). Баланс карты виден
в блоке «Реквизиты карты» вместе с номером, статусом и типом карты; он
уменьшается при покупках.

## Вкладка Step: оплата по QR

У ребёнка и подростка есть отдельная вкладка **Step** (`/child/step`) —
генератор временного QR-кода для оплаты в магазине.

- сначала выбираются **категория покупки** и **карта**, со счёта которой
  будут списаны деньги;
- код **одноразовый** и живёт **10 минут** (таймер идёт вниз, потом код
  гаснет);
- «сканирование» (кнопка «Оплатить») списывает сумму с выбранной карты,
  создаёт обычную транзакцию и начисляет кешбэк орешками по тем же правилам;
- код можно отменить; чужой код оплатить нельзя, родитель QR ребёнка может
  только посмотреть.

## Демо-учётки

После `python -m app.seed`:

| Роль | Логин | Пароль |
|---|---|---|
| Родитель | `parent@moby.by` | `Parent123!` |
| Ребёнок | `anna10` | `Child123!` |
| Подросток | `max16` | `Teen123!` |

## Структура репозитория

```
backend/    FastAPI: авторизация (JWT+cookie), БД (SQLAlchemy/SQLite), карты (несколько
            на ребёнка, баланс), лимиты, квесты, лояльность (орешки: кешбэк,
            конвертация), временные QR-платежи (вкладка Step), access-requests,
            AI-роуты
frontend/   React + TS + Vite SPA: дашборды родителя и ребёнка, карты с реквизитами,
            орешки с конвертацией, вкладка Step (QR на оплату), AI-чат, NL-команды
LOG.MD      журнал реализованных фич (индекс + описание каждой)
scripts/    setup-all.sh — полная установка одной командой;
            setup-ollama.sh / setup-ollama.ps1 — обязательная установка Ollama + модели
docs/       pitch-deck, product-canvas, economics, legal-notes, demo-script
TZ/         исходные материалы хакатона
plan.md     план проекта
```

Подробные README: [`backend/README.md`](backend/README.md), [`frontend/README.md`](frontend/README.md).
