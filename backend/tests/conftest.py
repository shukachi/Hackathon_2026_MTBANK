import os

os.environ["DB_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET"] = "test-secret-at-least-32-bytes-long-for-hmac"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "test.db")

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    """Прямой доступ к тестовой сессии БД — для сервисных тестов."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
