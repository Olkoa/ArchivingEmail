import subprocess

def convert_pst_to_mbox(pst_file_path: str, output_path: str):
    """
    Calls the readpst CLI command to convert a PST file to MBOX format.
    Continues to the next step once completed.
    """
    try:
        # Construct the command
        command = [
            "readpst",
            "-j", "0",  # Disable multithreading
            "-e",       # Extract attachments
            "-o", output_path,  # Output directory
            pst_file_path       # Input PST file
        ]

        # Run the command and wait for it to finish
        subprocess.run(command, check=True)
        print(f"Successfully converted PST file: {pst_file_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error running readpst: {e}")
    except FileNotFoundError:
        print("readpst not found. Make sure it is installed and in your PATH.")


# Example usage
# convert_pst_to_mbox("emails.pst", "./output")

if __name__ == "__main__":
    pass
