# Railway deployment

Use one dedicated Vizion project with `web`, `worker`, managed `Postgres`, and a private `vizion-videos` bucket. Both app services build the root Dockerfile. Web serves the frontend and API on one origin; worker claims PostgreSQL jobs and renders one lesson at a time. Database records and bucket exports survive redeploys. Temporary render files need no volume.

## Variables

Both services need:

```dotenv
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
PUBLIC_URL=https://YOUR-WEB-DOMAIN
S3_ENDPOINT_URL=YOUR-RAILWAY-BUCKET-ENDPOINT
S3_ACCESS_KEY_ID=YOUR-BUCKET-ACCESS-KEY
S3_SECRET_ACCESS_KEY=YOUR-BUCKET-SECRET
S3_BUCKET=YOUR-BUCKET-NAME
S3_REGION=YOUR-BUCKET-REGION
S3_ADDRESSING_STYLE=virtual
DAILY_PROJECT_LIMIT=5
DAILY_RENDER_LIMIT=3
GLOBAL_DAILY_RENDER_LIMIT=10
```

Set `APP_ROLE=web` on web. Set `APP_ROLE=worker`, `LLM_PROVIDER=groq`, `GROQ_API_KEY`, and `TTS_PROVIDER=piper` on worker. Keep the model key out of web and frontend build variables. The image downloads an offline English Piper voice during build, so narration uses no paid TTS API.

Startup rejects production SQLite, HTTP public URLs, missing private storage credentials, and workers missing a provider key or configured voice. Schema initialization takes a PostgreSQL advisory lock so simultaneous service starts are safe.

## Deploy

Link the root repository to the intended Railway project/environment:

```powershell
railway up --service web --detach
railway up --service worker --detach
```

Use one region/replica on the existing plan. Keep sleeping disabled for this dedicated project. `railway.toml` uses `/api/health`; the worker also exposes it. Initial resource caps: web 0.5 GB / 1 CPU, worker 2 GB / 2 CPUs. These are ceilings, not reservations or spending caps. Renders, PostgreSQL, storage, and always-on memory consume the Railway allowance.

Use Railway variable references and secret inputs. Keep credentials out of command arguments, screenshots, Git, and chat. Set `PUBLIC_URL` to the final HTTPS domain on both services; it controls cookie and origin checks.

## Acceptance and operations

1. Confirm both deploys and `/api/health` return successfully.
2. Register, save the recovery code, refresh, sign out, and sign back in.
3. Create a narrow original topic; review, edit, and save a scene.
4. Render and refresh while it works. Play/download the MP4 and confirm captions.
5. Redeploy, sign back in, and confirm the same project/export survives.
6. Confirm another account cannot read, edit, cancel, or download it.

Expired worker leases recover automatically, with at most three attempts. Cancellation fences old workers from overwriting state. Provider throttling has bounded retries and clear errors. An unrelated sample never silently replaces a failed topic, and there is no paid fallback. Rolling project/render reservations limit repeated usage.

Monitor Railway memory, CPU, storage, and account usage during real rendering. Groq free quotas are shared across its organization and can change. Enable suitable database backups before storing valuable work. `create_all` bootstraps this first schema; introduce explicit migrations before changing it. This MVP retains exports; add owner deletion and lifecycle retention before broader public launch.
