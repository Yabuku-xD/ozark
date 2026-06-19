# syntax=docker/dockerfile:1
#
# Multi-stage build for Ozark: builds the React frontend, then layers it
# onto a slim Python runtime that serves the API + static assets.

# ---- Frontend build ----
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Backend runtime ----
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install Python deps first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + CLI.
COPY backend/ ./backend/
COPY ozark.py ./

# Copy the built frontend so the server can serve static assets.
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Persist the SQLite database here.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

ENV PORT=8787
EXPOSE 8787

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/health', timeout=2); sys.exit(0)" || exit 1

CMD ["python", "-m", "backend.server"]
