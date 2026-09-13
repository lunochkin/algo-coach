# The engine's image: the API, the pages' built files, the migrations, and the
# compose file the server deploys with. `docs/architecture/README.md` gives why
# the image carries that compose file.

FROM node:24-slim AS pages
WORKDIR /web
# the manifests alone first, so a page edit reuses the installed layer
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.14-slim AS engine
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY README.md ./
COPY src src
# --no-editable: the package is copied into the environment, so the final stage
# carries no source tree
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.14-slim
# a submission runs in the container the broker starts rather than in this one,
# and the process answering requests still owns nothing it does not need
RUN useradd --create-home --uid 10001 engine
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH ALGO_COACH_PAGES=/app/web/dist
COPY --from=engine /app/.venv .venv
COPY alembic.ini ./
COPY migrations migrations
COPY deploy deploy
COPY --from=pages /web/dist web/dist
USER engine
EXPOSE 8000
# 0.0.0.0 inside the container, which `deploy/compose.yaml` publishes on the
# server's loopback address alone
CMD ["uvicorn", "--factory", "algo_coach.api.__main__:app", "--host", "0.0.0.0", "--port", "8000"]
