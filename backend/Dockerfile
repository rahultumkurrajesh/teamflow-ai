# Multi-stage build: dependencies are installed in a builder stage and only the
# installed packages are copied into the slim runtime image, keeping it small.
FROM python:3.12-slim AS builder
WORKDIR /install
COPY requirements.txt .
# Install all dependencies in one command with CPU-only PyTorch index.
# This prevents pip from re-resolving torch to the CUDA version when installing requirements.txt
RUN pip install --no-cache-dir --prefix=/install/deps \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

FROM python:3.12-slim AS runtime
# Run as a non-root user. If the container is ever compromised, the attacker
# does not get root inside it.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /install/deps /usr/local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1
# Runs migrations, then starts the server.
CMD ["./entrypoint.sh"]
