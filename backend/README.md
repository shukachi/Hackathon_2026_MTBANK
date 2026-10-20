# Moby Family — Backend

FastAPI backend для прототипа «Детско-семейный банкинг в Moby» (хакатон МТБанк).
Подробное описание концепции и архитектуры — в `../plan.md`.

## Стек

FastAPI, SQLAlchemy (SQLite по умолчанию), Pydantic v2, JWT (pyjwt) в httpOnly cookie,
bcrypt для хэширования паролей, AI-слой с graceful fallback без Ollama.

## Установка и запуск (Windows, git bash)

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

На машине разработки Ollama НЕ установлена — это ожидаемо для хакатон-прототипа.
`services/ollama_client.chat()` пытается обратиться к `http://localhost:11434/api/chat`
с таймаутом 3 секунды и возвращает `None` при любой ошибке сети/таймаута (никогда не бросает
исключение наружу). Оба AI-роута (`/ai/chat`, `/ai/parent-command`) в этом случае автоматически
переключаются на rule-based fallback — задокументировано в коде и проверено тестами
(`tests/test_ai_command_parser.py`) и вручную (см. ниже).

Если захотите протестировать реальный LLM-путь — установите Ollama, выполните
`ollama pull qwen2.5:1.5b` (или другую модель, указанную в `.env` как `MODEL_NAME`) и запустите
`ollama serve`. Код специально не требует этого для работы.

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
