#!/bin/bash
# MinIO initialization script for docker-compose.
#
# This script creates the necessary bucket on MinIO startup.
# It runs after MinIO is ready and exits successfully when the bucket exists.
#
# Expected environment variables:
#   MINIO_ROOT_USER: MinIO admin username
#   MINIO_ROOT_PASSWORD: MinIO admin password
#   MINIO_ENDPOINT: MinIO API endpoint (e.g., http://localhost:9000)
#   MINIO_BUCKET_NAME: Name of the bucket to create

set -e

ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
BUCKET_NAME="${MINIO_BUCKET_NAME:-teamflow}"
ACCESS_KEY="${MINIO_ROOT_USER:-minioadmin}"
SECRET_KEY="${MINIO_ROOT_PASSWORD:-minioadmin}"

echo "MinIO initialization starting..."
echo "Endpoint: $ENDPOINT"
echo "Bucket: $BUCKET_NAME"

# Wait for MinIO to be ready (retry a few times)
max_attempts=10
attempt=0
until nc -z minio 9000 || [ $attempt -eq $max_attempts ]; do
  echo "Waiting for MinIO to be ready... (attempt $((attempt + 1))/$max_attempts)"
  sleep 2
  attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
  echo "ERROR: MinIO did not become ready in time"
  exit 1
fi

echo "MinIO is ready. Creating bucket..."

# Configure mc (MinIO client) and create bucket
/usr/local/bin/mc alias set minio "$ENDPOINT" "$ACCESS_KEY" "$SECRET_KEY"

# Create bucket if it doesn't exist
if /usr/local/bin/mc ls "minio/$BUCKET_NAME" > /dev/null 2>&1; then
  echo "Bucket '$BUCKET_NAME' already exists."
else
  echo "Creating bucket '$BUCKET_NAME'..."
  /usr/local/bin/mc mb "minio/$BUCKET_NAME"
  echo "Bucket created successfully."
fi

echo "MinIO initialization complete."
