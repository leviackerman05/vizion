import time
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import Field
from sqlalchemy import func, select, text, update

from vizion.auth import current_user
from vizion.db import Project, RenderReservation, User, transaction
from vizion.schema import ProjectCreate, Storyboard, StrictModel
from vizion.settings import settings
from vizion.storage import storage

router = APIRouter(prefix="/api/projects", tags=["Projects"])
BUSY = {"queued", "planning", "narrating", "rendering", "assembling"}


def view(project: Project, full=True):
    result = {
        name: getattr(project, name)
        for name in (
            "id",
            "topic",
            "audience",
            "title",
            "status",
            "operation",
            "revision",
            "rendered_revision",
            "progress",
            "detail",
            "error",
            "duration",
            "provider",
            "created_at",
            "updated_at",
        )
    }
    result["has_video"] = bool(project.video_key)
    result["example"] = bool(project.example)
    if full:
        result["storyboard"] = project.storyboard
    return result


def owned(db, project_id, user_id, lock=False):
    query = select(Project).where(Project.id == project_id, Project.user_id == user_id)
    if lock:
        query = query.with_for_update()
    project = db.scalar(query)
    if project is None:
        raise HTTPException(404, "Project not found")
    return project


def quota_lock(db, user_id):
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(731623)"))
    else:
        db.execute(update(User).where(User.id == user_id).values(email=User.email))


def queue_capacity(db):
    pending = db.scalar(select(func.count()).select_from(Project).where(Project.status.in_(BUSY)))
    if pending >= settings.max_pending_jobs:
        raise HTTPException(429, "The render queue is full. Try again when a lesson finishes.")


def reserve_render(db, user_id):
    cutoff = time.time() - 86400
    personal = db.scalar(
        select(func.count())
        .select_from(RenderReservation)
        .where(RenderReservation.user_id == user_id, RenderReservation.created_at >= cutoff)
    )
    global_count = db.scalar(
        select(func.count()).select_from(RenderReservation).where(RenderReservation.created_at >= cutoff)
    )
    if personal >= settings.daily_render_limit or global_count >= settings.global_daily_render_limit:
        raise HTTPException(
            429, "The daily video allowance is used up. Your storyboard is saved; render it tomorrow."
        )
    db.add(RenderReservation(user_id=user_id))


@router.get("")
def list_projects(user: User = Depends(current_user)):
    with transaction() as db:
        return [
            view(p, False)
            for p in db.scalars(
                select(Project)
                .where(Project.user_id == user.id)
                .order_by(Project.created_at.desc())
                .limit(50)
            )
        ]


@router.post("", status_code=202)
def create_project(
    body: ProjectCreate,
    user: User = Depends(current_user),
    idempotency_key: str = Header(default="", max_length=80),
):
    key = idempotency_key or str(uuid.uuid4())
    with transaction() as db:
        quota_lock(db, user.id)
        existing = db.scalar(
            select(Project).where(Project.user_id == user.id, Project.idempotency_key == key)
        )
        if existing:
            return view(existing)
        count = db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.user_id == user.id, Project.created_at >= time.time() - 86400)
        )
        if count >= settings.daily_project_limit:
            raise HTTPException(
                429, "Your daily lesson allowance is used up. Existing lessons are still available."
            )
        queue_capacity(db)
        if body.example and not settings.allow_example_projects:
            raise HTTPException(400, "Example projects are disabled")
        project = Project(
            user_id=user.id,
            topic=body.topic.strip(),
            audience=body.audience,
            title=body.topic.strip()[:70],
            example=int(body.example),
            idempotency_key=key,
        )
        db.add(project)
        db.flush()
        return view(project)


@router.get("/{project_id}")
def get_project(project_id: str, user: User = Depends(current_user)):
    with transaction() as db:
        return view(owned(db, project_id, user.id))


class StoryboardUpdate(StrictModel):
    storyboard: Storyboard
    revision: int = Field(ge=1)


@router.put("/{project_id}/storyboard")
def save_storyboard(project_id: str, body: StoryboardUpdate, user: User = Depends(current_user)):
    with transaction() as db:
        project = owned(db, project_id, user.id, True)
        if project.status in BUSY:
            raise HTTPException(409, "Wait for the current job to finish before editing")
        if project.revision != body.revision:
            raise HTTPException(409, "This lesson changed in another tab. Reload before saving.")
        project.storyboard = body.storyboard.model_dump()
        project.title = body.storyboard.title
        project.revision += 1
        project.status, project.error = "draft", None
        project.detail, project.progress = "Storyboard saved. Ready to render.", 100
        project.updated_at = time.time()
        return view(project)


class RenderRequest(StrictModel):
    revision: int = Field(ge=1)


@router.post("/{project_id}/render", status_code=202)
def render_project(project_id: str, body: RenderRequest, user: User = Depends(current_user)):
    with transaction() as db:
        quota_lock(db, user.id)
        project = owned(db, project_id, user.id, True)
        if body.revision != project.revision:
            raise HTTPException(409, "Your storyboard has changed. Reload before rendering.")
        if project.status in BUSY and project.operation == "render":
            return view(project)
        if project.status == "completed" and project.rendered_revision == project.revision:
            return view(project)
        if not project.storyboard or project.status in BUSY:
            raise HTTPException(409, "A finished storyboard is required before rendering")
        Storyboard.model_validate(project.storyboard)
        queue_capacity(db)
        reserve_render(db, user.id)
        project.operation, project.status = "render", "queued"
        project.progress, project.detail = 0, "Waiting for the narration and render worker"
        project.error, project.lease_owner, project.lease_until = None, None, None
        project.attempts, project.retry_count = 0, 0
        project.render_count += 1
        project.updated_at = time.time()
        return view(project)


@router.post("/{project_id}/retry", status_code=202)
def retry_project(project_id: str, user: User = Depends(current_user)):
    with transaction() as db:
        quota_lock(db, user.id)
        project = owned(db, project_id, user.id, True)
        if project.status == "queued":
            return view(project)
        if project.status not in {"failed", "cancelled"}:
            raise HTTPException(409, "Only a failed or cancelled job can be retried")
        if project.retry_count >= 3:
            raise HTTPException(429, "This job reached its retry allowance. Create a narrower lesson.")
        queue_capacity(db)
        if project.operation == "render":
            reserve_render(db, user.id)
        project.status, project.error = "queued", None
        project.progress, project.detail = 0, "Queued for another attempt"
        project.attempts, project.lease_owner, project.lease_until = 0, None, None
        project.retry_count += 1
        project.updated_at = time.time()
        return view(project)


@router.post("/{project_id}/cancel")
def cancel_project(project_id: str, user: User = Depends(current_user)):
    with transaction() as db:
        project = owned(db, project_id, user.id, True)
        if project.status in BUSY:
            project.status, project.detail = "cancelled", "Job cancelled. Your saved storyboard is available."
            project.lease_owner, project.lease_until = None, None
            project.updated_at = time.time()
        return view(project)


@router.get("/{project_id}/assets/{asset}")
def project_asset(
    project_id: str,
    asset: Literal["video", "captions"],
    download: bool = False,
    user: User = Depends(current_user),
):
    with transaction() as db:
        project = owned(db, project_id, user.id)
        key = project.video_key if asset == "video" else project.captions_key
        if not key:
            raise HTTPException(404, "This asset is not ready yet")
    media_type = "video/mp4" if asset == "video" else "text/vtt"
    filename = f"vizion-{project_id[:8]}.{'mp4' if asset == 'video' else 'vtt'}"
    if storage.remote:
        if asset == "captions":
            body = storage.client().get_object(Bucket=settings.s3_bucket, Key=key)["Body"]
            try:
                content = body.read(512_000)
            finally:
                body.close()
            return Response(
                content,
                media_type="text/vtt",
                headers={
                    "Cache-Control": "private, no-store",
                    **({"Content-Disposition": f'attachment; filename="{filename}"'} if download else {}),
                },
            )
        url = storage.signed_url(key, filename if download else None, media_type)
        return RedirectResponse(url, status_code=307, headers={"Cache-Control": "private, no-store"})
    return FileResponse(
        storage.local_path(key),
        media_type=media_type,
        filename=filename if download else None,
        headers={"Cache-Control": "private, no-store"},
    )
