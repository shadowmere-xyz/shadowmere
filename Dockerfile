FROM cgr.dev/chainguard/python:latest-dev AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/shadowmere/venv/bin:$PATH"

WORKDIR /shadowmere/
RUN python -m venv ./venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM cgr.dev/chainguard/python:latest

ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
COPY --from=builder /shadowmere/venv /venv

WORKDIR /app/
COPY . .

CMD ["python", "-m", "gunicorn", "shadowmere.wsgi:application", "--bind", "0.0.0.0:8001", "-k", "gevent", "-w", "6", "--capture-output"]

ENTRYPOINT [ ]