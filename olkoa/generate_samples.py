#!/usr/bin/env python
"""
Generate sample mailboxes for the Okloa project.

This script creates three sample mailboxes, each containing 5 sent and 5 received emails.
The emails are formatted as mbox files and saved in the data/raw directory.
"""

import os
import sys

# Add the current directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.data.sample_generator import generate_test_mailboxes


def main():
    """Main function to generate sample mailboxes."""
    print("Generating sample mailboxes for the Okloa project...")
    
    # Set output directory
    project_root = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Project root: {project_root}")
    print(f"Output directory: {output_dir}")
    
    # Generate mailboxes with 5 sent and 5 received emails each
    generate_test_mailboxes(
        output_dir=output_dir,
        num_sent=5,
        num_received=5,
        format_type="mbox"
    )
    
    print(f"Sample mailboxes generated successfully in {output_dir}")
    print("\nMailbox details:")
    print("- mailbox_1: Marie Durand (Conservateur en chef)")
    print("- mailbox_2: Thomas Berger (Responsable numérisation)")
    print("- mailbox_3: Sophie Martin (Archiviste documentaliste)")
    
    # Print summary of generated data
    directories = [f"mailbox_{i+1}" for i in range(3)]
    total_emails = 0
    
    for directory in directories:
        metadata_path = os.path.join(output_dir, directory, "metadata.json")
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            sent = sum(1 for item in metadata if item["direction"] == "sent")
            received = sum(1 for item in metadata if item["direction"] == "received")
            
            print(f"\n{directory}:")
            print(f"  - Sent emails: {sent}")
            print(f"  - Received emails: {received}")
            
            total_emails += len(metadata)
    
    print(f"\nTotal emails generated: {total_emails}")


if __name__ == "__main__":
    main()