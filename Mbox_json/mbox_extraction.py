import mailbox
from bs4 import BeautifulSoup
import os
import json

# Open the mbox file
def extract_from_mbox(boxname):
    
    box=boxname
    mbox = mailbox.mbox(f'mbox/{box}')
    emails_data = []
    
    # Loop through the messages
    for i, message in enumerate(mbox):
        email_data = {
            "subject": message['subject'],
            "from": message['from'],
            "to": message['to'],
            "date": message['date'],
            "body": "",
            "attachments": []
        }
    
        # Extract body
        try:
            html_body = getBody(message)
            soup = BeautifulSoup(html_body, 'html.parser')
            email_data["body"] = soup.get_text()
        except Exception as e:
            email_data["body"] = "[Error reading body]"
    
        # Save and record attachments
        email_data["attachments"] = save_attachments(message, i + 1,boxname)
    
        # Append to list
        emails_data.append(email_data)
    # The directory path you want to ensure exists
    directory = "json/"
    
    # Check if the directory exists, if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Save all to JSON
    with open(f"{directory}/{box}.json", "w", encoding="utf-8") as f:
        json.dump(emails_data, f, indent=2, ensure_ascii=False)
    
    

    
def getcharsets(msg):
    charsets = set({})
    for c in msg.get_charsets():
        if c is not None:
            charsets.update([c])
    return charsets

def getBody(msg):
    while msg.is_multipart():
        msg = msg.get_payload()[0]
    t = msg.get_payload(decode=True)
    for charset in getcharsets(msg):
        try:
            t = t.decode(charset)
        except:
            pass
    return t

def save_attachments(msg, email_index, boxname):
    output_dir=f"attachments/{boxname}"
    os.makedirs(output_dir, exist_ok=True)
    attachments = []

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                safe_filename = f"{email_index}_{filename}"
                file_path = os.path.join(output_dir, safe_filename)
                with open(file_path, "wb") as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(file_path)
    return attachments
