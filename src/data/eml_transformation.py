from ..models.models import EmailAddress, MailingList, Organisation, Position, Entity, Attachment, ReceiverEmail, SenderEmail

from typing import List, Optional, Union, Dict, Any
import re
import html
import logging
from email.header import decode_header
import uuid
import datetime
import email.utils
import os
from pathlib import Path
from tqdm import tqdm
from email import policy

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
        return []

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

        for addr in addresses:
            addr = addr.strip()
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
                                email=email_obj,
                                is_physical_person=True  # Assuming default
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
    body_html = ""

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

                if content_type == "text/plain":
                    body_text += decoded_payload
                elif content_type == "text/html":
                    body_html += decoded_payload
            except:
                continue
    else:
        # Not multipart - get payload directly
        try:
            content_type = message.get_content_type()
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or 'utf-8'
                decoded_payload = payload.decode(charset, errors='replace')

                if content_type == "text/plain":
                    body_text = decoded_payload
                elif content_type == "text/html":
                    body_html = decoded_payload
        except:
            pass

    # Prefer HTML content but fall back to plain text
    if body_html:
        return {
            "html": body_html,
            "text": extract_clean_text_from_html(body_html),
            "has_html": True
        }
    else:
        return {
            "html": "",
            "text": body_text,
            "has_html": False
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

def extract_message_data(message, folder_name):
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
        body_content = {
            "text": "",
            "html": "",
            "has_html": False
        }

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
        'body_html': body_content["html"] if body_content["has_html"] else None,
        'has_html': body_content["has_html"],
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
                       include_html: bool = True,
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

            email_data = extract_message_data(message, folder_name)

            # Add the file path for reference
            email_data['file_path'] = str(eml_path)

            # Optionally exclude HTML content to reduce data size
            if not include_html:
                email_data.pop('body_html', None)

            # Optionally simplify attachment info to reduce data size
            if not include_attachments:
                email_data['attachment_count'] = len(email_data.get('attachments', []))
                email_data.pop('attachments', None)

            all_emails.append(email_data)

        except Exception as e:
            print(f"Error processing {eml_path}: {e}")

    return all_emails
