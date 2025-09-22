

import argparse
import os
import sys
from typing import List, Optional, Union, Dict, Any
import re
import html
import logging
from email.header import decode_header
import uuid
import datetime
import email.utils
from pathlib import Path
from tqdm import tqdm
from email import policy
from bs4 import BeautifulSoup
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT") or "Projet Demo"

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.models import EmailAddress, MailingList, Entity, Attachment, ReceiverEmail, SenderEmail
from src.data.duckdb_utils import setup_database

import constants


def clean_html(html_string):
    """
    Clean HTML content from a string and return plain text.

    Args:
        html_string (str): HTML content as string

    Returns:
        str: Plain text with HTML removed
    """
    if not html_string or not isinstance(html_string, str):
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_string, "html.parser")

    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text
    text = soup.get_text()

    # Remove extra whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

def parse_email_address(address_str: Optional[str]) -> List['Entity']:
    """
    Parse a string containing email addresses into a list of Entity objects.

    This function handles various email address formats including:
    - "Name <email@example.com>"
    - "email@example.com"
    - Multiple comma-separated addresses
    - Addresses with quoted parts

    Args:
        address_str: A string containing one or more email addresses
                     If None or empty, returns an empty list

    Returns:
        A list of Entity objects with populated name and email attributes

    Example:
        >>> entities = parse_email_address('John Doe <john@example.com>, jane@example.com')
        >>> len(entities)
        2
        >>> entities[0].name
        'John Doe'
        >>> entities[0].email.email
        'john@example.com'
    """
    if not address_str:
        # print("NO ADRESSSSS")
        return []

    # print("address_str", address_str)

    entities = []
    # Simple regex to extract name and email from patterns like "Name <email@example.com>"
    email_pattern = re.compile(r'(.*?)\s*<([^>]+)>|([^,\s]+@[^,\s]+)')

    try:
        # Split by commas, but handle potential nested commas in quotes
        addresses = []
        in_quotes = False
        current_address = ""

        for char in address_str:
            if char == '"':
                in_quotes = not in_quotes
                current_address += char
            elif char == ',' and not in_quotes:
                addresses.append(current_address.strip())
                current_address = ""
            else:
                current_address += char

        # Add the last address if there is one
        if current_address.strip():
            addresses.append(current_address.strip())

        # If no addresses were found, try the whole string
        if not addresses:
            addresses = [address_str]

        # print(addresses)


        for addr in addresses:
            addr = addr.strip()
            addr = re.sub(r'[();"\']+', '', addr).strip()
            if not addr:
                continue

            try:
                match = email_pattern.search(addr)
                if match:
                    if match.group(2):  # Format: "Name <email@example.com>"
                        name = match.group(1).strip().strip('"')
                        email_addr = match.group(2).strip()
                    else:  # Format: "email@example.com"
                        email_addr = match.group(3).strip()
                        name = email_addr  # Use email as name if no name is provided

                    # Validate email format to a minimum degree
                    if '@' in email_addr:
                        # Create Entity with EmailAddress
                        try:
                            email_obj = EmailAddress(email=email_addr)
                            entity = Entity(
                                name=name,
                                #is_physical_person=True,  # Assuming default
                                email=email_obj.model_dump() # email=email_obj,
                            )

                            entities.append(entity)
                        except Exception as e:
                            logging.error(f"Error creating Entity for email {email_addr}: {e}")
                else:
                    # Try a more forgiving approach if the regex didn't match
                    parts = addr.split('@')
                    if len(parts) == 2 and '.' in parts[1]:
                        # Looks like a valid email
                        email_addr = addr.strip()
                        try:
                            email_obj = EmailAddress(email=email_addr)
                            entity = Entity(
                                name=email_addr,  # Use email as name
                                email=email_obj,
                                is_physical_person=True
                            )
                            entities.append(entity)

                        except Exception as e:
                            logging.error(f"Error creating Entity for fallback email {email_addr}: {e}")

                    # We consider it's not a mail address but an indicator of the receiver name for now.
                    # This is a fallback for email sent from our adress that lost it's mail address
                    name = addr.strip()
                    try:
                        email_obj = EmailAddress(email="unknown@example.com")
                        entity = Entity(
                            name=name,  # Use email as name
                            email=email_obj,
                            is_physical_person=True
                        )

                        entities.append(entity)
                    except Exception as e:
                        logging.error(f"Error creating Entity with name only and no mail adress; {email_addr}: {e}")


            except Exception as e:
                logging.error(f"Error parsing address '{addr}': {e}")
    except Exception as e:
        logging.error(f"Error parsing addresses string '{address_str}': {e}")

    return entities


def decode_str(s):
    """Decode encoded email header strings"""
    if s is None:
        return ""
    try:
        decoded_parts = decode_header(s)
        return ''.join([
            part.decode(encoding or 'utf-8', errors='replace') if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        ])
    except:
        return str(s)

def extract_clean_text_from_html(html_content):
    """
    Extract clean, readable text from HTML content.

    Args:
        html_content (str): HTML content to clean

    Returns:
        str: Clean text without HTML tags
    """
    if not html_content:
        return ""

    try:
        # Remove scripts, styles, and other tags that contain content we don't want
        html_content = re.sub(r'<(script|style|head).*?>.*?</\1>', ' ', html_content, flags=re.DOTALL)

        # Replace common block elements with newlines to preserve structure
        html_content = re.sub(r'</(p|div|h\d|tr|li)>', '\n', html_content)
        html_content = re.sub(r'<br[^>]*>', '\n', html_content)

        # Replace table cells with tab separation
        html_content = re.sub(r'</td>', '\t', html_content)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)

        # Decode HTML entities (&nbsp;, &lt;, etc.)
        text = html.unescape(text)

        # Handle literal escape sequences that appear in the text
        # Replace literal "\xad" with empty string (remove soft hyphens)
        text = text.replace('\\xad', '')
        # Replace literal "\xa0" with a space (non-breaking spaces)
        text = text.replace('\\xa0', ' ')

        # Handle actual Unicode characters too
        # Remove soft hyphens (invisible hyphens used for word breaks)
        text = text.replace('\xad', '')
        # Replace non-breaking spaces with regular spaces
        text = text.replace('\xa0', ' ')
        # Remove other problematic control characters
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

        # Clean up other escape sequences that might appear in text
        text = text.replace('\\\\', '\\')  # Double backslash to single
        text = text.replace("\\'", "'")    # Escaped single quote
        text = text.replace('\\"', '"')    # Escaped double quote
        text = text.replace('\\n', '\n')   # Literal \n to newline
        text = text.replace('\\t', '\t')   # Literal \t to tab

        # Remove remaining literal escape sequences like \x.. that weren't handled above
        text = re.sub(r'\\x[0-9a-fA-F]{2}', '', text)

        # Clean up whitespace (multiple spaces, tabs, newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Final cleanup to remove leading/trailing whitespace
        return text.strip()
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return f"Error processing HTML content: {str(e)}"



def get_email_body(message):
    """Extract body text from email message, handling HTML correctly"""
    body_text = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue

                charset = part.get_content_charset() or 'utf-8'
                decoded_payload = payload.decode(charset, errors='replace')

                body_text += decoded_payload
            except:
                continue
    else:
        # Not multipart - get payload directly
        try:
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or 'utf-8'
                decoded_payload = payload.decode(charset, errors='replace')

                body_text = decoded_payload
        except:
            pass

    # Prefer HTML content but fall back to plain text

    #####body

    return {
        "text": clean_html(body_text),
    }

def extract_attachments_info(message):
    """Extract information about attachments with better error handling"""
    attachments = []

    if not message.is_multipart():
        return attachments

    try:
        for part in message.walk():
            try:
                content_disposition = str(part.get("Content-Disposition") or "")

                if "attachment" in content_disposition:
                    try:
                        filename = part.get_filename()
                        if filename:
                            try:
                                filename = decode_str(filename)
                            except Exception as e:
                                print(f"Error decoding attachment filename: {e}")
                                filename = "unknown_filename"
                        else:
                            filename = "unnamed_attachment"

                        content_type = part.get_content_type() or 'application/octet-stream'

                        # Get content safely
                        try:
                            content = part.get_payload(decode=True)
                            # Ensure content is bytes
                            if content is None:
                                content = b''
                            elif not isinstance(content, bytes):
                                content = str(content).encode('utf-8', errors='replace')
                        except Exception as e:
                            print(f"Error getting attachment content: {e}")
                            content = b''

                        size = len(content)

                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": size,
                            "content": content
                        })
                    except Exception as e:
                        print(f"Error processing individual attachment: {e}")
            except Exception as e:
                print(f"Error walking email part: {e}")
    except Exception as e:
        print(f"Error in attachment extraction: {e}")

    return attachments

def extract_recipients(message):
    """Extract all recipients (To, CC, BCC) as Entity objects with better error handling"""
    to_str = decode_str(message.get('to') or "")
    cc_str = decode_str(message.get('cc') or "")
    bcc_str = decode_str(message.get('bcc') or "")
    reply_to_str = decode_str(message.get('reply-to') or "")

    # Parse with error handling
    try:
        to_entities = parse_email_address(to_str)
    except Exception as e:
        print(f"Error parsing 'to' field: {e}, value: {to_str}")
        to_entities = []

    try:
        cc_entities = parse_email_address(cc_str)
    except Exception as e:
        print(f"Error parsing 'cc' field: {e}, value: {cc_str}")
        cc_entities = []

    try:
        bcc_entities = parse_email_address(bcc_str)
    except Exception as e:
        print(f"Error parsing 'bcc' field: {e}, value: {bcc_str}")
        bcc_entities = []

    reply_to_entity = None
    try:
        reply_to_entities = parse_email_address(reply_to_str)
        if reply_to_entities and len(reply_to_entities) > 0:
            reply_to_entity = reply_to_entities[0]
    except Exception as e:
        print(f"Error parsing 'reply-to' field: {e}, value: {reply_to_str}")

    return {
        "to": to_entities,
        "cc": cc_entities,
        "bcc": bcc_entities,
        "reply_to": reply_to_entity
    }

def extract_message_data(message, folder_name, config_file, mailbox_name="Boîte mail de Céline", project_name: Optional[str] = None):
    if project_name is None:
        project_name = os.getenv("ACTIVE_PROJECT") or getattr(constants, "ACTIVE_PROJECT", "Projet Demo")
    """Extract comprehensive email data to match Pydantic models"""
    # Generate a unique ID
    email_id = str(uuid.uuid4())

    # Extract basic headers
    subject = decode_str(message.get('subject') or "")
    from_str = decode_str(message.get('from') or "")
    date_str = message.get('date')
    message_id = decode_str(message.get('message-id') or "")
    in_reply_to = decode_str(message.get('in-reply-to') or "")
    references = decode_str(message.get('references') or "")
    mailbox_name = mailbox_name # config_file[project_name]["mailbox"][mailbox_name]["mailbox_name"]

    # Parse date
    try:
        timestamp = email.utils.parsedate_to_datetime(date_str)
    except:
        timestamp = datetime.datetime.now()  # Fallback to current time

    # Get sender entity
    try:
        sender_entities = parse_email_address(from_str)

        if sender_entities and len(sender_entities) > 0:
            sender_entity = sender_entities[0]
        else:
            # Create a fallback entity if parsing failed
            sender_entity = Entity(
                name="Unknown",
                email=EmailAddress(email="unknown@example.com"),
                is_physical_person=True
            )
    except Exception as e:
        print(f"Error parsing sender: {e}, from_str: {from_str}")
        sender_entity = Entity(
            name="Unknown",
            email=EmailAddress(email="unknown@example.com"),
            is_physical_person=True
        )

    # Get recipients
    try:
        recipients = extract_recipients(message)
    except Exception as e:
        print(f"Error extracting recipients: {e}")
        # Create empty recipients if extraction fails
        recipients = {
            "to": [],
            "cc": [],
            "bcc": [],
            "reply_to": None
        }

    # Get body content
    try:
        body_content = get_email_body(message)
    except Exception as e:
        print(f"Error extracting body: {e}")
        body_content = {"text": ""},


    # Get attachment info with careful error handling
    attachments = []
    try:
        attachments_data = extract_attachments_info(message)
        for att in attachments_data:
            if "filename" in att and att["filename"]:
                try:
                    # Create a safe version of the content
                    content = att.get("content", b'')
                    if not isinstance(content, bytes):
                        content = b''

                    attachment = Attachment(
                        filename=att["filename"],
                        content=content
                    )

                    # Add optional metadata safely
                    attachment.content_type = att.get('content_type', 'application/octet-stream')
                    attachment.size = att.get('size', len(content))

                    attachments.append(attachment)
                except Exception as e:
                    print(f"Error creating attachment object: {e}")
    except Exception as e:
        print(f"Error extracting attachments: {e}")

    # Check if this is potentially a mailing list
    list_id = decode_str(message.get('list-id') or "")
    list_unsubscribe = decode_str(message.get('list-unsubscribe') or "")
    is_mailing_list = bool(list_id or list_unsubscribe)

    # Create a mailing list object if applicable
    mailing_list = None
    if is_mailing_list and list_id:
        try:
            # Extract name from list-id which often looks like "List Name <listname.example.com>"
            # list_name_match = re.search(r'<([^>]+)>|([^,\s]+)', list_id)
            # list_name = list_name_match.group(1) if list_name_match else "Unknown List"
            list_name_match = re.search(r'<([^>]+)>|([^,\s]+)', list_id)

            if list_name_match:
                # Check both capture groups
                list_name = list_name_match.group(1) or list_name_match.group(2) or "Unknown List"
            else:
                list_name = "Unknown List"

            # Try to find a list email address
            list_email = "list@example.com"  # Default
            list_email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', list_unsubscribe)
            if list_email_match:
                list_email = list_email_match.group(1)

            mailing_list = MailingList(
                id=str(uuid.uuid4()),
                name=list_name,
                description=f"Mailing list extracted from {list_id}",
                email_address=EmailAddress(email=list_email)
            )
        except Exception as e:
            print(f"Error creating mailing list: {e}")

    # Create a SenderEmail object
    sender_email_id = str(uuid.uuid4())
    sender_email = SenderEmail(
        id=sender_email_id,
        sender=sender_entity,
        body=body_content["text"],
        timestamp=timestamp
    )

    # Create a ReceiverEmail object - safely handle the recipients
    receiver_email = ReceiverEmail(
        id=email_id,
        sender_email=sender_email,
        sender=sender_entity,
        to=recipients.get("to") if recipients.get("to") else None,
        reply_to=recipients.get("reply_to"),
        cc=recipients.get("cc") if recipients.get("cc") else None,
        bcc=recipients.get("bcc") if recipients.get("bcc") else None,
        mailbox_name=mailbox_name,
        direction = determine_email_direction(message, config_file, project_name, mailbox_name),
        timestamp=timestamp,
        subject=subject,
        body=body_content["text"],
        attachments=attachments if attachments else None,
        is_deleted=False,
        folder=folder_name,
        is_spam=False,
        mailing_list=mailing_list,
        importance_score=0,  # Default value
        mother_email=None,  # Will be linked later based on in_reply_to
        children_emails=None
    )

    # Create a data dictionary for our normalized database tables
    email_data = {
        'id': email_id,
        'sender_email_id': sender_email.id,
        'sender_id': None,  # Will be filled in by the processing function
        'reply_to_id': None,  # Will be filled in by the processing function
        'timestamp': timestamp,
        'subject': subject,
        'body': body_content["text"],
        'is_deleted': False,
        'folder': folder_name,
        'is_spam': False,
        'mailing_list_id': mailing_list.id if mailing_list else None,
        'importance_score': 0,
        'mother_email_id': None,  # Will be updated later based on in_reply_to
        'message_id': message_id,
        'references': references,
        'in_reply_to': in_reply_to
    }

    return email_data, receiver_email




def collect_email_data(directory: Union[str, Path],
                       mailbox_name:str ="Boîte mail de Céline",
                       project_name: Optional[str] = None,
                       include_attachments: bool = True) -> List[Dict[str, Any]]:
    """
    Recursively process all .eml files in the directory and its subdirectories
    and return a list of email data.

    Args:
        directory: Root directory to search for .eml files
        include_html: Whether to include HTML content in the email data
        include_attachments: Whether to include attachment information

    Returns:
        List of dictionaries containing extracted email data
    """

    project_name = project_name or os.getenv("ACTIVE_PROJECT") or getattr(constants, "ACTIVE_PROJECT", "Projet Demo")

    config_path = Path(project_root) / "data" / "Projects" / project_name / "project_config_file.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config_file = json.load(f)

    all_emails = []
    directory = Path(directory)  # Convert to Path object if it's a string

    # Find all .eml files recursively
    eml_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.eml'):
                eml_files.append(Path(root) / file)

    print(f"Found {len(eml_files)} .eml files")

    # Process each file
    for eml_path in tqdm(eml_files, desc="Processing emails"):
        # Determine folder structure relative to the root directory
        rel_path = eml_path.relative_to(directory)
        folder_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'

        try:
            # Parse the email file
            with open(eml_path, 'rb') as f:
                message = email.message_from_binary_file(f, policy=policy.default)

            email_data = extract_message_data(message, folder_name, config_file, mailbox_name, project_name)

            # Add the file path for reference
            email_data['file_path'] = str(eml_path)

            # Optionally simplify attachment info to reduce data size
            if not include_attachments:
                email_data['attachment_count'] = len(email_data.get('attachments', []))
                email_data.pop('attachments', None)

            all_emails.append(email_data)

        except Exception as e:
            print(f"Error processing {eml_path}: {e}")

    return all_emails


def determine_email_direction(message, config_file, project_name: str, mailbox_name: str) -> str:
    """
    Determine if an email was sent from or received in the mailbox.

    Args:
        message: The email message object (from email.message module)
        config_file: The configuration file containing mailbox information
        project_name: The name of the project in the config file
        mailbox_name: The name of the mailbox in the config file

    Returns:
        str: "sent" or "received"
    """
    # Extract the owner's main email and aliases from the config file
    try:
        mailbox_config = config_file[project_name]["mailboxs"][mailbox_name]
        main_email = mailbox_config["Entity"]["email_adress"].lower()
        email_aliases = [alias.lower() for alias in mailbox_config["Entity"]["email_adress_aliases"]]

        # Combine main email and aliases into a single list
        mailbox_owner_emails = [main_email] + email_aliases
    except (KeyError, TypeError) as e:
        # Fallback if the config structure doesn't match what we expect
        print(f"Warning: Could not extract emails from config file: {e}")
        mailbox_owner_emails = []

    # Get key headers
    from_header = message.get('from', '')
    folder = message.get('X-Folder', '')
    forensic_sender = message.get('X-libpst-forensic-sender', '')
    received_headers = message.get_all('Received', [])

    # Normalize the from_header for comparison (extract just the email address)
    from_email = None
    if '<' in from_header and '>' in from_header:
        from_email = from_header.split('<')[1].split('>')[0].lower()
    else:
        # For simpler formats, try to extract email using regex
        import re
        email_pattern = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
        match = email_pattern.search(from_header)
        if match:
            from_email = match.group(1).lower()

    # Check if from_email matches any of the mailbox owner emails
    from_is_owner = any(owner_email in from_email for owner_email in mailbox_owner_emails) if from_email and mailbox_owner_emails else False

    # Check indicators for "sent" emails
    sent_indicators = [
        # Check if the sender is one of the mailbox owners
        from_is_owner,

        # Check if it's in a sent folder
        folder and any(sent_term in folder.lower() for sent_term in ['sent', 'envoy', 'outbox']),

        # Check for forensic sender header (often present in sent emails)
        bool(forensic_sender),

        # Check for few received headers (sent emails typically have fewer)
        len(received_headers) <= 2
    ]

    # Check indicators for "received" emails
    received_indicators = [
        # Check if the sender is not one of the mailbox owners
        not from_is_owner and from_email,

        # Check if in inbox or other non-sent folder
        folder and not any(sent_term in folder.lower() for sent_term in ['sent', 'envoy', 'outbox']),

        # Check for multiple received headers (typical of incoming mail)
        len(received_headers) > 2,

        # Check for spam headers (only present in received emails)
        any(header in message for header in ['X-Spam-Status', 'X-Ovh-Spam-Status', 'X-VR-SPAMSTATE']),

        # Check for SPF headers (only present in received emails)
        bool(message.get('Received-SPF'))
    ]

    # Count the positive indicators for each direction
    sent_score = sum(1 for indicator in sent_indicators if indicator)
    received_score = sum(1 for indicator in received_indicators if indicator)

    # Determine direction based on relative strength of indicators
    if sent_score > received_score:
        return "sent"
    elif received_score > sent_score:
        return "received"
    else:
        # If tied, look at the From header as the tie-breaker
        if from_is_owner:
            return "sent"
        else:
            return "received"




#### Main process


def process_eml_to_duckdb(directory: Union[str, Path],
                          conn: 'duckdb.DuckDBPyConnection',
                          batch_size: int = 100,
                          mailbox_name: str = "Boîte mail de Céline",
                          project_name: Optional[str] = None,
                          entity_cache: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Recursively process all .eml files in a directory and its subdirectories directly to DuckDB in batches

    Args:
        directory: Root directory to search for .eml files
        conn: DuckDB connection
        batch_size: Number of records to process before committing to the database
        entity_cache: Cache to store entities we've already seen

    Returns:
        Updated entity cache after processing
    """

    project_name = project_name or os.getenv("ACTIVE_PROJECT") or getattr(constants, "ACTIVE_PROJECT", "Projet Demo")

    config_path = Path(project_root) / "data" / "Projects" / project_name / "project_config_file.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config_file = json.load(f)

    if entity_cache is None:
        entity_cache = {}  # Cache to store entities we've already seen

    directory = Path(directory)  # Convert to Path object if it's a string

    # Find all .eml files recursively
    eml_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.eml'):
                eml_files.append(Path(root) / file)

    print(f"Found {len(eml_files)} .eml files to process")

    # Process in batches for each table
    entity_batch = []
    entity_alias_emails_batch = []
    mailing_list_batch = []
    sender_email_batch = []
    receiver_email_batch = []
    to_recipients_batch = []
    cc_recipients_batch = []
    bcc_recipients_batch = []
    attachments_batch = []

    # Process each .eml file
    for i, eml_path in enumerate(tqdm(eml_files, desc="Processing emails")):
        # Determine folder structure relative to the root directory
        rel_path = eml_path.relative_to(directory)
        folder_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'

        try:
            # Parse the email file
            with open(eml_path, 'rb') as f:
                message = email.message_from_binary_file(f, policy=policy.default)
            email_data, receiver_email = extract_message_data(message, folder_name, config_file, mailbox_name, project_name)

            # Process sender entity
            sender = receiver_email.sender

            if sender.email.email not in entity_cache:
                entity_id = str(uuid.uuid4())
                entity_cache[sender.email.email] = entity_id

                # Add to entities batch
                entity_batch.append({
                    'id': entity_id,
                    'name': sender.name,
                    'email': sender.email.email,
                    'alias_names': json.dumps(sender.alias_names) if sender.alias_names else None,
                    'alias_emails': json.dumps(sender.alias_emails) if sender.alias_names else None,
                    'is_physical_person': sender.is_physical_person
                })

                # Process alias emails if any
                if sender.alias_emails:
                    for alias_email in sender.alias_emails:
                        entity_alias_emails_batch.append({
                            'id': str(uuid.uuid4()),
                            'entity_id': entity_id,
                            'email': alias_email.email
                        })
            else:
                # Get cached entity ID
                entity_id = entity_cache[sender.email.email]

            # Process sender email
            sender_email = receiver_email.sender_email
            sender_email_batch.append({
                'id': sender_email.id,
                'sender_id': entity_id,  # Use cached or new entity ID
                'body': sender_email.body,
                'timestamp': sender_email.timestamp
            })

            # Process receiver email
            reply_to_id = None
            if receiver_email.reply_to:
                reply_to_email = receiver_email.reply_to.email.email
                if reply_to_email not in entity_cache:
                    reply_to_id = str(uuid.uuid4())
                    entity_cache[reply_to_email] = reply_to_id

                    entity_batch.append({
                        'id': reply_to_id,
                        'name': receiver_email.reply_to.name,
                        'email': reply_to_email,
                        'alias_names': None,
                        'alias_emails': None,
                        'is_physical_person': True # can be changed later based on if list diffusion or not
                    })
                else:
                    reply_to_id = entity_cache[reply_to_email]

            # Add mailing list if present
            mailing_list_id = None
            if receiver_email.mailing_list:
                mailing_list_id = receiver_email.mailing_list.id
                mailing_list_batch.append({
                    'id': mailing_list_id,
                    'name': receiver_email.mailing_list.name,
                    'description': receiver_email.mailing_list.description,
                    'email_address': receiver_email.mailing_list.email_address.email
                })

            # Add receiver email
            receiver_email_batch.append({
                'id': receiver_email.id,
                'sender_email_id': sender_email.id,
                'sender_id': entity_id,
                'reply_to_id': reply_to_id,
                'mailbox_name': mailbox_name,
                'direction': receiver_email.direction,
                'timestamp':receiver_email.timestamp.strftime('%Y-%m-%d %H:%M:%S'), # 'timestamp': receiver_email.timestamp,
                'subject': receiver_email.subject,
                'body': receiver_email.body,
                'is_deleted': receiver_email.is_deleted,
                'folder': folder_name,  # Using the relative folder path as folder name
                'is_spam': receiver_email.is_spam,
                'mailing_list_id': mailing_list_id,
                'importance_score': receiver_email.importance_score,
                'mother_email_id': None,  # Will be updated later
                'message_id': email_data.get('message_id'),
                'references': email_data.get('references'),
                'in_reply_to': email_data.get('in_reply_to')
            })

            # Process recipients (to, cc, bcc) #
            if receiver_email.to:
                for entity in receiver_email.to:
                    if entity.email.email not in entity_cache:
                        to_entity_id = str(uuid.uuid4())
                        entity_cache[entity.email.email] = to_entity_id

                        entity_batch.append({
                            'id': to_entity_id,
                            'name': entity.name,
                            'email': entity.email.email,
                            'alias_names': json.dumps(entity.alias_names) if entity.alias_names else None,
                            'alias_emails': json.dumps(sender.alias_emails) if sender.alias_names else None,
                            'is_physical_person': entity.is_physical_person
                        })

                        # Process alias emails
                        if entity.alias_emails:
                            for alias_email in entity.alias_emails:
                                entity_alias_emails_batch.append({
                                    'id': str(uuid.uuid4()),
                                    'entity_id': to_entity_id,
                                    'email': alias_email.email
                                })
                    else:
                        to_entity_id = entity_cache[entity.email.email]

                    # Add to recipients relationship
                    to_recipients_batch.append({
                        'email_id': receiver_email.id,
                        'entity_id': to_entity_id
                    })

            # Process CC recipients
            if receiver_email.cc:
                for entity in receiver_email.cc:
                    if entity.email.email not in entity_cache:
                        cc_entity_id = str(uuid.uuid4())
                        entity_cache[entity.email.email] = cc_entity_id

                        entity_batch.append({
                            'id': cc_entity_id,
                            'name': entity.name,
                            'email': entity.email.email,
                            'alias_names': json.dumps(entity.alias_names) if entity.alias_names else None,
                            'alias_emails': json.dumps(sender.alias_emails) if sender.alias_names else None,
                            'is_physical_person': entity.is_physical_person
                        })
                    else:
                        cc_entity_id = entity_cache[entity.email.email]

                    # Add cc recipients relationship
                    cc_recipients_batch.append({
                        'email_id': receiver_email.id,
                        'entity_id': cc_entity_id
                    })

            # Process BCC recipients
            if receiver_email.bcc:
                for entity in receiver_email.bcc:
                    if entity.email.email not in entity_cache:
                        bcc_entity_id = str(uuid.uuid4())
                        entity_cache[entity.email.email] = bcc_entity_id

                        entity_batch.append({
                            'id': bcc_entity_id,
                            'name': entity.name,
                            'email': entity.email.email,
                            'alias_names': json.dumps(entity.alias_names) if entity.alias_names else None,
                            'alias_emails': json.dumps(sender.alias_emails) if sender.alias_names else None,
                            'is_physical_person': entity.is_physical_person
                        })
                    else:
                        bcc_entity_id = entity_cache[entity.email.email]

                    # Add bcc recipients relationship
                    bcc_recipients_batch.append({
                        'email_id': receiver_email.id,
                        'entity_id': bcc_entity_id
                    })

            # Process attachments
            if receiver_email.attachments:
                for attachment in receiver_email.attachments:
                    content_type = getattr(attachment, 'content_type', 'application/octet-stream')
                    size = getattr(attachment, 'size', len(attachment.content) if attachment.content else 0)

                    attachments_batch.append({
                        'id': str(uuid.uuid4()),
                        'email_id': receiver_email.id,
                        'filename': attachment.filename,
                        'content': attachment.content,
                        'content_type': content_type,
                        'size': size
                    })
        except Exception as e:
            print(f"Error processing email {eml_path}: {e}")
            continue

        # Process batch when it reaches the batch size or on the last file
        if len(receiver_email_batch) >= batch_size or i == len(eml_files) - 1:
            try:
                # Insert entities
                if entity_batch:
                    entities_df = pd.DataFrame(entity_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO entities
                    SELECT * FROM entities_df
                    """)
                    entity_batch = []

                # Insert entity alias emails
                if entity_alias_emails_batch:
                    alias_emails_df = pd.DataFrame(entity_alias_emails_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO entity_alias_emails
                    SELECT * FROM alias_emails_df
                    """)
                    entity_alias_emails_batch = []

                # Insert mailing lists
                if mailing_list_batch:
                    mailing_lists_df = pd.DataFrame(mailing_list_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO mailing_lists
                    SELECT * FROM mailing_lists_df
                    """)
                    mailing_list_batch = []

                # Insert sender emails
                if sender_email_batch:
                    sender_emails_df = pd.DataFrame(sender_email_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO sender_emails
                    SELECT * FROM sender_emails_df
                    """)
                    sender_email_batch = []

                # Insert receiver emails
                if receiver_email_batch:
                    receiver_emails_df = pd.DataFrame(receiver_email_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO receiver_emails
                    SELECT * FROM receiver_emails_df
                    """)
                    receiver_email_batch = []

                # Insert recipient relationships
                if to_recipients_batch:
                    to_recipients_df = pd.DataFrame(to_recipients_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO email_recipients_to
                    SELECT * FROM to_recipients_df
                    """)
                    to_recipients_batch = []

                if cc_recipients_batch:
                    cc_recipients_df = pd.DataFrame(cc_recipients_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO email_recipients_cc
                    SELECT * FROM cc_recipients_df
                    """)
                    cc_recipients_batch = []

                if bcc_recipients_batch:
                    bcc_recipients_df = pd.DataFrame(bcc_recipients_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO email_recipients_bcc
                    SELECT * FROM bcc_recipients_df
                    """)
                    bcc_recipients_batch = []

                # Insert attachments
                if attachments_batch:
                    attachments_df = pd.DataFrame(attachments_batch)
                    conn.execute("""
                    INSERT OR IGNORE INTO attachments
                    SELECT * FROM attachments_df
                    """)
                    attachments_batch = []

                # Commit to save progress
                conn.commit()
            except Exception as e:
                print(f"Error inserting batch into database: {e}")
                # Continue processing even if one batch fails
                entity_batch = []
                entity_alias_emails_batch = []
                mailing_list_batch = []
                sender_email_batch = []
                receiver_email_batch = []
                to_recipients_batch = []
                cc_recipients_batch = []
                bcc_recipients_batch = []
                attachments_batch = []

    print(f"Completed processing {len(eml_files)} .eml files")

    return entity_cache




def process_eml_files(directory: Union[str, Path],
                     output_path: Optional[str] = None) -> None:
    """
    Recursively process .eml files from a directory and its subdirectories and save to DuckDB format
    with normalized tables

    Args:
        directory: Directory containing .eml files (may be nested in subdirectories)
        output_path: Output file path (default: emails.duckdb)
    """
    # Set default output path if not provided
    if output_path is None:
        output_path = 'emails.duckdb'
    elif not output_path.endswith('.duckdb'):
        output_path = f"{output_path}.duckdb"

    # Setup database
    conn = setup_database(output_path)

    # Convert directory to Path if it's a string
    directory = Path(directory)

    # Entity cache to avoid duplicates across files
    entity_cache = {}

    try:
        # Process all .eml files in the directory and subdirectories
        print(f"Processing .eml files in {directory} and subdirectories...")
        entity_cache = process_eml_to_duckdb(directory, conn, entity_cache=entity_cache)
    except Exception as e:
        print(f"Error processing directory {directory}: {e}")

    try:
        # Create relationships between emails (mother/child relationships)
        print("Creating email thread relationships...")
        conn.execute("""
        UPDATE receiver_emails
        SET mother_email_id = (
            SELECT r2.id
            FROM receiver_emails r2
            WHERE r2.message_id = receiver_emails.in_reply_to
            LIMIT 1
        )
        WHERE in_reply_to IS NOT NULL
        """)

        # Populate the children relationships table
        print("Populating child email relationships...")
        conn.execute("""
        INSERT INTO email_children (parent_id, child_id)
        SELECT mother_email_id, id
        FROM receiver_emails
        WHERE mother_email_id IS NOT NULL
        AND mother_email_id IN (SELECT id FROM receiver_emails)
        AND id != mother_email_id  -- Prevent self-references
        """)
    except Exception as e:
        print(f"Warning: Error in relationship creation: {e}")
        print("Continuing with database optimization...")

    # Final optimization and cleanup
    print("Optimizing database...")


    conn.execute("PRAGMA enable_optimizer") # conn.execute("PRAGMA optimize_database")
    conn.close()

    print(f"DuckDB database saved to {output_path}")

def generate_duck_db() -> str | bool:
    active_project = os.getenv("ACTIVE_PROJECT") or getattr(constants, "ACTIVE_PROJECT", "Projet Demo")
    db_path = os.path.join(project_root, "data", "Projects", active_project, f"{active_project}.duckdb")
    eml_folder_path = os.path.join(project_root, "data", "Projects", active_project)

    try:
        setup_database(db_path) # duckdb_conn =
        process_eml_files(eml_folder_path, db_path)
        return db_path
    except Exception as e:
        print(f"Error generating DuckDB: {e}")
        return False



if __name__ == "__main__":
    generate_duck_db()
    ## Set up argument parser
    # parser = argparse.ArgumentParser(description='Process EML files into a DuckDB database')
    # parser.add_argument('path_to_eml', nargs='?', default="data/processed/celine_readpst_with_S",
    #                     help='Path to the directory containing EML files')
    # parser.add_argument('path_for_db', nargs='?', default="data/Projects/Boîte mail de Céline/celine.duckdb",
    #                     help='Path where the DuckDB file should be created')

    # # Parse arguments
    # args = parser.parse_args()

    # # Process the files using the provided arguments
    # process_eml_files(args.path_to_eml, args.path_for_db)
