# Stage 1 – build wheels
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y build-essential git
WORKDIR /app
COPY requirements.txt .
RUN pip wheel -r requirements.txt -w /wheels

# Stage 2 – runtime
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels
COPY . .
HEALTHCHECK CMD curl --fail http://localhost:8000/healthz || exit 1
CMD ["uvicorn", "app.enhanced_main:app", "--host", "0.0.0.0", "--port", "8000"]
