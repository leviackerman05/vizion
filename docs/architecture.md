# Architecture and trust boundaries

The browser uses a same-origin API. Accounts, session hashes, recovery-code hashes, storyboards, job leases, and quota reservations live in PostgreSQL. Passwords use Argon2. Opaque production cookies use `__Host-`, Secure, HttpOnly, SameSite=Lax, and a 30-day sliding expiry. Mutations require the custom app header and a matching Origin. Login/recovery attempts are rate limited in the database. Logout and recovery revoke server sessions.

The worker claims a queued project under a row lock and gives each attempt a unique fencing token. It renews a lease while working. Every progress/final update checks the token. Restarts recover expired leases; old or cancelled attempts cannot overwrite newer results. Projects are durable jobs, so API restarts cannot lose an in-memory task.

The planner requests strict JSON from Groq's `openai/gpt-oss-120b`. Pydantic validates narration budgets, supported scene types, bounded arithmetic, graph domains, and array indices. Each generation stage permits up to three validation attempts. A separate structured critic reviews facts and visual correspondence; rejected drafts get one repair and another review. Persistent errors are not published as completed storyboards. Clicking Render approves the saved storyboard revision. Concurrent edits during rendering are rejected.

Rendering measures offline speech per scene. Static Manim code reads validated JSON and holds visuals for the measured audio duration. FFmpeg joins narrated clips. Burned-in captions and WebVTT use measured scene durations with approximate phrase timing, not word-level forced alignment.

The model never writes executable Python. Expressions use a bounded AST interpreter without `eval`, imports, or attributes. Render subprocesses receive no model, storage, or database credentials. Per-attempt directories isolate intermediate files. Containers run as non-root.

Exports live in private S3-compatible storage. The API checks ownership before issuing a one-hour video URL. Captions are proxied through the authenticated API to avoid CORS problems. Signed URLs are temporary bearer links: anyone holding one can use it until expiry. New revisions replace the current export pointer; old objects remain pending retention support.

## Mobile path

The studio is responsive. Retain the lesson contract and HTTP API for future native clients, adding an explicit secure session/token flow and origin policy. Never expose provider credentials in clients. Arbitrary 3D/Remotion can become another trusted renderer against a versioned scene contract after the core flow is reliable.
