# Single container: Next.js (public $PORT) + FastAPI on 127.0.0.1:8000 (server-side proxy).
# Build from repository root: docker build -t vc-analyst .

FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN mkdir -p public
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_DEMO_MODE=false
ENV NEXT_PUBLIC_DEMO_MODE=${NEXT_PUBLIC_DEMO_MODE}
ARG NEXT_PUBLIC_API_URL=
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

FROM node:20-bookworm-slim AS runner
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-venv \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /venv \
  && /venv/bin/pip install --no-cache-dir --upgrade pip

WORKDIR /work/backend
COPY backend/requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app

WORKDIR /work/web
COPY --from=frontend-builder /frontend/public ./public
COPY --from=frontend-builder /frontend/.next/standalone ./
COPY --from=frontend-builder /frontend/.next/static ./.next/static

COPY docker/entrypoint.sh /work/entrypoint.sh
RUN chmod +x /work/entrypoint.sh

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
# Server-side /api proxy target (see frontend/src/lib/backend-origin.ts). Do not remove:
# overrides mistaken BACKEND_URL=https://your-app.ondigitalocean.app in App Platform UI.
ENV INTERNAL_FASTAPI_URL=http://127.0.0.1:8000
ENV BACKEND_URL=http://127.0.0.1:8000
ENV PYTHONUNBUFFERED=1

EXPOSE 3000
WORKDIR /work
ENTRYPOINT ["/work/entrypoint.sh"]
