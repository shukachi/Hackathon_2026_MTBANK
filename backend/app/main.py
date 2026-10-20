from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.routers import access_requests, ai, auth, cards, family, goals, limits, loyalty, quests, transactions

# Импорт app.models регистрирует все таблицы в Base.metadata перед create_all.
import app.models  # noqa: F401,E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
app.include_router(access_requests.router)
app.include_router(ai.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
