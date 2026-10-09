FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID=1000
RUN useradd --uid "${APP_UID}" --create-home --shell /usr/sbin/nologin msds \
    && mkdir -p /app /data/sds /data/bhp_evidence \
    && chown -R msds:msds /app /data

WORKDIR /app

# Zależności osobno: ta warstwa przebudowuje się tylko po zmianie pyproject.toml.
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py \
    && pip install . \
    && pip uninstall -y msds-manager \
    && rm -rf app build *.egg-info

# Kod należy do użytkownika aplikacji, żeby `docker compose watch` mógł go podmieniać.
COPY --chown=msds:msds app ./app
COPY --chown=msds:msds alembic.ini ./
COPY --chown=msds:msds migrations ./migrations
COPY --chown=msds:msds scripts ./scripts
RUN pip install --no-deps -e . && rm -rf build

USER msds

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["sh", "-c", "python -m alembic upgrade head && exec python -m streamlit run app/presentation/streamlit/main.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true --browser.gatherUsageStats=false"]
