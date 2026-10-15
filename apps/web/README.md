# Vizion web studio

React / TypeScript frontend, built and deployed from the monorepo root. Run `npm ci` and `npm run dev` there. Vite proxies `/api` to port 8000; production serves the bundle and API from one origin.

No auth token or provider/storage credential belongs in frontend variables. Authentication uses an HttpOnly session cookie. See the root README and DEPLOY.md.
