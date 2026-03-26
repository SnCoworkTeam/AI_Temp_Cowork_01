FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements.txt

COPY backend/app /app/app

ENV HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
