from conftest import register
from vizion.db import Project, transaction
from vizion.examples import example_storyboard
from vizion.settings import settings


def create(client, key="first-lesson"):
    response = client.post(
        "/api/projects",
        json={"topic": "Explain why a parabola curves", "example": True},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 202, response.text
    return response.json()


def make_draft(project_id):
    with transaction() as db:
        project = db.get(Project, project_id)
        project.storyboard = example_storyboard().model_dump()
        project.status = "draft"


def test_create_is_idempotent_and_projects_survive_reload(logged_in):
    first = create(logged_in)
    assert create(logged_in)["id"] == first["id"]
    assert len(logged_in.get("/api/projects").json()) == 1
    assert logged_in.get(f"/api/projects/{first['id']}").json()["topic"] == first["topic"]


def test_every_project_operation_is_scoped_to_its_owner(logged_in):
    project = create(logged_in)
    make_draft(project["id"])
    logged_in.post("/api/auth/logout")
    register(logged_in, "other@example.com")
    path = f"/api/projects/{project['id']}"
    assert logged_in.get(path).status_code == 404
    assert logged_in.get("/api/projects").json() == []
    assert logged_in.post(path + "/cancel").status_code == 404
    assert logged_in.post(path + "/retry").status_code == 404
    assert logged_in.post(path + "/render", json={"revision": 1}).status_code == 404
    assert (
        logged_in.put(
            path + "/storyboard", json={"revision": 1, "storyboard": example_storyboard().model_dump()}
        ).status_code
        == 404
    )
    assert logged_in.get(path + "/assets/video").status_code == 404


def test_storyboard_revision_prevents_overwriting_another_tab(logged_in):
    project = create(logged_in)
    make_draft(project["id"])
    path = f"/api/projects/{project['id']}/storyboard"
    body = {"revision": 1, "storyboard": example_storyboard().model_dump()}
    saved = logged_in.put(path, json=body)
    assert saved.status_code == 200 and saved.json()["revision"] == 2
    assert logged_in.put(path, json=body).status_code == 409


def test_render_is_idempotent_and_cancel_is_durable(logged_in):
    project = create(logged_in)
    make_draft(project["id"])
    path = f"/api/projects/{project['id']}"
    assert logged_in.post(path + "/render", json={"revision": 1}).status_code == 202
    assert logged_in.post(path + "/render", json={"revision": 1}).status_code == 202
    with transaction() as db:
        assert db.get(Project, project["id"]).render_count == 1
    assert logged_in.post(path + "/cancel").json()["status"] == "cancelled"
    assert logged_in.get(path).json()["status"] == "cancelled"
    assert logged_in.post(path + "/retry").json()["status"] == "queued"


def test_daily_allowance_is_enforced_before_queueing(logged_in, monkeypatch):
    monkeypatch.setattr(settings, "daily_project_limit", 1)
    create(logged_in)
    assert (
        logged_in.post(
            "/api/projects", json={"topic": "Another math lesson"}, headers={"Idempotency-Key": "second"}
        ).status_code
        == 429
    )
