FROM ghcr.io/astral-sh/uv:0.9.30 AS uv

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

COPY --from=uv /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID=1000
RUN useradd --uid "${APP_UID}" --create-home --shell /usr/sbin/nologin msds \
    && mkdir -p /app /data/sds /data/bhp_evidence \
    && chown -R msds:msds /app /data

WORKDIR /app

# Zależności osobno z uv.lock: ta warstwa przebudowuje się tylko po zmianie
# pyproject.toml lub uv.lock. --frozen przerywa build, gdy lock jest nieaktualny.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Kod należy do użytkownika aplikacji, żeby `docker compose watch` mógł go podmieniać.
COPY --chown=msds:msds app ./app
COPY --chown=msds:msds alembic.ini ./
COPY --chown=msds:msds migrations ./migrations
COPY --chown=msds:msds scripts ./scripts
# Projekt instalowany jako editable, więc kod zsynchronizowany przez watch jest używany.
RUN uv sync --frozen --no-dev && rm -rf build *.egg-info

EXPOSE 8501


# Obraz do testów: zależności produkcyjne + grupa dev (pytest).
FROM base AS test
RUN uv sync --frozen --group dev
USER msds


# Obraz aplikacji: bez narzędzi deweloperskich. Domyślny target (ostatni etap).
FROM base AS runtime
USER msds

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m streamlit run app/presentation/streamlit/main.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false"]
