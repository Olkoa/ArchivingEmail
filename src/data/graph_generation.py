
"""Utilities for pre-generating mailbox graphs."""
from __future__ import annotations

import json
import os
import shutil
import email
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from bs4 import BeautifulSoup
from email.policy import default as default_policy

from src.features.decodeml import decode_unicode_escape, getBody


LOGGER = logging.getLogger(__name__)


def _decode_email_text(text: Optional[str], encoding: str = "utf-8") -> str:
    """Best-effort decoding mirroring the Streamlit viewer helper."""
    if not text:
        return ""

    value = str(text)
    try:
        decoded_header = email.header.decode_header(value)
        decoded = ""
        for part, charset in decoded_header:
            if isinstance(part, bytes):
                charset = charset or encoding
                try:
                    decoded += part.decode(charset, errors="replace")
                except LookupError:
                    decoded += part.decode("utf-8", errors="replace")
            else:
                decoded += part
        value = decoded
    except Exception:
        pass

    try:
        return value.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return value


def _list_processed_folders(project_path: Path, mailbox_names: Iterable[str]) -> List[Dict[str, object]]:
    folders: List[Dict[str, object]] = []

    for mailbox in mailbox_names:
        processed_root = project_path / mailbox / "processed"
        if not processed_root.exists():
            continue

        for dirpath, _, filenames in os.walk(processed_root):
            eml_count = sum(1 for name in filenames if name.lower().endswith(".eml"))
            if not eml_count:
                continue

            current_dir = Path(dirpath)
            relative_path = current_dir.relative_to(processed_root)
            relative_display = "" if str(relative_path) in (".", "") else str(relative_path).replace("\\", "/")

            folders.append(
                {
                    "mailbox": mailbox,
                    "path": current_dir,
                    "relative_path": relative_path,
                    "relative_display": relative_display,
                    "eml_count": eml_count,
                }
            )

    folders.sort(key=lambda item: (item["mailbox"], str(item["relative_path"])) )
    return folders


def _extract_emails_from_folder(folder: Path) -> List[Dict[str, str]]:
    emails: List[Dict[str, str]] = []
    for entry in folder.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".eml":
            try:
                with entry.open("r", encoding="utf-8", errors="ignore") as handle:
                    msg = email.message_from_file(handle, policy=default_policy)

                sender_raw = msg.get("From", "")
                sender = email.utils.parseaddr(sender_raw)[1]
                sender = _decode_email_text(sender)

                receivers = msg.get_all("To", [])
                receiver_list = email.utils.getaddresses(receivers)

                subject = _decode_email_text(msg.get("Subject", ""))
                date = msg.get("Date", "")

                try:
                    html_body = getBody(msg)
                    soup = BeautifulSoup(html_body, "html.parser")
                    body_text = soup.get_text()
                    body_text = decode_unicode_escape(body_text)
                    body_text = _decode_email_text(body_text)
                except Exception:
                    body_text = ""

                for _, addr in receiver_list:
                    normalized_addr = _decode_email_text(addr)
                    if not normalized_addr:
                        continue
                    emails.append(
                        {
                            "sender": sender or "unknown",
                            "receiver": normalized_addr,
                            "subject": subject,
                            "date": date,
                            "body": body_text,
                        }
                    )
            except Exception as exc:
                LOGGER.warning("Failed to parse %s: %s", entry, exc)
    return emails


def _build_graph(emails: List[Dict[str, str]]) -> Dict[str, object]:
    from collections import defaultdict

    normalized = [
        {
            "sender": str(item["sender"]).strip().lower(),
            "receiver": str(item["receiver"]).strip().lower(),
            "subject": item.get("subject", ""),
            "date": item.get("date", ""),
            "body": item.get("body", ""),
        }
        for item in emails
        if item.get("sender") and item.get("receiver")
    ]

    unique_emails = sorted({entry["sender"] for entry in normalized} | {entry["receiver"] for entry in normalized})
    nodes = [{"id": email_addr, "name": email_addr} for email_addr in unique_emails if email_addr]

    edges_map: Dict[tuple, Dict[str, object]] = {}
    for entry in normalized:
        key = (entry["sender"], entry["receiver"])
        if key not in edges_map:
            edges_map[key] = {
                "id": f"{entry['sender']}->{entry['receiver']}",
                "source": entry["sender"],
                "target": entry["receiver"],
                "label": f"{entry['sender']} → {entry['receiver']}",
                "interactions": [],
            }
        edges_map[key]["interactions"].append(
            {
                "date": entry.get("date", ""),
                "subject": entry.get("subject", ""),
                "body": entry.get("body", ""),
            }
        )

    return {"nodes": nodes, "edges": list(edges_map.values())}


def generate_graphs_for_project(project_name: str, project_path: Path, mailbox_names: Iterable[str]) -> Dict[str, object]:
    """Generate mailbox graphs for all folders under processed/ for each mailbox."""
    processed_folders = _list_processed_folders(project_path, mailbox_names)
    graphs_root = project_path / "Graphs"

    if graphs_root.exists():
        shutil.rmtree(graphs_root)
    graphs_root.mkdir(parents=True, exist_ok=True)

    index_entries: List[Dict[str, object]] = []
    all_emails: List[Dict[str, str]] = []
    total_emails = 0

    for idx, folder in enumerate(processed_folders, start=1):
        emails = _extract_emails_from_folder(folder["path"])
        if not emails:
            continue

        graph_data = _build_graph(emails)
        graph_dir_name = f"graph_{idx:03d}"
        graph_dir = graphs_root / graph_dir_name
        graph_dir.mkdir(parents=True, exist_ok=True)

        json_path = graph_dir / "graph.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(graph_data, handle, ensure_ascii=False)

        index_entries.append(
            {
                "id": graph_dir_name,
                "mailbox": folder["mailbox"],
                "relative_parent": str(Path(folder["path"]).relative_to(project_path)),
                "relative_display": folder["relative_display"],
                "eml_count": folder["eml_count"],
                "graph_json": str(Path(graph_dir_name) / "graph.json"),
            }
        )

        all_emails.extend(emails)
        total_emails += folder["eml_count"]

    if all_emails:
        graph_data_full = _build_graph(all_emails)
        graph_dir_name = f"graph_{len(index_entries) + 1:03d}"
        graph_dir = graphs_root / graph_dir_name
        graph_dir.mkdir(parents=True, exist_ok=True)

        json_path = graph_dir / "graph.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(graph_data_full, handle, ensure_ascii=False)

        index_entries.append(
            {
                "id": graph_dir_name,
                "mailbox": "Boîte Mail Complète",
                "relative_parent": "FULL_MAILBOX",
                "relative_display": "",
                "eml_count": total_emails,
                "graph_json": str(Path(graph_dir_name) / "graph.json"),
                "is_full_mailbox": True,
            }
        )

    index_data = {
        "project": project_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "graphs": index_entries,
    }

    index_path = graphs_root / "index.json"
    with index_path.open("w", encoding="utf-8") as handle:
        json.dump(index_data, handle, ensure_ascii=False, indent=2)

    return index_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate prebuilt graphs for a project.")
    parser.add_argument("project_path", type=str)
    parser.add_argument("project_name", type=str)
    parser.add_argument("mailboxes", nargs="+")
    args = parser.parse_args()

    generate_graphs_for_project(args.project_name, Path(args.project_path), args.mailboxes)
