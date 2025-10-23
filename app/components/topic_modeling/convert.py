import mailbox
import json


def convert_mbox_to_json(email_mbox,email_json):
    # Load the MBOX file
    mbox = mailbox.mbox(email_mbox)
    
    # Extract the email data into a dictionary format
    emails = []
    for message in mbox:
        email_data = {
            'from': message['From'],
            'to': message['To'],
            'subject': message['Subject'],
            'date': message['Date'],
            'body': message.get_payload(decode=True).decode('utf-8', 'ignore') if message.is_multipart() else message.get_payload()
        }
        emails.append(email_data)
    
    # Optionally, you can save the extracted emails as JSON
    with open(email_json, 'w', encoding='utf-8') as f:
        json.dump(emails, f, ensure_ascii=False, indent=4)
