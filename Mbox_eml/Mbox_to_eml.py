import mailbox
import os
import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup

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

    print(f"Conversion complete. {i + 1} messages saved to {output_dir}/")



    for filename in os.listdir(output_dir):
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
            print("Subject:", msg['subject'])
            print("From:", msg['from'])
            print("To:", msg['to'])
            print("Date:", msg['date'])
            
            # Extract the body of the email
            # If the email is multi-part, get the plain text or HTML part
            if msg.is_multipart():
                for part in msg.iter_parts():
                    if part.get_content_type() == "text/plain":  # Get plain text part
                        body = part.get_payload(decode=True).decode(part.get_content_charset())
                        print("Body (Plain Text):", body)
                    elif part.get_content_type() == "text/html":  # Get HTML part
                        html_body = part.get_payload(decode=True).decode(part.get_content_charset())
                        print("Body (HTML):", html_body)
            else:
                # If it's a simple email (not multipart), extract the body directly
                body = msg.get_payload(decode=True).decode(msg.get_content_charset())
                print("Body:", body)
                
            soup = BeautifulSoup(html_body, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            print(text)