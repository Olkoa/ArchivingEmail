"""
File which goal is to setup a new mailbox project from scratch
"""
import sys
import os

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.eml_transformation import generate_duck_db

from src.rag.colbert_initialization import initialize_colbert_rag_system

def main():
    """
    Main function to set up the mailbox project.
    """

    # Make sure the var ACTIVE_PROJECT in the .env file is set to the project name

    # Make sure to create the proper project structure

    # use cli command here "readpst -j 0 -e -o output_path path_to_pst_file "



    # load emls at the proper place

    # create db
    generate_duck_db()

    # generate colbert indexes

    index_dir = initialize_colbert_rag_system(project_root=project_root, force_rebuild=True, test_mode=False)

if __name__ == "__main__":
    main()
