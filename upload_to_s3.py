
#!/usr/bin/env python3
"""CLI helper wrapping `upload_raw_data_to_s3` for quick S3 uploads."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.data.upload_mailbox import upload_raw_data_to_s3

REQUIRED_ENV_VARS = [
    "S3_ENDPOINT_URL",
    "S3_REGION_NAME",
    "SCW_ACCESS_KEY",
    "SCW_SECRET_KEY",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a mailbox raw directory to S3 using preconfigured credentials.",
    )
    parser.add_argument(
        "local_raw_data_dir",
        type=Path,
        help="Local path to the mailbox raw directory (e.g. data/Projects/<Project>/<Mailbox>/raw)",
    )
    parser.add_argument(
        "mailbox_name",
        type=str,
        help="Name of the mailbox; used as the S3 prefix (e.g. BoiteMailDeCeline)",
    )
    parser.add_argument(
        "--bucket",
        default="olkoa-projects",
        help="Target bucket name (default: olkoa-projects)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable console upload progress output",
    )
    return parser.parse_args()


def ensure_environment() -> None:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if not missing:
        return

    message_lines = [
        "❌ Missing required environment variables:",
        "  " + ", ".join(missing),
        "",
        "Set them in your shell before running this script, for example:",
        "  export S3_ENDPOINT_URL=https://your-endpoint",
        "  export S3_REGION_NAME=fr-par",
        "  export SCW_ACCESS_KEY=your_access_key",
        "  export SCW_SECRET_KEY=your_secret_key",
        "",
        "Retry after exporting the variables or placing them in a .env file",
    ]
    sys.stderr.write("\n".join(message_lines) + "\n")
    sys.exit(1)


def main() -> None:
    args = parse_args()
    load_dotenv()
    ensure_environment()

    local_dir = args.local_raw_data_dir
    if not local_dir.exists():
        sys.stderr.write(f"❌ Local directory not found: {local_dir}\n")
        sys.exit(1)

    try:
        upload_raw_data_to_s3(
            local_raw_data_dir=str(local_dir),
            mailbox_name=args.mailbox_name,
            project_bucket=args.bucket,
            show_progress=not args.no_progress,
        )
    except Exception as exc:
        sys.stderr.write(f"❌ Upload failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
