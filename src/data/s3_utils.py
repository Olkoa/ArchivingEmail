import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import logging
from typing import List, Dict, Any, Optional, Union, BinaryIO
import mimetypes

import json
import io

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

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def list_buckets(self) -> List[str]:
        """
        List all available buckets.

        Returns:
            List of bucket names
        """
        try:
            buckets = [bucket.name for bucket in self.s3.buckets.all()]
            return buckets
        except Exception as e:
            self.logger.error(f"Error listing buckets: {e}")
            raise

    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> bool:
        """
        Create a new bucket.

        Args:
            bucket_name: Name of the bucket to create
            region: Region to create the bucket in (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            create_bucket_config = {}
            if region and region != 'us-east-1':
                create_bucket_config['LocationConstraint'] = region

            if create_bucket_config:
                self.s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=create_bucket_config
                )
            else:
                self.s3.create_bucket(Bucket=bucket_name)

            self.logger.info(f"Bucket {bucket_name} created successfully")
            return True
        except ClientError as e:
            self.logger.error(f"Error creating bucket {bucket_name}: {e}")
            return False

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a bucket. If force=True, will delete all objects first.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete all objects in the bucket first

        Returns:
            True if successful, False otherwise
        """
        try:
            bucket = self.s3.Bucket(bucket_name)

            if force:
                bucket.objects.all().delete()

            bucket.delete()
            self.logger.info(f"Bucket {bucket_name} deleted successfully")
            return True
        except ClientError as e:
            self.logger.error(f"Error deleting bucket {bucket_name}: {e}")
            return False

    def list_objects(self, bucket_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """
        List objects in a bucket with optional prefix filter.

        Args:
            bucket_name: Name of the bucket
            prefix: Prefix to filter objects by

        Returns:
            List of objects with key, size, last_modified
        """
        try:
            bucket = self.s3.Bucket(bucket_name)
            objects = []

            for obj in bucket.objects.filter(Prefix=prefix):
                objects.append({
                    'key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified
                })

            return objects
        except ClientError as e:
            self.logger.error(f"Error listing objects in bucket {bucket_name}: {e}")
            raise

    def upload_file(self, file_path: str, bucket_name: str,
                   object_key: Optional[str] = None,
                   extra_args: Optional[Dict[str, Any]] = None) -> bool:
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
            self.s3.meta.client.upload_file(
                file_path, bucket_name, object_key, ExtraArgs=extra_args
            )
            self.logger.info(f"File {file_path} uploaded to {bucket_name}/{object_key}")
            return True
        except ClientError as e:
            self.logger.error(f"Error uploading file {file_path}: {e}")
            return False

    def upload_fileobj(self, file_obj: BinaryIO, bucket_name: str,
                      object_key: str,
                      extra_args: Optional[Dict[str, Any]] = None) -> bool:
        """
        Upload a file-like object to S3.

        Args:
            file_obj: File-like object to upload
            bucket_name: Name of the bucket
            object_key: Key to use in S3
            extra_args: Additional arguments for upload (ContentType, ACL, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3.meta.client.upload_fileobj(
                file_obj, bucket_name, object_key, ExtraArgs=extra_args or {}
            )
            self.logger.info(f"File object uploaded to {bucket_name}/{object_key}")
            return True
        except ClientError as e:
            self.logger.error(f"Error uploading file object: {e}")
            return False

    def download_file(self, bucket_name: str, object_key: str,
                     file_path: str) -> bool:
        """
        Download a file from S3.

        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object in S3
            file_path: Path to save the file locally

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            self.s3.meta.client.download_file(
                bucket_name, object_key, file_path
            )
            self.logger.info(f"File {bucket_name}/{object_key} downloaded to {file_path}")
            return True
        except ClientError as e:
            self.logger.error(f"Error downloading file {bucket_name}/{object_key}: {e}")
            return False

    def get_object(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """
        Get an object and its metadata from S3.

        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object in S3

        Returns:
            Dictionary with object content and metadata
        """
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=object_key)
            return {
                'Body': response['Body'].read(),
                'ContentType': response.get('ContentType'),
                'ContentLength': response.get('ContentLength'),
                'LastModified': response.get('LastModified'),
                'Metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            self.logger.error(f"Error getting object {bucket_name}/{object_key}: {e}")
            raise

    def delete_object(self, bucket_name: str, object_key: str) -> bool:
        """
        Delete an object from S3.

        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object in S3

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3.Object(bucket_name, object_key).delete()
            self.logger.info(f"Object {bucket_name}/{object_key} deleted successfully")
            return True
        except ClientError as e:
            self.logger.error(f"Error deleting object {bucket_name}/{object_key}: {e}")
            return False

    def delete_objects(self, bucket_name: str, object_keys: List[str]) -> Dict[str, List[str]]:
        """
        Delete multiple objects from S3 in a single request.

        Args:
            bucket_name: Name of the bucket
            object_keys: List of object keys to delete

        Returns:
            Dictionary with 'Deleted' and 'Errors' lists
        """
        if not object_keys:
            return {'Deleted': [], 'Errors': []}

        try:
            objects = [{'Key': key} for key in object_keys]
            response = self.client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects}
            )

            deleted = [obj.get('Key') for obj in response.get('Deleted', [])]
            errors = [f"{err.get('Key')}: {err.get('Message')}" for err in response.get('Errors', [])]

            if deleted:
                self.logger.info(f"Deleted {len(deleted)} objects from {bucket_name}")
            if errors:
                self.logger.warning(f"Failed to delete {len(errors)} objects from {bucket_name}")

            return {
                'Deleted': deleted,
                'Errors': errors
            }
        except ClientError as e:
            self.logger.error(f"Error batch deleting objects from {bucket_name}: {e}")
            raise

    def copy_object(self, source_bucket: str, source_key: str,
                   dest_bucket: str, dest_key: str) -> bool:
        """
        Copy an object within S3.

        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key

        Returns:
            True if successful, False otherwise
        """
        try:
            copy_source = {
                'Bucket': source_bucket,
                'Key': source_key
            }
            self.s3.meta.client.copy(copy_source, dest_bucket, dest_key)
            self.logger.info(f"Object {source_bucket}/{source_key} copied to {dest_bucket}/{dest_key}")
            return True
        except ClientError as e:
            self.logger.error(f"Error copying object: {e}")
            return False

    def generate_presigned_url(self, bucket_name: str, object_key: str,
                              expiration: int = 3600, http_method: str = 'GET') -> Optional[str]:
        """
        Generate a presigned URL for an S3 object.

        Args:
            bucket_name: Name of the bucket
            object_key: Key of the object in S3
            expiration: Time in seconds until the URL expires
            http_method: HTTP method to allow ('GET', 'PUT')

        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object' if http_method == 'GET' else 'put_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            self.logger.error(f"Error generating presigned URL: {e}")
            return None


# Example usage in main
if __name__ == "__main__":
    # Initialize the handler
    s3_handler = S3Handler()

    try:
        # List buckets
        print("Available buckets:")
        buckets = s3_handler.list_buckets()
        for bucket in buckets:
            print(f"- {bucket}")

        # if buckets:
        #     # Pick the first bucket for demonstration
        #     demo_bucket = buckets[0]
        #     print(f"\nListing objects in bucket '{demo_bucket}':")
        #     objects = s3_handler.list_objects(demo_bucket)

        #     for obj in objects[:10]:  # Show first 10 objects
        #         print(f"- {obj['key']} ({obj['size']} bytes, modified: {obj['last_modified']})")

        testerette_bucket = 'demo-testerette-bucket'

        s3_handler.create_bucket(testerette_bucket)
        buckets = s3_handler.list_buckets()
        for bucket in buckets:
            print(f"- {bucket}")

        # Upload a file
        # s3_handler.upload_file('mermaid.md', testerette_bucket, 'mermaid.md')
        # print("\nUploading file to bucket:")
        # objects = s3_handler.list_objects(testerette_bucket)

        print(f"\nListing objects in bucket '{testerette_bucket}':")
        objects = s3_handler.list_objects(testerette_bucket)

        # For a string
        text_data = "This is some text I want to upload"
        text_file_obj = io.BytesIO(text_data.encode('utf-8'))  # Convert to bytes and wrap in BytesIO

        # Upload the string as a file
        s3_handler.upload_fileobj(
            file_obj=text_file_obj,
            bucket_name=testerette_bucket,
            object_key="my-text-file.txt"
        )

        # For a JSON object
        json_data = {"name": "John", "age": 30}
        json_string = json.dumps(json_data)  # Convert to JSON string
        json_file_obj = io.BytesIO(json_string.encode('utf-8'))  # Convert to bytes and wrap in BytesIO

        # Upload the JSON as a file
        s3_handler.upload_fileobj(
            file_obj=json_file_obj,
            bucket_name=testerette_bucket,
            object_key="data.json",
            extra_args={"ContentType": "application/json"}  # Specify correct content type
        )

        # s3_handler.get_object(testerette_bucket, 'mermaid.md')
        # # Get the object
        # obj = s3_handler.get_object(testerette_bucket, 'mermaid.md')

        # # The body is returned as bytes, so we need to decode it to a string
        # # Assuming the content is UTF-8 encoded text
        # content = obj['Body'].decode('utf-8')

        # # Print the content
        # print("File content:", content)

        # # Delete the object
        # s3_handler.delete_object(testerette_bucket, 'mermaid.md')
        print("\nListing objects in bucket after deletion:")
        objects = s3_handler.list_objects(testerette_bucket)
        for obj in objects:
            print(f"- {obj['key']} ({obj['size']} bytes, modified: {obj['last_modified']})")

        # Copy my-text-file.txt
        s3_handler.copy_object(
            source_bucket=testerette_bucket,
            source_key='my-text-file.txt',
            dest_bucket=testerette_bucket,
            dest_key='copied-text-file.txt'
        )

        print("\nListing objects in bucket after copying:")
        objects = s3_handler.list_objects(testerette_bucket)
        for obj in objects:
            print(f"- {obj['key']} ({obj['size']} bytes, modified: {obj['last_modified']})")


        s3_handler.delete_bucket(testerette_bucket, force=True)

        # List buckets again to confirm deletion
        print("\nAvailable buckets after deletion:")

        buckets = s3_handler.list_buckets()
        for bucket in buckets:
            print(f"- {bucket}")

    except Exception as e:
        print(f"Error: {e}")
