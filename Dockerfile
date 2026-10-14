FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS base
WORKDIR /app

# Enable bytecode compilation to make initialization of the container fast
# Set link mode to copy to grant security and portability
ENV UV_COMPILE_BYTECODE=1\
    UV_LINK_MODE=copy

COPY . /app

FROM base AS development
RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]


FROM base AS builder
RUN uv sync --frozen --no-dev --no-install-project
COPY . /app
RUN uv sync --frozen --no-dev

# Production stage, dont uses the image with UV, use a clean python image
FROM python:3.14-slim-trixie AS production
WORKDIR /app
# Copy from the builder only the dependencies in venv and the files in app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Runs with uvicorn which is properly and optimized to deploys/prod
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
