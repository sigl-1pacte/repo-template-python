# Pre-built generic Python base image — swap for an internal mirror if needed.
FROM python:3.12-slim

# Inject uv from its official distroless image; no extra packages required.
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

# Install deps before copying source so this layer is cached across code changes.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

COPY app/ ./app/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
