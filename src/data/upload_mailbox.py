"""CLI helper for uploading mailbox raw data directories to S3."""
from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.data.s3_utils import S3Handler


def upload_raw_data_to_s3(
    local_raw_data_dir: str,
    mailbox_name: str,
    project_bucket: str = "olkoa-projects",
    show_progress: bool = True,
) -> None:
    """Upload mailbox raw data folder to the shared S3 bucket."""
    load_dotenv()

    s3_handler = S3Handler()

    buckets = s3_handler.list_buckets()
    print("Existing buckets:", buckets)

    if project_bucket not in buckets:
        s3_handler.create_bucket(project_bucket)
        print(f"Bucket '{project_bucket}' created.")
    else:
        print(f"Bucket '{project_bucket}' already exists.")

    print("Available prefixes:", s3_handler.list_directories(project_bucket, prefix=""))

    s3_handler.upload_mailbox_raw(
        local_raw_data_dir=local_raw_data_dir,
        mailbox_name=mailbox_name,
        project_bucket=project_bucket,
        show_progress=show_progress,
    )
    print(f"Uploaded contents of '{local_raw_data_dir}' to 's3://{project_bucket}/{mailbox_name}/raw/'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a mailbox raw directory to S3.")
    parser.add_argument("local_raw_data_dir", type=Path, help="Path to the mailbox raw directory")
    parser.add_argument("mailbox_name", type=str, help="Mailbox name used as S3 prefix")
    parser.add_argument(
        "--bucket",
        default="olkoa-projects",
        help="Target bucket name (default: olkoa-projects)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress output",
    )

    args = parser.parse_args()

    upload_raw_data_to_s3(
        local_raw_data_dir=str(args.local_raw_data_dir),
        mailbox_name=args.mailbox_name,
        project_bucket=args.bucket,
        show_progress=not args.no_progress,
    )


if __name__ == "__main__":
    main()
