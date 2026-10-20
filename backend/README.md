# Moby Family — Backend

FastAPI backend для прототипа «Детско-семейный банкинг в Moby» (хакатон МТБанк).
Подробное описание концепции и архитектуры — в `../plan.md`.

## Стек

FastAPI, SQLAlchemy (SQLite по умолчанию), Pydantic v2, JWT (pyjwt) в httpOnly cookie,
bcrypt для хэширования паролей, AI-слой на локальной Ollama (`qwen2.5:1.5b`) с graceful
fallback на rule-based парсер, если сервис недоступен.

## Установка и запуск (Windows, git bash)

Шаг 0 (обязательный, до остальных) — Ollama + локальная модель. Выполняется из корня
репозитория:

```bash
bash ../scripts/setup-ollama.sh
```

Скрипт скачает и поставит Ollama (если её нет), поднимет сервис, скачает модель
`qwen2.5:1.5b` и проверит, что она отвечает. Полный чеклист установки — в
[`../README.md`](../README.md).

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env   # при необходимости поменяйте значения, особенно JWT_SECRET в проде
```

### Запуск сервера

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- Health-check: http://127.0.0.1:8000/health

БД (SQLite-файл `app.db`) создаётся автоматически при старте приложения (`Base.metadata.create_all`)
и переживает перезапуск сервера — данные не теряются.

### Наполнение демо-данными

Сид-скрипт запускается ОТДЕЛЬНО, руками, не при каждом старте сервера:

```bash
python -m app.seed
```

Если `parent@moby.by` уже есть в базе — скрипт просто сообщит об этом и ничего не создаст повторно.
Чтобы пересоздать демо-данные с нуля — удалите `app.db` и запустите сид заново.

### Демо-учётки (после `python -m app.seed`)

| Роль      | Логин            | Пароль      | Комментарий                         |
|-----------|------------------|-------------|--------------------------------------|
| Родитель  | `parent@moby.by` | `Parent123!`| Иван Иванов                          |
| Ребёнок   | `anna10`         | `Child123!` | Анна Иванова, 10 лет, карта+лояльность |
| Подросток | `max16`          | `Teen123!`  | Максим Иванов, 16 лет, карта+лояльность |

Также создаются: 30 транзакций за последние ~80 дней на обеих картах, лимит `sweets 50 BYN/week`
для Анны и общий лимит `200 BYN/month` для Максима, 3 квеста (разных статусов), 2 цели накопления
и один pending access-request от `max16` (feature=`subscription`).

## Тесты

```bash
python -m pytest -v
```

Тесты используют отдельную SQLite-базу `test.db` (создаётся/очищается автоматически через
fixture в `tests/conftest.py`), не трогают рабочий `app.db`.

## Структура

```
app/
  main.py          # FastAPI app, CORS, роуты, lifespan (create_all)
  db.py             # SQLAlchemy engine/session
  seed.py           # ручной скрипт демо-данных (python -m app.seed)
  models/           # SQLAlchemy ORM-модели
  schemas/          # Pydantic-схемы запросов/ответов
  routers/          # auth, family, cards, transactions, limits, goals, quests,
                     # loyalty, access_requests, ai
  services/
    limits_engine.py     # проверка трат против лимитов
    ollama_client.py     # клиент к локальной Ollama (graceful fallback -> None)
    rag.py                # простой keyword-RAG по транзакциям для /ai/chat
    nl_command_parser.py  # LLM JSON-парсинг команды родителя + rule-based fallback
  core/
    config.py        # Settings (.env)
    security.py       # bcrypt + JWT
    deps.py            # get_current_user / get_current_parent / get_child_owned_by_parent
tests/              # pytest, TestClient, отдельная test.db
```

## AI-слой и Ollama

Ollama и модель `qwen2.5:1.5b` — **обязательная** часть установки (см. `../scripts/setup-ollama.sh`
и раздел «Обязательные шаги установки» в `../README.md`): AI-сценарии демо должны идти через
реальную локальную модель, а не через rule-based fallback.

`services/ollama_client.chat()` обращается к `http://localhost:11434/api/chat`
с таймаутом `OLLAMA_TIMEOUT_SEC` (60 с по умолчанию — первый запрос после перезапуска
сервиса подгружает модель в память) и возвращает `None` при любой ошибке сети/таймаута
(никогда не бросает исключение наружу). Оба AI-роута (`/ai/chat`, `/ai/parent-command`)
в этом случае автоматически переключаются на rule-based fallback — задокументировано
в коде и проверено тестами (`tests/test_ai_command_parser.py`) и вручную (см. ниже).

Модель задаётся в `.env` через `MODEL_NAME` (по умолчанию `qwen2.5:1.5b`), адрес — через
`OLLAMA_URL` (по умолчанию `http://localhost:11434`).

Проверить готовность AI-слоя:

```bash
curl http://127.0.0.1:8000/health
```

Ответ содержит `ai_ready: true` и блок `ollama` с `available` / `model_present` — удобно
проверять одним запросом, что сервис поднят и нужная модель скачана.

Системные промпты пока хранятся как константы в `app/routers/ai.py` и
`app/services/nl_command_parser.py`. TODO (вне зоны backend/): когда появится папка
`ai/prompts/` в корне репозитория с файлами `child_assistant_system.md` и
`parent_command_system.md`, переключить код на чтение промптов из файлов.

## Известные ограничения / TODO

- `POST /auth/refresh` не реализован (не требовался явно, полезен для продакшена).
- RAG для `/ai/chat` — простой keyword-match без векторной БД, как и предполагает MVP.
- Нет Alembic-миграций — `Base.metadata.create_all` достаточно для хакатона (см. plan.md §5.1).
- `cookie secure=False` — осознанно для локальной HTTP-демки; переключить на `True` в проде (HTTPS).
- Промпты AI хранятся в коде, а не файлах `ai/prompts/*.md` (эта папка не в зоне backend/).
