import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from vizion.auth import router as auth_router
from vizion.db import engine, initialize
from vizion.projects import router as projects_router
from vizion.settings import settings


@asynccontextmanager
async def lifespan(app):
    settings.validate_runtime()
    initialize()
    stop = threading.Event()
    worker = None
    if settings.embedded_worker:
        from vizion.worker import run_worker

        worker = threading.Thread(target=run_worker, args=(stop,), daemon=True)
        worker.start()
    yield
    stop.set()
    if worker:
        worker.join(timeout=5)


def create_app():
    app = FastAPI(title="Vizion", version="0.2.0", lifespan=lifespan)
    app.include_router(auth_router)
    app.include_router(projects_router)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "private, no-store"
        if settings.production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.get("/api/health")
    def health():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception:
            logging.exception("Database health check failed")
            return JSONResponse({"status": "unavailable"}, status_code=503)

    @app.get("/api/config")
    def config():
        return {
            "example_available": settings.allow_example_projects,
            "daily_project_limit": settings.daily_project_limit,
            "narration": "Local neural voice",
            "version": "0.2.0",
        }

    if (settings.web_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=settings.web_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Endpoint not found")
        root = settings.web_dist.resolve()
        file = (root / path).resolve()
        if file.is_file() and root in file.parents:
            return FileResponse(file)
        index = root / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse({"message": "Vizion API is ready. Run npm run dev for the website."})

    return app


app = create_app()
