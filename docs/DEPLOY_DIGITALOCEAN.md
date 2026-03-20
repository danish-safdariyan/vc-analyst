# Deploy on DigitalOcean App Platform

This project is wired for **[App Platform](https://www.digitalocean.com/products/app-platform)** using the Dockerfiles in `backend/` and `frontend/`.

## What we optimized for DO

1. **Same-origin API in the browser** — The Next app calls `/api/...`; `next.config.mjs` rewrites those requests to your FastAPI service. You usually **do not** need browser CORS, but you can set `CORS_ORIGINS` on the API if you use `NEXT_PUBLIC_API_DIRECT=true`.
2. **`PORT` on the API** — The backend container respects `$PORT` (App Platform sets it). Default is `8000` locally.
3. **`NEXT_PUBLIC_API_URL` at build time** — Required so Next rewrites know where to proxy. The sample spec uses `${api.PUBLIC_URL}`.

## One-time setup

1. Push the repo to GitHub and connect it in DigitalOcean.
2. Open **App Platform → Create App → GitHub**.
3. Choose **Edit app spec** and paste from [`.do/app.yaml`](../.do/app.yaml), then:
   - Replace `YOUR_GITHUB_ORG/YOUR_REPO`.
   - Under **api → envs**: set `OPENROUTER_API_KEY` (type **SECRET**) in the UI; remove the placeholder `REPLACE_ME_IN_DASHBOARD` value from YAML if the UI complains.
4. Deploy.

### If `${api.PUBLIC_URL}` does not resolve on first build

Set **`NEXT_PUBLIC_API_URL`** on the **web** service manually to your API’s URL (e.g. `https://api-xxxxx.ondigitalocean.app`), then **Redeploy** the web component.

### CORS (optional)

If you turn on **`NEXT_PUBLIC_API_DIRECT=true`** on the frontend, the browser will call the API host directly. Then set **`CORS_ORIGINS`** on the API to your frontend URL, e.g. `https://web-xxxxx.ondigitalocean.app` (comma-separated if several).

## Health check

The API exposes **`GET /health`**. The sample app spec uses it as the health check path.

## Droplet alternative

On a single Droplet you can run **Docker Compose** from the repo root:

```bash
# API only — set backend/.env with production secrets
docker compose up -d --build api
```

Then build and run the frontend image with:

```bash
docker build -t vc-web --build-arg NEXT_PUBLIC_API_URL=https://YOUR_API_HOST ./frontend
docker run -p 3000:3000 vc-web
```

Put the API and web behind Nginx or Caddy with TLS, or use the App Platform instead for HTTPS and scaling.

## Costs

Use **`basic-xxs`** instances in the spec for the smallest bill; adjust `instance_size_slug` when you need more CPU/RAM.
