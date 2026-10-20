"""SQLAlchemy engine/session + declarative Base."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DB_URL.startswith("sqlite") else {}
engine = create_engine(settings.DB_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Колонки, добавленные к уже существующим таблицам после первого релиза.
# Alembic в прототипе нет, поэтому схему дополняем вручную при старте.
ADDED_COLUMNS: list[tuple[str, str, str]] = [
    # (таблица, колонка, SQL-тип)
    ("loyalty_accounts", "converted_byn", "FLOAT DEFAULT 0.0"),
    ("cards", "balance", "FLOAT DEFAULT 0.0"),
]


def migrate_schema() -> None:
    """Добавляет недостающие колонки в существующие таблицы.

    `Base.metadata.create_all` создаёт отсутствующие таблицы, но не добавляет
    новые колонки в уже созданные — без этого шага приложение, запущенное на
    базе из прошлой версии, падало бы с «no such column».
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, column, sql_type in ADDED_COLUMNS:
            if table not in existing_tables:
                continue
            columns = {c["name"] for c in inspector.get_columns(table)}
            if column in columns:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
