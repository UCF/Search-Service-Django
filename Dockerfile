# syntax=docker/dockerfile:1

# Python 3.8 matches production until the upgrade after cutover. The
# official 3.8 images no longer receive updates, so both stages upgrade
# their OS packages.
ARG PYTHON_IMAGE=python:3.8-slim-bookworm


# Build stage: compiles the Python dependencies. mysqlclient needs a
# compiler and the MySQL client headers, which the final image doesn't.
FROM ${PYTHON_IMAGE} AS build

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends gcc pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project --extra postgres


# Final stage
FROM ${PYTHON_IMAGE}

# libmariadb3 is the MySQL client library mysqlclient links against;
# xmlsec1 checks SAML signatures.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libmariadb3 xmlsec1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --no-create-home app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=build /opt/venv /opt/venv

WORKDIR /app
COPY . .

# Settings come from the template plus environment variables. The
# front-end assets in static/ are compiled and committed with gulp, so
# collectstatic only adds the admin and Django REST framework files.
RUN cp settings_local.tmpl.py settings_local.py \
    && cat docker/env-settings.py >> settings_local.py \
    && SECRET_KEY=collectstatic DB_ENGINE=django.db.backends.sqlite3 DB_NAME=:memory: \
        python manage.py collectstatic --noinput

USER app

EXPOSE 8000

CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
