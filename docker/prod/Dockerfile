FROM python:3.12-slim as builder
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
		PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    PROJECT_PATH="/shadowmere"

# install poetry
RUN pip install --upgrade poetry

# copy poetry and project files
WORKDIR $PROJECT_PATH
COPY ../../poetry.lock pyproject.toml ./

# install dependencies and project
RUN poetry install --no-root --no-interaction --no-cache && rm -rf $POETRY_CACHE_DIR


# run stage
FROM python:3.12-slim

# Creating user
ARG USERNAME=shadowmere
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Timezone
ARG TZ=UTC
ENV TZ ${TZ}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# OS dependencies
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    apt-get update && \
    apt-get install -y sudo && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/apt && \
    rm -rf /var/lib/dpkg && \
    rm -rf /var/cache && \
    rm -rf /var/log && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

ENV VIRTUAL_ENV=/shadowmere/.venv
ENV PATH="/shadowmere/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# upload scripts
COPY --chmod=755 ../../docker/dev/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint

COPY --chmod=755 ../../docker/dev/start /start
RUN sed -i 's/\r//' /start

USER $USERNAME

WORKDIR $PROJECT_PATH
