import mailbox
import os
import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
import shutil

def mbox_to_eml(mbox_file, output_dir):
    """
    Convert a single MBOX file to individual EML files.

    Args:
        mbox_file (str): Path to the MBOX file
        output_dir (str): Directory where EML files will be saved

    Returns:
        int: Number of emails extracted
    """
    mbox = mailbox.mbox(mbox_file)

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    email_count = 0

    # Iterate through each message in the MBOX file
    for i, message in enumerate(mbox):
        eml_filename = f"{output_dir}/message_{i + 1}.eml"

        # Save each message as an EML file
        with open(eml_filename, 'wb') as eml_file:
            eml_file.write(message.as_bytes())

        email_count += 1

    print(f"Extracted {email_count} emails from {mbox_file} to {output_dir}")
    return email_count


def convert_folder_mbox_to_eml(input_folder, output_folder):
    """
    Convert all MBOX files from a folder to EML files in the output folder.

    Args:
        input_folder (str): Path to the folder containing MBOX files
        output_folder (str): Root directory where EML files will be organized

    Returns:
        dict: Summary of conversion results
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input folder does not exist: {input_folder}")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    results = {
        'total_mbox_files': 0,
        'total_emails_extracted': 0,
        'processed_files': [],
        'errors': []
    }

    # Find all MBOX files in the input folder
    mbox_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.mbox') or file.endswith('.mbox.gz'):
                mbox_files.append(os.path.join(root, file))

    print(f"Found {len(mbox_files)} MBOX files to process")

    for mbox_file in mbox_files:
        try:
            # Create a subdirectory for each MBOX file
            mbox_filename = os.path.splitext(os.path.basename(mbox_file))[0]
            mbox_output_dir = os.path.join(output_folder, mbox_filename)

            # Convert the MBOX file
            email_count = mbox_to_eml(mbox_file, mbox_output_dir)

            # Update results
            results['total_mbox_files'] += 1
            results['total_emails_extracted'] += email_count
            results['processed_files'].append({
                'mbox_file': mbox_file,
                'output_dir': mbox_output_dir,
                'email_count': email_count
            })

        except Exception as e:
            error_msg = f"Error processing {mbox_file}: {str(e)}"
            print(error_msg)
            results['errors'].append(error_msg)

    print(f"\nConversion completed:")
    print(f"- Processed {results['total_mbox_files']} MBOX files")
    print(f"- Extracted {results['total_emails_extracted']} emails total")
    if results['errors']:
        print(f"- {len(results['errors'])} errors occurred")

    return results


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
    """Remove empty directories from attachments folder."""
    parent_dir = "attachments"

    if not os.path.exists(parent_dir):
        return

    # Loop through each item in the parent directory
    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)

        # Check if it's a directory
        if os.path.isdir(item_path):
            if len(os.listdir(item_path)) == 0:
                # Remove the empty directory
                os.rmdir(item_path)
                print(f"Removed empty directory: {item_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single MBOX conversion:")
        print("    python mbox_to_eml.py <mbox_file> <output_dir>")
        print("  Batch folder conversion:")
        print("    python mbox_to_eml.py --batch <input_folder> <output_folder>")
        sys.exit(1)

    if sys.argv[1] == "--batch":
        if len(sys.argv) != 4:
            print("Batch mode requires input_folder and output_folder")
            sys.exit(1)

        input_folder = sys.argv[2]
        output_folder = sys.argv[3]

        print(f"Converting all MBOX files from {input_folder} to {output_folder}")
        results = convert_folder_mbox_to_eml(input_folder, output_folder)

        if results['errors']:
            print(f"\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
    else:
        mbox_file = sys.argv[1]
        output_dir = sys.argv[2]

        print(f"Converting {mbox_file} to {output_dir}")
        email_count = mbox_to_eml(mbox_file, output_dir)
        print(f"Successfully extracted {email_count} emails")