from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine, migrate_schema
from app.routers import access_requests, ai, auth, cards, family, goals, limits, loyalty, qr_payment, quests, transactions
from app.services import ollama_client

# Импорт app.models регистрирует все таблицы в Base.metadata перед create_all.
import app.models  # noqa: F401,E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_schema()
    yield


app = FastAPI(title="Moby Family API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(family.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(limits.router)
app.include_router(goals.router)
app.include_router(quests.router)
app.include_router(loyalty.router)
app.include_router(qr_payment.router)
app.include_router(access_requests.router)
app.include_router(ai.router)


@app.get("/health")
def health() -> dict:
    """Базовый статус + проверка готовности локального AI-слоя (Ollama).

    `ollama.available` — отвечает ли сервис; `ollama.model_present` — скачана ли
    модель из MODEL_NAME. Значения `false` не ломают backend: AI-роуты в этом
    случае уходят в rule-based fallback.
    """
    ollama = ollama_client.status()
    return {
        "status": "ok",
        "ai_ready": bool(ollama["available"] and ollama["model_present"]),
        "ollama": ollama,
    }
