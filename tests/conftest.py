import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from vizion import db
from vizion.settings import settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "s3_bucket", "")
    monkeypatch.setattr(settings, "embedded_worker", False)
    monkeypatch.setattr(settings, "daily_project_limit", 5)
    monkeypatch.setattr(settings, "daily_render_limit", 10)
    monkeypatch.setattr(settings, "global_daily_render_limit", 30)
    engine = db.make_engine(settings.database_url)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "Session", sessionmaker(engine, expire_on_commit=False))
    from vizion import api

    monkeypatch.setattr(api, "engine", engine)
    with TestClient(api.create_app(), headers={"X-Vizion-Client": "web"}) as instance:
        yield instance
    engine.dispose()


def register(client, email="teacher@example.com"):
    response = client.post("/api/auth/register", json={"email": email, "password": "a-long-test-password"})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def logged_in(client):
    register(client)
    return client
