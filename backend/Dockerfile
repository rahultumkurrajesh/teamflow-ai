# Multi-stage build: dependencies are installed in a builder stage and only the
# installed packages are copied into the slim runtime image, keeping it small.
FROM python:3.12-slim AS builder
WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

FROM python:3.12-slim AS runtime
# Run as a non-root user. If the container is ever compromised, the attacker
# does not get root inside it.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /install/deps /usr/local
COPY app ./app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
