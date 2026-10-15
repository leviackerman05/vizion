# MVP verification — 15 October 2026

The canonical monorepo is `vizion`, with frontend code in `apps/web` and Python services in `services/video`. Both original Git histories are preserved. PR: https://github.com/leviackerman05/vizion/pull/8

## Automated checks

- 35 pytest cases pass: sessions, logout/recovery, secure cookies, CSRF/origin checks, rate limits, ownership, idempotency, quotas, optimistic revisions, cancellation, lease fencing/recovery, expression bounds, graph domains, measured caption timing, provider errors, independent review, repair, and failure handling.
- Ruff, TypeScript/Vite production build, and ESLint pass.
- GitHub Actions runs the same checks on Linux / Python 3.12 / Node 24.

## Actual media and account checks

- A real Groq topic request produced a binary-search lesson, including the numeric array and midpoint indices 3, 5, and 4.
- In the deployed browser, edited and saved the first scene, rendered revision 2, reloaded, signed out/in, and retained the same project.
- Railway produced and privately stored a four-scene export: H.264 video, AAC narration, 1280×720, nominal 24 fps, 40.79 seconds container duration (40.74 seconds measured narration).
- Authenticated MP4 download and WebVTT retrieval succeeded. Browser metadata loaded without errors and playback advanced normally.
- Video frames from all four scenes were inspected. Audio is present; measured mean volume -17.7 dBFS and peak -0.4 dBFS.
- A different account received 404 for project details, video, captions, and cancellation, and an empty project list.
- The project and export survived web/worker redeploys. Phone layout bounds were checked at 390×844 with no horizontal overflow and working project navigation.
- Worker memory observed during rendering peaked at approximately 403 MiB, within the configured 2 GB ceiling. This is a smoke measurement, not a load test or monthly cost guarantee.

## Prompt regression

A physics smoke check found an incorrect claim that a frictionless table cancels a horizontal push, and a later draft confused zero net force with no forces. The new independent critic returned concrete rejection reasons. The repair then correctly retained gravity and normal force, described acceleration during the push, and constant velocity after release; a separate verdict approved it. Real provider throttling and bounded retry behavior were also exercised.

Generated educational material still needs human review. These checks establish a working MVP flow and specific regressions, not universal factual correctness or production-scale capacity. Arbitrary 3D, verified email, billing, retention/deletion, backups, and explicit future database migrations remain follow-up work.

Screenshots, test credentials, temporary setup files, and generated media remain in ignored local `data/`, not Git. Provider/storage keys remain in local `.env` and Railway secret variables.
