"""S3-compatible storage client using boto3.

Works with both MinIO (local development) and real S3 (production).
Configuration comes from environment variables, so the same code works
against either backend without code changes.

Environment variables:
    S3_ENDPOINT_URL: MinIO/S3 endpoint (empty for real AWS S3)
    S3_ACCESS_KEY_ID: Access key
    S3_SECRET_ACCESS_KEY: Secret key
    S3_BUCKET_NAME: Bucket name
    S3_REGION: AWS region (default: us-east-1)
"""
import logging
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class S3Storage:
    """S3-compatible storage client."""

    def __init__(self):
        """Initialize S3 client from environment configuration."""
        self.bucket_name = settings.s3_bucket_name
        self.region = settings.s3_region

        client_kwargs = {
            "aws_access_key_id": settings.s3_access_key_id,
            "aws_secret_access_key": settings.s3_secret_access_key,
            "region_name": self.region,
        }

        if settings.s3_endpoint_url:
            # MinIO or other S3-compatible service
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url

        self.s3_client = boto3.client("s3", **client_kwargs)

    def upload_file(
        self, storage_key: str, file_content: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        """Upload a file to the bucket.

        Args:
            storage_key: Unique key for the file in the bucket (e.g., project_id/document_id/filename).
            file_content: File contents as bytes.
            content_type: MIME type of the file.

        Raises:
            Exception if the upload fails.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=BytesIO(file_content),
                ContentType=content_type,
            )
            logger.info(f"Uploaded file to S3: {storage_key}")
        except ClientError as e:
            logger.exception(f"Failed to upload file to S3: {e}")
            raise

    def download_file(self, storage_key: str) -> bytes:
        """Download a file from the bucket.

        Args:
            storage_key: Unique key for the file in the bucket.

        Returns:
            File contents as bytes.

        Raises:
            Exception if the download fails.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_key)
            return response["Body"].read()
        except ClientError as e:
            logger.exception(f"Failed to download file from S3: {e}")
            raise

    def delete_file(self, storage_key: str) -> None:
        """Delete a file from the bucket.

        Args:
            storage_key: Unique key for the file in the bucket.

        Raises:
            Exception if the deletion fails.
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_key)
            logger.info(f"Deleted file from S3: {storage_key}")
        except ClientError as e:
            logger.exception(f"Failed to delete file from S3: {e}")
            raise

    def generate_presigned_url(self, storage_key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for downloading a file.

        The URL is valid for the specified expiration time (default 1 hour).
        Can be used to provide temporary access to files without authentication.

        Args:
            storage_key: Unique key for the file in the bucket.
            expiration: URL expiration time in seconds (default 3600 = 1 hour).

        Returns:
            Presigned URL as a string.

        Raises:
            Exception if URL generation fails.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": storage_key},
                ExpiresIn=expiration,
            )
            logger.debug(f"Generated presigned URL for: {storage_key}")
            return url
        except ClientError as e:
            logger.exception(f"Failed to generate presigned URL: {e}")
            raise

    def file_exists(self, storage_key: str) -> bool:
        """Check if a file exists in the bucket.

        Args:
            storage_key: Unique key for the file in the bucket.

        Returns:
            True if the file exists, False otherwise.
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=storage_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.exception(f"Error checking if file exists: {e}")
            raise


# Global instance
storage = S3Storage()
