"""A one-job-at-a-time worker with persisted leases and fencing on every update."""

import logging
import shutil
import signal
import threading
import time
import uuid

from sqlalchemy import select, update

from vizion.db import Project, initialize, transaction
from vizion.examples import example_storyboard
from vizion.media import Cancelled
from vizion.planner import PipelineError, plan_lesson
from vizion.render import render_lesson
from vizion.settings import settings
from vizion.storage import storage

log = logging.getLogger(__name__)
ACTIVE = {"planning", "narrating", "rendering", "assembling"}


def claim_job():
    now = time.time()
    with transaction() as db:
        expired = list(
            db.scalars(
                select(Project)
                .where(Project.status.in_(ACTIVE), Project.lease_until < now)
                .with_for_update(skip_locked=True)
            )
        )
        for project in expired:
            project.status = "failed" if project.attempts >= 3 else "queued"
            project.detail = (
                "The worker restarted. Recovering this job."
                if project.status == "queued"
                else "The worker could not recover this job. Retry it from the studio."
            )
            project.error = project.detail if project.status == "failed" else None
            project.lease_owner, project.lease_until = None, None
        db.flush()
        project = db.scalar(
            select(Project)
            .where(Project.status == "queued")
            .order_by(Project.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not project:
            return None
        token = str(uuid.uuid4())
        changed = db.execute(
            update(Project)
            .where(Project.id == project.id, Project.status == "queued")
            .values(
                status="planning" if project.operation == "plan" else "narrating",
                lease_owner=token,
                lease_until=now + settings.lease_seconds,
                attempts=Project.attempts + 1,
                updated_at=now,
            )
        )
        if changed.rowcount != 1:
            return None
        db.refresh(project)
        db.expunge(project)
        return project


def update_job(project, **values):
    with transaction() as db:
        changed = db.execute(
            update(Project)
            .where(
                Project.id == project.id,
                Project.lease_owner == project.lease_owner,
                Project.status.in_(ACTIVE),
            )
            .values(**values, updated_at=time.time(), lease_until=time.time() + settings.lease_seconds)
        )
        return changed.rowcount == 1


def process_job(project: Project, stop=None):
    interrupted = threading.Event()
    finished = threading.Event()
    work_dir = settings.data_dir / "jobs" / project.id / project.lease_owner

    def heartbeat():
        while not finished.wait(min(15, settings.lease_seconds / 3)):
            if stop and stop.is_set():
                interrupted.set()
                return
            try:
                if not update_job(project):
                    interrupted.set()
                    return
            except Exception:
                log.exception("Job heartbeat failed for %s", project.id)
                interrupted.set()
                return

    def cancelled():
        return interrupted.is_set() or bool(stop and stop.is_set())

    def notify(progress, detail, status=None):
        if cancelled():
            raise Cancelled()
        values = {"progress": progress, "detail": detail}
        if status:
            values["status"] = status
        if not update_job(project, **values):
            interrupted.set()
            raise Cancelled()

    pulse = threading.Thread(target=heartbeat, daemon=True)
    pulse.start()
    try:
        if project.operation == "plan":
            if project.example:
                plan, provider = example_storyboard(), "built-in example (no model API)"
            else:
                plan, provider = plan_lesson(project.topic, project.audience, notify)
            notify(95, "Checking narration length, scene types, and graph expressions")
            update_job(
                project,
                storyboard=plan.model_dump(),
                title=plan.title,
                provider=provider,
                status="draft",
                progress=100,
                detail="Your storyboard is ready. Review it, then render.",
                error=None,
                lease_owner=None,
            )
        else:
            from vizion.schema import Storyboard

            plan = Storyboard.model_validate(project.storyboard)
            video, captions, duration = render_lesson(plan, work_dir, notify, cancelled)
            notify(98, "Saving the video and captions to private storage", "assembling")
            key_root = f"{project.user_id}/{project.id}/r{project.revision}-{project.lease_owner}"
            storage.upload(video, f"{key_root}/lesson.mp4", "video/mp4")
            storage.upload(captions, f"{key_root}/captions.vtt", "text/vtt")
            if cancelled():
                raise Cancelled()
            update_job(
                project,
                status="completed",
                progress=100,
                detail="Your narrated lesson is ready.",
                video_key=f"{key_root}/lesson.mp4",
                captions_key=f"{key_root}/captions.vtt",
                duration=duration,
                rendered_revision=project.revision,
                error=None,
                lease_owner=None,
            )
    except Cancelled:
        log.info("Job %s stopped or lost its lease", project.id)
        # A graceful worker shutdown leaves a recoverable lease. Explicit cancellation already fences us out.
        if stop and stop.is_set():
            update_job(
                project,
                status="queued",
                detail="Worker restarting. Your job is safely queued.",
                lease_owner=None,
            )
    except Exception as exc:
        log.exception("Job %s failed", project.id)
        message = (
            str(exc)
            if isinstance(exc, PipelineError)
            else "This lesson could not be completed. Your saved work is available; retry or revise its storyboard."
        )
        update_job(project, status="failed", error=message, detail=message, lease_owner=None)
    finally:
        finished.set()
        pulse.join(timeout=2)
        # Each attempt owns exactly this directory. Other jobs and completed assets remain untouched.
        if work_dir.exists():
            root = (settings.data_dir / "jobs").resolve()
            resolved = work_dir.resolve()
            if root in resolved.parents:
                shutil.rmtree(resolved, ignore_errors=True)


def run_worker(stop=None):
    stop = stop or threading.Event()
    settings.validate_runtime()
    initialize()
    log.info("Vizion worker ready; one render at a time")
    while not stop.is_set():
        try:
            project = claim_job()
            if project:
                process_job(project, stop)
                continue
        except Exception:
            log.exception("Worker polling failed; reconnecting shortly")
        stop.wait(settings.poll_seconds)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    run_worker(stop)


if __name__ == "__main__":
    main()
