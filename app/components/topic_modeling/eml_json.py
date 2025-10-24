import os
import json
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path


def _sanitize_string(value):
    """Return a UTF-8 safe string, replacing any surrogate characters."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    return value.encode("utf-8", "replace").decode("utf-8")

# === CONFIGURATION ===
#EML_FOLDER = "Éléments envoyés"  # 👈 change this
# MAILBOX_NAME = "Boîte mail de Céline"
# MAILBOX_PATH = "processed/celine.guyon/Boîte de réception"


def extract_email_fields(eml_path, MAILBOX_NAME,MAILBOX_PATH):
    """Extract all relevant fields from a .eml file."""
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    # Helper to safely get header
    def safe_get(field):
        raw = msg.get(field, None)
        return _sanitize_string(raw)

    # Extract email body (prefer plain text, fallback to HTML)
    plain_body = ""
    html_body = ""
    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get_content_disposition()

        if content_disposition == "attachment":
            continue  # skip attachments

        if content_type == "text/plain":
            plain_body += part.get_content()
        elif content_type == "text/html":
            html_body += part.get_content()

    # Clean HTML body with BeautifulSoup
    body = plain_body.strip()
    if not body and html_body:
        soup = BeautifulSoup(html_body, "html.parser")
        # remove script and style tags
        for tag in soup(["script", "style"]):
            tag.decompose()
        body = soup.get_text(separator=" ", strip=True)

    body = _sanitize_string(body)

    # Detect attachments
    has_attachments = any(
        part.get_filename() for part in msg.walk() if part.get_content_disposition() == "attachment"
    )

    # Convert date to Unix timestamp
    date_hdr = msg.get("Date")
    if date_hdr:
        try:
            date_parsed = email.utils.parsedate_to_datetime(date_hdr)
            timestamp = int(date_parsed.timestamp())
        except Exception:
            timestamp = None
    else:
        timestamp = None

    # Build structured dictionary
    email_data = {
        "message_id": safe_get("Message-ID"),
        "date": timestamp,
        "mailbox_name": _sanitize_string(MAILBOX_NAME),
        "direction": "received",
        "from": safe_get("From"),
        "to": safe_get("To"),
        "cc": safe_get("Cc"),
        "subject": safe_get("Subject"),
        "body": body,
        "has_attachments": has_attachments,
        "mailbox": _sanitize_string(MAILBOX_PATH),
        "file_name": _sanitize_string(os.path.basename(eml_path))
    }

    return email_data


def run_email_extraction(EML_FOLDER,MAILBOX_NAME,MAILBOX_PATH):
    all_emails = []

    for root, _, files in os.walk(EML_FOLDER):
        for file in files:
            if file.lower().endswith(".eml"):
                eml_path = os.path.join(root, file)
                try:
                    email_data = extract_email_fields(eml_path, MAILBOX_NAME, MAILBOX_PATH)
                    sanitized_data = {
                        key: _sanitize_string(value) if isinstance(value, str) else value
                        for key, value in email_data.items()
                    }
                    all_emails.append(sanitized_data)
                except Exception as e:
                    print(f"⚠️ Error reading {file}: {e}")

    # Write all emails to JSON (saved alongside this module)
    output_path = Path(__file__).resolve().parent / "email_output.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(all_emails, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracted {len(all_emails)} emails to {output_path}")

# def run_email_extraction(EML_FOLDER,MAILBOX_NAME,MAILBOX_PATH):
#     main(EML_FOLDER,MAILBOX_NAME,MAILBOX_PATH)
