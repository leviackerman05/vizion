# Vizion

A topic becomes a storyboard checked by an independent model review, then a narrated Manim video after user approval. The MVP focuses on one short teaching objective at a time, with an editor, persistent jobs, private exports, and reliable account sessions.

## Repository

- `apps/web`: responsive React / TypeScript studio.
- `services/video/vizion`: FastAPI, PostgreSQL auth and job queue, lesson planner, trusted Manim renderer, offline narration, and private storage.
- `tests`: auth, ownership, quotas, storyboard validation, cancellation, and worker recovery.
- `legacy`: archived implementations for reference. Legacy Firebase, Supabase, Stripe, and generated-code paths do not run in the new app.

The `feat/vizion-mvp` branch imports the original `vizion-ui` repository under `apps/web`, preserving its Git history. The backend history also remains intact. Keep future development here; the separate UI repository is no longer needed for deployment.

## Run locally

Use Python 3.12 and Node 22.12 or newer. On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[render,dev]'
npm ci
Copy-Item .env.example .env
```

Set the Groq key in `.env` for topic generation. The explicitly selected parabola example works without a model key. Windows uses its installed English voice. Linux uses Piper with a downloaded voice, or `espeak-ng` for development. Linux Manim needs Cairo, Pango, FFmpeg, and a C/C++ compiler; the Dockerfile provides them.

Run API and worker in separate terminals, then the web development server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn vizion.api:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m vizion.worker
npm run dev
```

Open `http://localhost:8080`. For a single-process local demo, set `EMBEDDED_WORKER=true` on the API instead of starting a separate worker. Production uses separate services. `npm run build` creates the bundle FastAPI serves from the same origin.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check services tests
npm run check
```

Unit tests do not spend model quota or render full videos. End-to-end acceptance additionally requires a real provider request, narrated Manim render, private upload, and browser playback. See [deployment](DEPLOY.md), [architecture](docs/architecture.md), and [prompt design](docs/prompt-design.md).

## Scope

English, landscape 720p / 24fps, approximately 30-90 second lessons, six constrained visual types: function curves, number arrays, concept relationships, steps, comparisons, and a Pythagorean diagram. Arbitrary 3D scenes and documentary footage are future work. The renderer executes checked-in Python only; the model supplies validated data.

Signup displays a recovery code once. Save it: this MVP uses recovery codes instead of paid email delivery and does not verify email ownership. Keep usage small until adding verified email, stronger abuse controls, project deletion / retention, billing, and production migrations. Daily limits constrain render usage but do not guarantee Railway stays within a fixed monthly credit amount.
