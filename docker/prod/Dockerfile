FROM python:3.12-slim as python-base

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION="1.7.1" \
    POETRY_HOME="/opt/poetry" \
    POETRY_VENV="/opt/poetry-venv" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR="/opt/.cache" \
    PROJECT_PATH="/shadowmere" \
    PROJECT_USER="shadowmere" \
    VENV_PATH="/shadowmere/.venv"

ENV PATH="${POETRY_HOME}/bin:${VENV_PATH}/bin:${PATH}"

FROM python-base as poetry-base

RUN python -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install --no-cache-dir -U pip setuptools wheel \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

FROM python-base as example-app

COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

ENV PYTHONPATH="${PYTHONPATH}:$VENV_PATH/lib/python3.12/site-packages"
ENV PATH="${PATH}:${POETRY_VENV}/bin"

RUN groupadd -r $PROJECT_USER && \
    useradd -r -g $PROJECT_USER -d $PROJECT_PATH -s /sbin/nologin -c "Docker image user" $PROJECT_USER

WORKDIR $PROJECT_PATH

COPY poetry.lock pyproject.toml ./

#RUN poetry check

RUN poetry install --no-interaction --no-cache --without dev

# upload scripts
COPY ./docker/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/wait_for_migration.sh /wait_for_migration.sh
RUN sed -i 's/\r//' /wait_for_migration.sh
RUN chmod +x /wait_for_migration.sh

COPY ./docker/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

COPY ./docker/celery/worker/start /start-celeryworker
RUN sed -i 's/\r//' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./docker/celery/beat/start /start-celerybeat
RUN sed -i 's/\r//' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ../.. $PROJECT_PATH

USER $PROJECT_USER
