"""
Email loading utilities for the Okloa project.

This module provides functions for loading email data from various formats
and converting them to a standardized DataFrame format for further processing.
"""

import os
import mailbox
import email
import pandas as pd
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
from typing import List, Dict, Any, Optional, Union


def extract_email_address(addr_str: str) -> str:
    """Extract email address from a string that might be in "Name <email>" format."""
    if not addr_str:
        return ""
    
    # Check if it's in "Name <email>" format
    match = re.search(r'<([^>]+)>', addr_str)
    if match:
        return match.group(1).lower()
    
    # Otherwise, assume it's just an email address
    return addr_str.lower()


def parse_email_message(message: email.message.Message) -> Dict[str, Any]:
    """
    Parse an email message into a dictionary with key fields.
    
    Args:
        message: An email.message.Message object
        
    Returns:
        A dictionary containing extracted email data
    """
    # Extract header information
    msg_id = message.get('Message-ID', '')
    subject = message.get('Subject', '').strip()
    from_addr = extract_email_address(message.get('From', ''))
    
    # Handle multiple recipients
    to_field = message.get('To', '')
    to_addrs = [extract_email_address(addr.strip()) for addr in to_field.split(',') if addr.strip()]
    to_addr = '; '.join(to_addrs) if to_addrs else ''
    
    # Handle CC recipients
    cc_field = message.get('Cc', '')
    cc_addrs = [extract_email_address(addr.strip()) for addr in cc_field.split(',') if addr.strip()]
    cc = '; '.join(cc_addrs) if cc_addrs else ''
    
    # Parse date
    date_str = message.get('Date', '')
    try:
        if date_str:
            date = parsedate_to_datetime(date_str)
        else:
            date = None
    except (TypeError, ValueError):
        date = None
    
    # Extract body content
    body = ""
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body += payload.decode(charset, errors='replace')
                except Exception:
                    body += "[Error decoding text content]"
    else:
        try:
            payload = message.get_payload(decode=True)
            charset = message.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')
        except Exception:
            body = "[Error decoding message content]"
    
    # Get attachments information
    attachments = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            content_disposition = part.get("Content-Disposition", "")
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
    
    # Determine if this is a sent or received email
    # This logic would need to be customized based on the mailbox structure
    # For now, we'll use a placeholder approach
    direction = "sent" if from_addr.endswith("@archives-vaucluse.fr") else "received"
    
    return {
        "message_id": msg_id,
        "date": date,
        "from": from_addr,
        "to": to_addr,
        "cc": cc,
        "subject": subject,
        "body": body,
        "attachments": "; ".join(attachments),
        "has_attachments": len(attachments) > 0,
        "direction": direction
    }


def load_mbox_file(filepath: str) -> pd.DataFrame:
    """
    Load emails from an mbox file into a pandas DataFrame.
    
    Args:
        filepath: Path to the mbox file
        
    Returns:
        DataFrame containing parsed email data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Mbox file not found: {filepath}")
    
    mbox = mailbox.mbox(filepath)
    emails = []
    
    for message in mbox:
        try:
            email_data = parse_email_message(message)
            emails.append(email_data)
        except Exception as e:
            print(f"Error parsing email: {e}")
    
    # Convert to DataFrame
    df = pd.DataFrame(emails)
    
    # Convert date column to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    return df


def load_mailboxes(mailbox_names: List[str], base_dir: str = None) -> pd.DataFrame:
    """
    Load multiple mailboxes and combine them into a single DataFrame.
    
    Args:
        mailbox_names: List of mailbox directory names
        base_dir: Base directory containing the mailbox directories
        
    Returns:
        Combined DataFrame with all emails from the specified mailboxes
    """
    # Use absolute path if base_dir is not provided
    if base_dir is None:
        # Get the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        base_dir = os.path.join(project_root, 'data', 'raw')
    
    print(f"Looking for mailboxes in: {base_dir}")
    all_emails = []
    
    for mailbox_name in mailbox_names:
        mailbox_dir = os.path.join(base_dir, mailbox_name)
        
        # For demonstration: if using mbox format
        mbox_path = os.path.join(mailbox_dir, "emails.mbox")
        if os.path.exists(mbox_path):
            df = load_mbox_file(mbox_path)
            df["mailbox"] = mailbox_name
            all_emails.append(df)
        
        # For individual .eml files
        eml_dir = os.path.join(mailbox_dir, "eml")
        if os.path.exists(eml_dir):
            # Process EML files (not implemented yet)
            pass
    
    # Combine all mailboxes
    if all_emails:
        combined_df = pd.concat(all_emails, ignore_index=True)
        return combined_df
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=[
            "message_id", "date", "from", "to", "cc", "subject", 
            "body", "attachments", "has_attachments", "direction", "mailbox"
        ])


def generate_test_mailboxes(output_dir: str = "../data/raw") -> None:
    """
    Generate test mailbox data for development purposes.
    This is a placeholder implementation that would create sample data.
    
    Args:
        output_dir: Directory where the test mailboxes should be created
    """
    # Implementation would be added here
    pass


if __name__ == "__main__":
    # Example usage
    mailboxes = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"])
    print(f"Loaded {len(mailboxes)} emails from all mailboxes")