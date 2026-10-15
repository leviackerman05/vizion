import time
import uuid
from contextlib import contextmanager

from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from vizion.settings import settings


def identifier():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    recovery_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[float] = mapped_column(Float, index=True)


class AuthAttempt(Base):
    __tablename__ = "auth_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    bucket: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        Index("ix_project_queue", "status", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(80))
    topic: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(20), default="beginner")
    title: Mapped[str] = mapped_column(String(100), default="Untitled lesson")
    status: Mapped[str] = mapped_column(String(20), default="queued")
    operation: Mapped[str] = mapped_column(String(20), default="plan")
    example: Mapped[int] = mapped_column(Integer, default=0)
    storyboard: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    rendered_revision: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(Text, default="Waiting for the lesson planner")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    captions_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)
    lease_until: Mapped[float | None] = mapped_column(Float, nullable=True)
    lease_owner: Mapped[str | None] = mapped_column(String(36), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    render_count: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class RenderReservation(Base):
    __tablename__ = "render_reservations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=identifier)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)


def make_engine(url: str):
    options = (
        {"connect_args": {"check_same_thread": False, "timeout": 30}}
        if url.startswith("sqlite")
        else {"pool_pre_ping": True}
    )
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_setup(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return engine


settings.data_dir.mkdir(parents=True, exist_ok=True)
engine = make_engine(settings.sql_url)
Session = sessionmaker(engine, expire_on_commit=False)


def initialize():
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(731622)"))
        Base.metadata.create_all(connection)


@contextmanager
def transaction():
    with Session.begin() as session:
        yield session
