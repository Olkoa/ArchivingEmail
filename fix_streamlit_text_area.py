import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the path to the email_viewer.py file
email_viewer_path = os.path.join('app', 'components', 'email_viewer.py')

# Function to fix the text_area height issue
def fix_text_area_height(file_path):
    try:
        # Read the current content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if the file contains the problematic code
        pattern = r'height=min\(len\(decoded_body\.splitlines\(\)\) \* 16, 180\)'
        if not re.search(pattern, content):
            print(f"The specific code pattern was not found in {file_path}")
            return False
        
        # Replace the height calculation to ensure minimum height of 68px
        fixed_content = re.sub(
            pattern,
            'height=max(min(len(decoded_body.splitlines()) * 16, 180), 68)',
            content
        )
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(fixed_content)
        
        print(f"Successfully fixed the text_area height issue in {file_path}")
        return True
    
    except Exception as e:
        print(f"Error fixing the text_area height issue: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Looking for email_viewer.py at: {email_viewer_path}")
    
    if os.path.exists(email_viewer_path):
        fix_text_area_height(email_viewer_path)
    else:
        print(f"File not found: {email_viewer_path}")
        
        # Try to find the file using alternative methods
        print("Searching for email_viewer.py in the project directory...")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file == 'email_viewer.py':
                    found_path = os.path.join(root, file)
                    print(f"Found at: {found_path}")
                    fix_text_area_height(found_path)
