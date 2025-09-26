import os
import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import logging
from typing import Dict, Any, Optional
import mimetypes

import math
import sys
import threading
import time

class UploadProgress:
    """Console progress reporter for S3 uploads."""

    def __init__(self, filename: str):
        self.filename = filename
        self.filesize = float(os.path.getsize(filename)) if os.path.exists(filename) else 0.0
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._start_time = time.time()

    def __call__(self, bytes_amount: int) -> None:
        if self.filesize <= 0:
            return
        with self._lock:
            self._seen_so_far += bytes_amount
            elapsed = max(time.time() - self._start_time, 1e-6)
            speed = self._seen_so_far / elapsed  # bytes/sec
            remaining = max(self.filesize - self._seen_so_far, 0.0)
            eta = remaining / speed if speed > 0 else float("inf")
            percentage = (self._seen_so_far / self.filesize) * 100.0

            eta_str = f"{eta:6.1f}s" if math.isfinite(eta) else "--.-s"

            line = (
                f"\r[{os.path.basename(self.filename)}] "
                f"{self._seen_so_far/1e6:8.1f} / {self.filesize/1e6:8.1f} MB "
                f"({percentage:5.1f}%)  speed: {speed/1e6:5.1f} MB/s  ETA: {eta_str}"
            )
            sys.stdout.write(line)
            sys.stdout.flush()

            if self._seen_so_far >= self.filesize:
                sys.stdout.write("\n")

class S3Handler:
    """
    A class to handle common S3 operations using boto3.
    This includes listing, creating, deleting buckets and objects,
    uploading and downloading files, and generating presigned URLs.
    It also supports using environment variables for configuration.
    Environment variables:
        - S3_ENDPOINT_URL: The endpoint URL for the S3 service
        - S3_REGION_NAME: The region name for the S3 service
        - SCW_ACCESS_KEY: Access key ID for authentication
        - SCW_SECRET_KEY: Secret access key for authentication
    Example usage:
        s3_handler = S3Handler()
        buckets = s3_handler.list_buckets()
        print(buckets)
        s3_handler.create_bucket('my-new-bucket')
        s3_handler.upload_file('local_file.txt', 'my-new-bucket', 's3_file.txt')
        url = s3_handler.generate_presigned_url('my-new-bucket', 's3_file.txt')
        print(url)
        s3_handler.download_file('my-new-bucket', 's3_file.txt', 'downloaded_file.txt')
    This class requires the `boto3` and `python-dotenv` packages.
    Install them using:
        pip install boto3 python-dotenv
    Ensure to set the environment variables or pass them as arguments.
    """

    def __init__(self, endpoint_url=None, region_name=None,
                 access_key_id=None, secret_access_key=None):
        """
        Initialize the S3 handler with optional credentials.
        If not provided, will use environment variables.
        """
        # Load environment variables if not done already
        load_dotenv()

        # Use provided credentials or fall back to environment variables
        self.endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self.region_name = region_name or os.getenv("S3_REGION_NAME")
        self.access_key_id = access_key_id or os.getenv("SCW_ACCESS_KEY")
        self.secret_access_key = secret_access_key or os.getenv("SCW_SECRET_KEY")

        # Initialize S3 resource and client
        self.s3 = boto3.resource(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key
        )

        self.client = boto3.client(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key
        )

        # Configure multipart uploads to stay within S3 limits
        self.transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=128 * 1024 * 1024
        )

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_path: str, bucket_name: str,
                   object_key: Optional[str] = None,
                   extra_args: Optional[Dict[str, Any]] = None,
                   show_progress: bool = True) -> bool:
        """
        Upload a file to S3.

        Args:
            file_path: Path to the local file
            bucket_name: Name of the bucket
            object_key: Key to use in S3 (defaults to filename if not provided)
            extra_args: Additional arguments for upload (ContentType, ACL, etc.)

        Returns:
            True if successful, False otherwise
        """
        if not object_key:
            object_key = os.path.basename(file_path)

        # Determine content type if not specified in extra_args
        if extra_args is None:
            extra_args = {}

        if 'ContentType' not in extra_args:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type:
                extra_args['ContentType'] = content_type

        try:
            file_size = os.path.getsize(file_path)
            max_parts = 1000
            min_chunk_size = 8 * 1024 * 1024
            suggested_chunk = max(min_chunk_size, math.ceil(file_size / max_parts))
            max_chunk_size = 5 * 1024 * 1024 * 1024
            chunk_size = min(suggested_chunk, max_chunk_size)

            if chunk_size != self.transfer_config.multipart_chunksize:
                transfer_config = TransferConfig(
                    multipart_threshold=self.transfer_config.multipart_threshold,
                    multipart_chunksize=chunk_size,
                )
            else:
                transfer_config = self.transfer_config

            callback = UploadProgress(file_path) if show_progress else None
            self.s3.meta.client.upload_file(
                file_path,
                bucket_name,
                object_key,
                ExtraArgs=extra_args,
                Config=transfer_config,
                Callback=callback
            )
            self.logger.info(f"File {file_path} uploaded to {bucket_name}/{object_key}")
            return True
        except ClientError as e:
            self.logger.error(f"Error uploading file {file_path}: {e}")
            return False

    def upload_directory(self, local_dir, bucket_name, s3_prefix, show_progress: bool = True):
        """
        Upload a directory and all its contents to S3, preserving the folder structure.

        Args:
            s3_handler: Instance of S3Handler class
            local_dir: Path to local directory
            bucket_name: Name of the S3 bucket
            s3_prefix: Prefix in S3 where files should be uploaded
        """
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_file_path = os.path.join(root, file)

                # Create S3 key by replacing local path with S3 prefix
                relative_path = os.path.relpath(local_file_path, local_dir)
                s3_key = os.path.join(s3_prefix, relative_path).replace("\\", "/")

                # Upload the file
                self.upload_file(
                    file_path=local_file_path,
                    bucket_name=bucket_name,
                    object_key=s3_key,
                    show_progress=show_progress
                )
                print(f"Uploaded {local_file_path} to {bucket_name}/{s3_key}")


def  upload_raw_data_to_s3(local_raw_data_dir, mailbox_name):

    # Initialize S3 handler
    s3_handler = S3Handler()

    # Define your project bucket name
    project_bucket = "olkoa-projects"

    # Upload raw data directory to S3
    # local_raw_data_dir = "data/Projects/Projet Demo/Boîte mail de Céline/raw/"
    s3_prefix = f"{mailbox_name}/raw/"

    s3_handler.upload_directory(
        local_dir=local_raw_data_dir,
        bucket_name=project_bucket,
        s3_prefix=s3_prefix
    )
    print(f"Uploaded contents of '{local_raw_data_dir}' to 's3://{project_bucket}/{s3_prefix}'")