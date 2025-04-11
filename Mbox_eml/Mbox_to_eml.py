import mailbox
import os
import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import shutil

def mbox_to_eml(mbox_file, output_dir):
    mbox = mailbox.mbox(mbox_file)
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Iterate through each message in the MBOX file
    for i, message in enumerate(mbox):
        eml_filename = f"{output_dir}/message_{i + 1}.eml"
        
        # Save each message as an EML file
        with open(eml_filename, 'wb') as eml_file:
            eml_file.write(message.as_bytes())




    for i,filename in enumerate( os.listdir(output_dir)):
        # Create the full file path
        file_path = os.path.join(output_dir, filename)
        
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            # Path to the EML file you want to read
        
            eml_file_path = file_path
            
            # Read the EML file
            with open(eml_file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            
            # Print basic information about the email
            
            
            # Extract the body of the email
            # If the email is multi-part, get the plain text or HTML part
            if msg.is_multipart():
                for part in msg.iter_parts():
                    if part.get_content_type() == "text/plain":  # Get plain text part
                        body = part.get_payload(decode=True).decode(part.get_content_charset())
                    elif part.get_content_type() == "text/html":  # Get HTML part
                        html_body = part.get_payload(decode=True).decode(part.get_content_charset())
                       
            else:
                # If it's a simple email (not multipart), extract the body directly
                body = msg.get_payload(decode=True).decode(msg.get_content_charset())
            
            soup = BeautifulSoup(html_body, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
           
            save_attachments(msg,i+1,filename)
    is_empty_dir()    
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
def is_empty_dir():
    parent_dir = "attachments"

    # Loop through each item in the parent directory
    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        
        # Check if it's a directory
        if os.path.isdir(item_path):
            # Print the directory name and the count of its contents
            
            if len(os.listdir(item_path)) == 0:
                # Remove the empty directory
                os.rmdir(item_path)