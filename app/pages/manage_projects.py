"""
Olkoa - Interface de Gestion de Projets

Créez, modifiez et gérez vos projets d’archivage d’e-mails.
Chaque projet peut contenir plusieurs boîtes mail avec des métadonnées sur les personnes et les organisations impliquées.
"""

import ast
import duckdb
import importlib
import os
import re
import json
import shutil
import streamlit as st
import subprocess
import sys
import tempfile
import uuid
import zipfile
from datetime import datetime

from components.logins import make_hashed_password, verify_password, add_user, initialize_users_db

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Get project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DEFAULT_PROJECT_NAME = "Projet Demo"

from dotenv import load_dotenv

import constants
from src.data.s3_utils import S3Handler
from src.data.mbox_to_eml import convert_folder_mbox_to_eml, mbox_to_eml
from src.rag.colbert_initialization import initialize_colbert_rag_system
from src.data.eml_transformation import generate_duck_db


# Page configuration
# st.set_page_config(
#     page_title="Olkoa - Project Management",
#     page_icon="📁",
#     layout="wide",
# )

# Initialize user session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "users_db" not in st.session_state:
    st.session_state.users_db = initialize_users_db()

if 'project_creation_error' not in st.session_state:
    st.session_state.project_creation_error = None

# Login form
def show_login_form():
    st.title("Okloa - Email Archive Analytics")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if verify_password(username, password, st.session_state.users_db):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    # Display demo credentials for testing
    # st.info("""Demo credentials:\n- Username: admin, Password: admin123\n- Username: user, Password: user123""")

    ## Add "Admin Panel" section for creating new users
    # st.subheader("Admin Panel")
    # with st.expander("Create New User"):
    #     with st.form("create_user_form"):
    #         admin_username = st.text_input("Admin Username")
    #         admin_password = st.text_input("Admin Password", type="password")
    #         new_username = st.text_input("New Username")
    #         new_password = st.text_input("New Password", type="password")
    #         confirm_password = st.text_input("Confirm Password", type="password")

    #         create_button = st.form_submit_button("Create User")

    #         if create_button:
    #             # Verify admin credentials
    #             if verify_password(admin_username, admin_password, st.session_state.users_db):
    #                 # Check if passwords match
    #                 if new_password == confirm_password:
    #                     # Add new user
    #                     st.session_state.users_db = add_user(new_username, new_password)
    #                     st.success(f"User '{new_username}' created successfully!")
    #                 else:
    #                     st.error("Passwords do not match!")
    #             else:
    #                 st.error("Invalid admin credentials")

# Page configuration is already set at the top of the file

# Check if authenticated
if not st.session_state.authenticated:
    show_login_form()
else:
    # Custom CSS
    try:
        css_path = os.path.join(os.path.dirname(__file__), '../static/project_manager.css')
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load custom CSS: {e}")
        # Continue without custom CSS

    # Title and description
    st.title("Manage Projects")
    st.markdown("""
        Create, edit, and manage your email archive projects. Each project can contain multiple mailboxes
        with metadata about the people and organizations involved.
    """)

    # Function to find all project config files
    def find_projects():
        projects_dir = os.path.join(project_root, 'data', 'Projects')
        projects = []

        if not os.path.exists(projects_dir):
            os.makedirs(projects_dir)
            return []

        for project_folder in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_folder)
            config_file_path = os.path.join(project_path, 'project_config_file.json')

            if os.path.isdir(project_path) and os.path.exists(config_file_path):
                try:
                    with open(config_file_path, 'r', encoding='utf-8') as file:
                        config_data = json.load(file)
                        project_name = list(config_data.keys())[0]
                        projects.append({
                            'name': project_name,
                            'path': project_path,
                            'config': config_data
                        })
                except Exception as e:
                    st.error(f"Error loading project {project_folder}: {str(e)}")

        # Sort projects based on PROJECT_ORDER in constants.py
        try:
            constants_path = os.path.join(project_root, 'constants.py')
            with open(constants_path, 'r', encoding='utf-8') as file:
                constants_content = file.read()

            # Extract project order
            match = re.search(r'PROJECT_ORDER = \[(.*?)\]', constants_content, re.DOTALL)
            if match:
                order_str = match.group(1)
                # Parse the order into a list
                project_order = [p.strip().strip('"').strip("'") for p in order_str.split(',') if p.strip()]

                # Sort projects based on the order
                def get_project_order(project):
                    project_name = project['name']
                    if project_name in project_order:
                        return project_order.index(project_name)
                    else:
                        # If project is not in the order list, place it at the end
                        return len(project_order)

                projects.sort(key=get_project_order)
        except Exception as e:
            # If there's an error reading the order, just keep the original order
            pass

        return projects

    # Function to create folder structure for a new project
    def create_project_structure(project_name, mailboxes):
        projects_dir = os.path.join(project_root, 'data', 'Projects')
        project_path = os.path.join(projects_dir, project_name)

        # Create project folder if it doesn't exist
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        # Create folders for each mailbox
        for mailbox_name in mailboxes:
            mailbox_path = os.path.join(project_path, mailbox_name)
            os.makedirs(mailbox_path, exist_ok=True)

            # Create raw and processed folders inside each mailbox
            os.makedirs(os.path.join(mailbox_path, 'raw'), exist_ok=True)
            os.makedirs(os.path.join(mailbox_path, 'processed'), exist_ok=True)

        return project_path

    # Function to save uploaded files
    def save_uploaded_files(mailbox_name, uploaded_files, project_path):
        mailbox_raw_path = os.path.join(project_path, mailbox_name, 'raw')

        for uploaded_file in uploaded_files:
            # Create a temporary file to store the uploaded content
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                # Write content to the temporary file
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            # Move the temporary file to the destination
            target_path = os.path.join(mailbox_raw_path, uploaded_file.name)
            shutil.move(tmp_file_path, target_path)

        return True

    # Initialize session state for project form
    if 'project_form' not in st.session_state:
        st.session_state.project_form = {
            'mode': None,  # 'create' or 'edit'
            'current_project': None,
            'project_name': '',
            'mailboxes': [
                {
                    'id': str(uuid.uuid4()),
                    'name': '',
                    'entity_name': '',
                    'is_physical_person': True,
                    'email_address': '',
                    'email_aliases': [],
                    'alias_names': [],
                    'organization_name': '',
                    'organization_description': '',
                    'positions': [
                        {
                            'id': str(uuid.uuid4()),
                            'title': '',
                            'start_date': '',
                            'end_date': '',
                            'description': ''
                        }
                    ],
                    'files': []
                }
            ]
        }

    # Function to reset form
    def reset_form():
        st.session_state.project_form = {
            'mode': None,
            'current_project': None,
            'project_name': '',
            'mailboxes': [
                {
                    'id': str(uuid.uuid4()),
                    'name': '',
                    'entity_name': '',
                    'is_physical_person': True,
                    'email_address': '',
                    'email_aliases': [],
                    'alias_names': [],
                    'organization_name': '',
                    'organization_description': '',
                    'positions': [
                        {
                            'id': str(uuid.uuid4()),
                            'title': '',
                            'start_date': '',
                            'end_date': '',
                            'description': ''
                        }
                    ],
                    'files': []
                }
            ]
        }

    # Function to load project data into form
    def load_project_for_edit(project):
        # Update the project order when a project is edited
        update_project_order(project['name'])

        form_data = {
            'mode': 'edit',
            'current_project': project['name'],
            'project_name': project['name'],
            'mailboxes': []
        }

        project_data = project['config'][project['name']]
        mailboxes_data = project_data.get('mailboxs', {})

        for mailbox_name, mailbox_data in mailboxes_data.items():
            positions = []
            for pos_title, pos_data in mailbox_data.get('Positions', {}).items():
                positions.append({
                    'id': str(uuid.uuid4()),
                    'title': pos_title,
                    'start_date': pos_data.get('start_date', ''),
                    'end_date': pos_data.get('end_date', ''),
                    'description': pos_data.get('description', '')
                })

            # If no positions were found, add a default empty one
            if not positions:
                positions.append({
                    'id': str(uuid.uuid4()),
                    'title': '',
                    'start_date': '',
                    'end_date': '',
                    'description': ''
                })

            entity_data = mailbox_data.get('Entity', {})
            org_data = mailbox_data.get('Organisation', {})

            form_data['mailboxes'].append({
                'id': str(uuid.uuid4()),
                'name': mailbox_name,
                'entity_name': entity_data.get('name', ''),
                'is_physical_person': entity_data.get('is_physical_person', True),
                'email_address': entity_data.get('email_adress', ''),
                'email_aliases': entity_data.get('email_adress_aliases', []),
                'alias_names': entity_data.get('alias_names', []),
                'organization_name': org_data.get('name', ''),
                'organization_description': org_data.get('description', ''),
                'positions': positions,
                'files': []  # Files can't be loaded from existing project
            })

        st.session_state.project_form = form_data

    # Function to start creating a new project
    def start_new_project():
        reset_form()
        st.session_state.project_form['mode'] = 'create'

    # Function to generate config JSON from form data
    def generate_config_json():
        form = st.session_state.project_form
        project_name = form['project_name']

        config = {project_name: {"mailboxs": {}}}

        for mailbox in form['mailboxes']:
            mailbox_name = mailbox['name']

            # Skip if mailbox name is empty
            if not mailbox_name:
                continue

            # Create positions dictionary
            positions = {}
            for position in mailbox['positions']:
                if position['title']:  # Only add positions with titles
                    positions[position['title']] = {
                        "start_date": position['start_date'],
                        "end_date": position['end_date'],
                        "description": position['description']
                    }

            # Create entity dictionary
            entity = {
                "name": mailbox['entity_name'],
                "alias_names": mailbox['alias_names'],
                "is_physical_person": mailbox['is_physical_person'],
                "email_adress": mailbox['email_address'],
                "email_adress_aliases": mailbox['email_aliases']
            }

            # Create organization dictionary
            organization = {
                "name": mailbox['organization_name'],
                "description": mailbox['organization_description']
            }

            # Add mailbox to config
            config[project_name]["mailboxs"][mailbox_name] = {
                "Positions": positions,
                "Entity": entity,
                "Organisation": organization
            }

        return config

    # Function to update project order in constants.py
    def update_project_order(project_name):
        constants_path = os.path.join(project_root, 'constants.py')
        try:
            with open(constants_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Extract current project order
            match = re.search(r'PROJECT_ORDER = \[(.*?)\]', content, re.DOTALL)
            if match:
                current_order_str = match.group(1)
                # Parse the current order into a list
                current_order = [p.strip().strip('"').strip("'") for p in current_order_str.split(',') if p.strip()]

                # Remove the project if it's already in the list
                if project_name in current_order:
                    current_order.remove(project_name)

                # Add the project to the beginning of the list
                current_order.insert(0, project_name)

                # Create the new project order string
                new_order_str = '[' + ', '.join([f'"{p}"' for p in current_order]) + ']'

                # Replace in the content
                new_content = re.sub(r'PROJECT_ORDER = \[.*?\]', f'PROJECT_ORDER = {new_order_str}', content, flags=re.DOTALL)

                with open(constants_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)

                return True
            else:
                # If PROJECT_ORDER doesn't exist yet, create it
                new_content = re.sub(r'ACTIVE_PROJECT = ".*?"', f'ACTIVE_PROJECT = "{project_name}"\n\n# Project order - Most recently accessed projects will appear first\n# Format: List of project names in display order\nPROJECT_ORDER = ["{project_name}"]', content)

                with open(constants_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)

                return True
        except Exception as e:
            st.error(f"Error updating project order: {str(e)}")
            return False

    # Function to set active project
    def set_active_project(project_name):
        constants_path = os.path.join(project_root, 'constants.py')
        env_path = os.path.join(project_root, '.env')
        try:
            with open(constants_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Use regex to replace the ACTIVE_PROJECT value
            new_content = re.sub(r'ACTIVE_PROJECT = ".*?"', f'ACTIVE_PROJECT = "{project_name}"', content)

            with open(constants_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            # Keep .env in sync so environment loads the same project
            try:
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as env_file:
                        env_content = env_file.read()

                    env_pattern = r'^ACTIVE_PROJECT\s*=.*$'
                    if re.search(env_pattern, env_content, flags=re.MULTILINE):
                        updated_env = re.sub(env_pattern, f'ACTIVE_PROJECT = "{project_name}"', env_content, flags=re.MULTILINE)
                    else:
                        updated_env = env_content.rstrip() + f'\nACTIVE_PROJECT = "{project_name}"\n'
                else:
                    updated_env = f'ACTIVE_PROJECT = "{project_name}"\n'

                with open(env_path, 'w', encoding='utf-8') as env_file:
                    env_file.write(updated_env)
            except Exception as env_error:
                st.warning(f"Active project updated but .env sync failed: {env_error}")

            # Refresh in-memory configuration for current Streamlit session
            os.environ["ACTIVE_PROJECT"] = project_name
            load_dotenv(override=True)
            importlib.reload(constants)
            st.session_state.active_project = project_name
            st.cache_data.clear()

            # Update project order
            update_project_order(project_name)

            return True
        except Exception as e:
            st.error(f"Error setting active project: {str(e)}")
            return False

    def remove_project_from_constants(project_name):
        """Remove a project from the PROJECT_ORDER list in constants.py."""
        constants_path = os.path.join(project_root, 'constants.py')
        try:
            with open(constants_path, 'r', encoding='utf-8') as file:
                content = file.read()

            match = re.search(r'PROJECT_ORDER\s*=\s*\[(.*?)\]', content, flags=re.DOTALL)
            if not match:
                return

            order_str = match.group(0).split('=', 1)[1].strip()
            try:
                project_order = ast.literal_eval(order_str)
            except (SyntaxError, ValueError):
                return

            filtered_order = [name for name in project_order if name != project_name]
            order_repr = ', '.join(f'"{name}"' for name in filtered_order)
            new_order_block = f'PROJECT_ORDER = [{order_repr}]'
            content = re.sub(r'PROJECT_ORDER\s*=\s*\[.*?\]', new_order_block, content, flags=re.DOTALL)

            with open(constants_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            st.warning(f"Failed to update project order in constants.py: {e}")

    def handle_project_creation_failure(project_name, project_path, reason, fallback_project=None):
        """Clean up partial project data and prepare an error message for the overview."""
        cleanup_notes = []

        if project_path and os.path.exists(project_path):
            try:
                shutil.rmtree(project_path)
            except Exception as cleanup_error:
                cleanup_notes.append(f"Impossible de supprimer le dossier du projet ({cleanup_error})")

        remove_project_from_constants(project_name)

        fallback = fallback_project or DEFAULT_PROJECT_NAME
        if fallback:
            set_active_project(fallback)

        message_parts = [f"❌ La création du projet '{project_name}' a échoué."]
        if reason:
            message_parts.append(reason)
        if cleanup_notes:
            message_parts.extend(cleanup_notes)

        st.session_state.project_creation_error = " ".join(message_parts)
        reset_form()

    def mailboxes_missing_files(project_path, mailbox_names, subfolder, required_extensions=None):
        missing = []
        extensions = None
        if required_extensions:
            if isinstance(required_extensions, str):
                extensions = (required_extensions.lower(),)
            else:
                extensions = tuple(ext.lower() for ext in required_extensions)

        for mailbox_name in mailbox_names:
            target_dir = os.path.join(project_path, mailbox_name, subfolder)
            if not os.path.isdir(target_dir):
                missing.append(mailbox_name)
                continue

            has_files = False
            for _, _, files in os.walk(target_dir):
                if not files:
                    continue

                if extensions:
                    if any(file.lower().endswith(extensions) for file in files):
                        has_files = True
                        break
                else:
                    has_files = True
                    break

            if not has_files:
                missing.append(mailbox_name)

        return missing

    # Function to validate form data
    def validate_form():
        form = st.session_state.project_form

        if not form['project_name']:
            st.error("Project name is required")
            return False

        if not form['mailboxes']:
            st.error("At least one mailbox is required")
            return False

        for i, mailbox in enumerate(form['mailboxes']):
            if not mailbox['name']:
                st.error(f"Mailbox #{i+1} name is required")
                return False
            if not mailbox['entity_name']:
                st.error(f"Entity name for mailbox '{mailbox['name']}' is required")
                return False
            if not mailbox['email_address']:
                st.error(f"Email address for mailbox '{mailbox['name']}' is required")
                return False
            if not mailbox['organization_name']:
                st.error(f"Organization name for mailbox '{mailbox['name']}' is required")
                return False

        return True

    # Function to save project
    def save_project():
        if not validate_form():
            return False

        form = st.session_state.project_form
        project_name = form['project_name']

        previous_project = st.session_state.get('active_project', DEFAULT_PROJECT_NAME)

        set_active_project(project_name)

        # Generate config JSON
        config = generate_config_json()

        # Create project structure (folders for project and mailboxes)
        project_path = create_project_structure(
            project_name,
            [mailbox['name'] for mailbox in form['mailboxes']]
        )

        # Save config file
        config_path = os.path.join(project_path, 'project_config_file.json')
        with open(config_path, 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=2, ensure_ascii=False)

        # Save uploaded files for each mailbox
        for mailbox in form['mailboxes']:
            if mailbox['files']:
                save_uploaded_files(mailbox['name'], mailbox['files'], project_path)

        # Update the project order when a project is saved
        update_project_order(project_name)

        # Start data preparation pipeline for new projects
        if form['mode'] == 'create':
            # Collect mailbox info including data sources
            mailbox_info = []
            for mailbox in form['mailboxes']:
                mailbox_info.append({
                    'name': mailbox['name'],
                    'data_source': mailbox.get('data_source', 'upload'),
                    's3_project_name': mailbox.get('s3_project_name', '')
                })

            pipeline_success, pipeline_message = start_data_preparation_pipeline(project_name, project_path, mailbox_info)
            if pipeline_success:
                st.info("Data preparation pipeline started successfully. Processing will continue in the background.")
            else:
                handle_project_creation_failure(project_name, project_path, pipeline_message, fallback_project=previous_project)
                return False

        return True

    class PipelineError(Exception):
        """Custom exception for pipeline failures."""

    def start_data_preparation_pipeline(project_name, project_path, mailbox_info):
        """
        Start the complete data preparation pipeline for a newly created project.
        This function is called after project folders are created and will orchestrate
        the entire data processing workflow.

        Args:
            project_name (str): Name of the project
            project_path (str): Full path to the project directory
            mailbox_info (list): List of mailbox dictionaries with name, data_source, s3_project_name

        Returns:
            tuple: (success: bool, message: Optional[str])
        """
        # TODO: Implement the data preparation pipeline
        # This function will call other functions to:
        # 1. 
        # 2. Process EML files into DuckDB
        # 3. Generate embeddings and search indexes
        # 4. Initialize RAG system
        # 5. Create visualizations and analytics

        try:
            print(f"Starting data preparation pipeline for project: {project_name}")
            print(f"Project path: {project_path}")
            print(f"Mailboxes to process: {[mb['name'] for mb in mailbox_info]}")

            mailbox_names = [mb['name'] for mb in mailbox_info]

            if not mailbox_names:
                raise PipelineError("Aucune boîte mail n'a été fournie pour la création du projet.")

            # Separate mailboxes by data source
            upload_mailboxes = [mb['name'] for mb in mailbox_info if mb['data_source'] == 'upload']
            s3_mailboxes = [mb for mb in mailbox_info if mb['data_source'] == 's3' and mb['s3_project_name']]

            # For uploaded files: upload to S3 then download back to verify
            if upload_mailboxes:
                st.info("📤 Téléversement des fichiers fournis...")
                upload_success = upload_project_raw_data_to_s3(project_name, project_path, upload_mailboxes)
                if not upload_success:
                    raise PipelineError("Échec du téléversement des données brutes vers S3 pour au moins une boîte mail.")

                st.info("Vérification de la synchronisation S3...")
                download_success = download_project_raw_data_from_s3(project_name, project_path, upload_mailboxes)
                if not download_success:
                    raise PipelineError("La vérification de la synchronisation S3 a échoué pour les boîtes mail téléversées.")

            # For S3 sources: just download from selected projects
            if s3_mailboxes:
                st.info("📥 Téléchargement des données depuis les projets S3 sélectionnés...")
                for mailbox in s3_mailboxes:
                    download_success = download_project_raw_data_from_s3(
                        project_name=mailbox['s3_project_name'],
                        project_path=project_path,
                        mailbox_names=[mailbox['name']]
                    )
                    if not download_success:
                        raise PipelineError(
                            f"Échec du téléchargement des données S3 pour la boîte mail '{mailbox['name']}'."
                        )

            # Verify raw data presence
            missing_raw = mailboxes_missing_files(project_path, mailbox_names, 'raw')
            if missing_raw:
                raise PipelineError(
                    "Aucune donnée brute n'a été trouvée pour les boîtes mail suivantes : " +
                    ", ".join(missing_raw)
                )


            # Convert PST/MBOX (included if they are in a zip) files to EML
            # Unzip if needed
            unzip_success = extract_project_zip_files(project_name, project_path, mailbox_names)
            if not unzip_success:
                raise PipelineError("L'extraction des archives ZIP a échoué.")

            cleanup_stats = cleanup_mailbox_raw_artifacts(project_path, mailbox_names)
            if cleanup_stats["removed_directories"] or cleanup_stats["removed_files"]:
                st.info(
                    "Nettoyage des artefacts macOS : suppression de "
                    f"{len(cleanup_stats['removed_directories'])} dossiers et "
                    f"{len(cleanup_stats['removed_files'])} fichiers."
                )

            # process files into .eml (s)
            conversion_success = convert_project_emails_to_eml(project_name, project_path, mailbox_names)
            if not conversion_success:
                raise PipelineError("La conversion des emails en EML a échoué.")
            
            # Process EML files into DuckDB
            db_path = generate_duck_db()
            if not db_path or not os.path.exists(db_path):
                raise PipelineError(
                    "La base de données DuckDB attendue n'a pas été générée "
                    f"(fichier manquant : {project_name}.duckdb)."
                )

            try:
                db_conn = duckdb.connect(db_path, read_only=True)
                existing_tables = {
                    row[0]
                    for row in db_conn.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
                    ).fetchall()
                }

                if "receiver_emails" not in existing_tables:
                    raise PipelineError(
                        "La base de données DuckDB est incomplète : la table 'receiver_emails' est absente."
                    )

                email_count = db_conn.execute("SELECT COUNT(*) FROM receiver_emails").fetchone()[0]
                if email_count == 0:
                    raise PipelineError(
                        "La base de données DuckDB a été créée mais ne contient aucun email."
                    )
            except PipelineError:
                raise
            except Exception as db_error:
                raise PipelineError(f"La vérification de la base DuckDB a échoué : {db_error}")
            finally:
                try:
                    db_conn.close()
                except Exception:
                    pass

            missing_processed = mailboxes_missing_files(
                project_path,
                mailbox_names,
                'processed',
                required_extensions=('.eml',)
            )
            if missing_processed:
                raise PipelineError(
                    "Aucun email converti (.eml) n'a été trouvé pour les boîtes mail suivantes : " +
                    ", ".join(missing_processed)
                )

            st.info("🚀 Initialisation du système RAG (ColBERT)...")
            st.info("📊 Construction des index sémantiques pour la recherche avancée")
            try:
                with st.spinner("Construction du système RAG - cela peut prendre quelques minutes..."):
                    index_dir = initialize_colbert_rag_system(
                        project_root=project_root,
                        force_rebuild=True,
                        test_mode=False,
                        rag_mode="light",
                        project_name=project_name
                    )
                print(f"Colbert RAG system initialized with index at {index_dir}")
            except Exception as rag_error:
                raise PipelineError(f"La construction du système RAG a échoué: {rag_error}")

            print("Data preparation pipeline completed successfully")
            return True, None

        except PipelineError as pipeline_error:
            error_message = str(pipeline_error)
            st.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Erreur inattendue dans le pipeline: {e}"
            st.error(error_message)
            return False, error_message

    def upload_project_raw_data_to_s3(project_name, project_path, mailbox_names, bucket_name="olkoa-projects"):
        """
        Upload raw data for all mailboxes in a project to S3.

        Args:
            project_name (str): Name of the project
            project_path (str): Full path to the project directory
            mailbox_names (list): List of mailbox names to upload
            bucket_name (str): S3 bucket name (default: "olkoa-projects")

        Returns:
            bool: True if all uploads successful, False otherwise
        """
        try:
            # Initialize S3 handler
            s3_handler = S3Handler()

            # Ensure bucket exists (create if it doesn't)
            try:
                buckets = s3_handler.list_buckets()
                if bucket_name not in buckets:
                    s3_handler.create_bucket(bucket_name)
                    st.info(f"Created S3 bucket: {bucket_name}")
            except Exception as e:
                st.error(f"Failed to check/create S3 bucket: {e}")
                return False

            upload_success = True
            uploaded_any = False
            missing_mailboxes = []

            # Upload raw data for each mailbox
            for mailbox_name in mailbox_names:
                local_raw_data_dir = os.path.join(project_path, mailbox_name, "raw")
                s3_prefix = f"{project_name}/{mailbox_name}/raw"

                # Check if raw data directory exists and has files
                if not os.path.exists(local_raw_data_dir):
                    st.warning(f"Raw data directory not found for mailbox '{mailbox_name}': {local_raw_data_dir}")
                    missing_mailboxes.append(mailbox_name)
                    upload_success = False
                    continue

                if not os.listdir(local_raw_data_dir):
                    st.warning(f"No files found to upload for mailbox '{mailbox_name}'")
                    missing_mailboxes.append(mailbox_name)
                    upload_success = False
                    continue

                try:
                    st.info(f"Uploading raw data for mailbox: {mailbox_name}")
                    s3_handler.upload_directory(
                        local_dir=local_raw_data_dir,
                        bucket_name=bucket_name,
                        s3_prefix=s3_prefix
                    )
                    st.success(f"Successfully uploaded raw data for mailbox '{mailbox_name}' to S3")
                    uploaded_any = True

                except Exception as e:
                    st.error(f"Failed to upload raw data for mailbox '{mailbox_name}': {e}")
                    upload_success = False

            if missing_mailboxes:
                st.warning("Les boîtes mail suivantes n'ont fourni aucun fichier brut : " + ", ".join(missing_mailboxes))

            if not uploaded_any:
                return False

            return upload_success

        except Exception as e:
            st.error(f"Error in S3 upload process: {e}")
            return False

    def download_project_raw_data_from_s3(project_name, project_path, mailbox_names, bucket_name="olkoa-projects"):
        """
        Download raw data for all mailboxes in a project from S3.

        Args:
            project_name (str): Name of the project
            project_path (str): Full path to the project directory
            mailbox_names (list): List of mailbox names to download
            bucket_name (str): S3 bucket name (default: "olkoa-projects")

        Returns:
            bool: True if all downloads successful, False otherwise
        """
        if not mailbox_names:
            return True

        try:
            # Initialize S3 handler
            s3_handler = S3Handler()

            # Check if bucket exists
            try:
                buckets = s3_handler.list_buckets()
                if bucket_name not in buckets:
                    st.error(f"S3 bucket '{bucket_name}' not found")
                    return False
            except Exception as e:
                st.error(f"Failed to check S3 bucket: {e}")
                return False

            download_success = True
            total_downloaded_files = 0
            total_downloaded_size = 0
            total_mailboxes = len(mailbox_names)

            # Download raw data for each mailbox
            for mailbox_idx, mailbox_name in enumerate(mailbox_names, 1):
                local_raw_data_dir = os.path.join(project_path, mailbox_name, "raw")

                candidate_prefixes = []
                if mailbox_name:
                    candidate_prefixes.extend([
                        f"{project_name}/{mailbox_name}/raw",
                        f"{project_name}/{mailbox_name}"
                    ])
                candidate_prefixes.extend([
                    f"{project_name}/raw",
                    f"{project_name}"
                ])

                objects_found = []
                selected_prefix = None
                for prefix in candidate_prefixes:
                    try:
                        objects_found = s3_handler.list_objects(bucket_name=bucket_name, prefix=prefix)
                    except Exception:
                        objects_found = []

                    if objects_found:
                        selected_prefix = prefix.rstrip('/')
                        break

                if not selected_prefix:
                    st.error(
                        "❌ Aucun fichier trouvé sur S3 pour la boîte mail "
                        f"'{mailbox_name}'. Préfixes testés: " + ", ".join(candidate_prefixes)
                    )
                    download_success = False
                    continue

                try:
                    st.info(f"📦 Downloading raw data for mailbox {mailbox_idx}/{total_mailboxes}: {mailbox_name}")

                    # Create a progress callback for individual file tracking
                    progress_placeholder = st.empty()

                    def progress_callback(current_file, total_files, current_filename):
                        file_progress = (current_file / total_files) * 100
                        progress_placeholder.info(f"📄 File {current_file}/{total_files} ({file_progress:.1f}%): {os.path.basename(current_filename)}")

                    # Download the directory with progress tracking
                    stats = s3_handler.download_directory(
                        bucket_name=bucket_name,
                        s3_prefix=selected_prefix,
                        local_dir=local_raw_data_dir,
                        progress_callback=progress_callback
                    )

                    # Clear progress placeholder
                    progress_placeholder.empty()

                    if stats['downloaded_files'] > 0:
                        # Format file size for better readability
                        size_mb = stats['total_size'] / (1024 * 1024)
                        size_display = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{stats['total_size'] / 1024:.2f} KB"

                        st.success(f"✅ Successfully downloaded {stats['downloaded_files']} files for mailbox '{mailbox_name}'")
                        st.info(f"📊 Size: {size_display} | 📁 Downloaded to: {local_raw_data_dir}")

                        # Update totals
                        total_downloaded_files += stats['downloaded_files']
                        total_downloaded_size += stats['total_size']

                        # Print path information
                        print(f"✅ Downloaded mailbox '{mailbox_name}' to: {local_raw_data_dir}")
                        print(f"   Files: {stats['downloaded_files']}, Size: {size_display}")
                    else:
                        st.warning(
                            "⚠️ Aucun fichier téléchargé depuis S3 pour la boîte mail "
                            f"'{mailbox_name}' (préfixe '{selected_prefix}')."
                        )
                        download_success = False

                    if stats['failed_files'] > 0:
                        st.warning(f"❌ Failed to download {stats['failed_files']} files for mailbox '{mailbox_name}'")
                        download_success = False

                    # Show overall progress across mailboxes
                    overall_progress = (mailbox_idx / total_mailboxes) * 100
                    st.progress(overall_progress / 100, text=f"Overall progress: {mailbox_idx}/{total_mailboxes} mailboxes ({overall_progress:.1f}%)")

                except Exception as e:
                    st.error(f"❌ Failed to download raw data for mailbox '{mailbox_name}': {e}")
                    print(f"❌ Error downloading mailbox '{mailbox_name}': {e}")
                    download_success = False

            # Final completion summary
            if total_downloaded_files > 0:
                total_size_mb = total_downloaded_size / (1024 * 1024)
                total_size_display = f"{total_size_mb:.2f} MB" if total_size_mb >= 1 else f"{total_downloaded_size / 1024:.2f} KB"

                st.success(f"🎉 Download completed! Total: {total_downloaded_files} files ({total_size_display}) across {total_mailboxes} mailboxes")
                st.info(f"📁 All files downloaded to project directory: {project_path}")

                # Print completion info to console
                print(f"\n🎉 DOWNLOAD COMPLETION SUMMARY:")
                print(f"   Project: {project_name}")
                print(f"   Total Files: {total_downloaded_files}")
                print(f"   Total Size: {total_size_display}")
                print(f"   Mailboxes: {total_mailboxes}")
                print(f"   Root Path: {project_path}")
                print(f"   Success: {'✅ YES' if download_success else '❌ PARTIAL'}")

            if total_downloaded_files == 0:
                st.warning("⚠️ Aucun fichier n'a été téléchargé depuis S3 pour ce projet.")
                return False

            return download_success

        except Exception as e:
            st.error(f"Error in S3 download process: {e}")
            return False

    def extract_project_zip_files(project_name, project_path, mailbox_names):
        """
        Extract ZIP files found in raw folders for all mailboxes in a project.

        Args:
            project_name (str): Name of the project
            project_path (str): Full path to the project directory
            mailbox_names (list): List of mailbox names to process

        Returns:
            bool: True if all extractions successful, False otherwise
        """
        try:
            extraction_success = True

            # Process each mailbox
            for mailbox_name in mailbox_names:
                raw_folder = os.path.join(project_path, mailbox_name, "raw")

                # Check if raw folder exists
                if not os.path.exists(raw_folder):
                    st.warning(f"Raw data folder not found for mailbox '{mailbox_name}': {raw_folder}")
                    continue

                # Find ZIP files
                zip_files = []
                for root, dirs, files in os.walk(raw_folder):
                    for file in files:
                        if file.lower().endswith('.zip'):
                            zip_files.append(os.path.join(root, file))

                if not zip_files:
                    st.info(f"No ZIP files found for mailbox '{mailbox_name}'")
                    continue

                st.info(f"Found {len(zip_files)} ZIP files for mailbox: {mailbox_name}")

                # Extract each ZIP file
                for zip_file_path in zip_files:
                    try:
                        zip_filename = os.path.basename(zip_file_path)
                        extract_dir = os.path.join(raw_folder, f"extracted_{os.path.splitext(zip_filename)[0]}")

                        # Create extraction directory if it doesn't exist
                        os.makedirs(extract_dir, exist_ok=True)

                        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                            # Check if ZIP file is valid and not corrupted
                            zip_ref.testzip()

                            # Extract all contents
                            zip_ref.extractall(extract_dir)

                        st.success(f"Successfully extracted: {zip_filename}")
                        st.info(f"Extracted to: {extract_dir}")

                        # Optionally, remove the original ZIP file after successful extraction
                        # os.remove(zip_file_path)
                        # st.info(f"Removed original ZIP file: {zip_filename}")

                    except zipfile.BadZipFile:
                        st.error(f"Bad ZIP file (corrupted or invalid): {zip_filename}")
                        extraction_success = False
                    except Exception as e:
                        st.error(f"Failed to extract ZIP file '{zip_filename}': {e}")
                        extraction_success = False

            return extraction_success

        except Exception as e:
            st.error(f"Error in ZIP extraction process: {e}")
            return False


    def cleanup_mailbox_raw_artifacts(project_path, mailbox_names):
        """Remove macOS-specific artifacts from raw mailbox folders."""
        removed_dirs = []
        removed_files = []

        for mailbox_name in mailbox_names:
            raw_folder = os.path.join(project_path, mailbox_name, "raw")
            if not os.path.isdir(raw_folder):
                continue

            # We clean both the raw root and any extracted_* subdirectories
            candidate_roots = [raw_folder]
            candidate_roots.extend(
                os.path.join(raw_folder, entry)
                for entry in os.listdir(raw_folder)
                if entry.startswith("extracted_")
                and os.path.isdir(os.path.join(raw_folder, entry))
            )

            for candidate_root in candidate_roots:
                for root, dirs, files in os.walk(candidate_root, topdown=True):
                    # Remove __MACOSX directories produced by macOS zipping
                    for dirname in list(dirs):
                        if dirname == "__MACOSX":
                            dir_path = os.path.join(root, dirname)
                            try:
                                shutil.rmtree(dir_path)
                                removed_dirs.append(dir_path)
                            except Exception as cleanup_error:
                                st.warning(f"Impossible de supprimer {dir_path}: {cleanup_error}")
                            dirs.remove(dirname)

                    # Remove AppleDouble resource fork files and other trivial artefacts
                    for filename in files:
                        if filename.startswith("._") or filename in {".DS_Store"}:
                            file_path = os.path.join(root, filename)
                            try:
                                os.remove(file_path)
                                removed_files.append(file_path)
                            except FileNotFoundError:
                                continue
                            except Exception as cleanup_error:
                                st.warning(f"Impossible de supprimer {file_path}: {cleanup_error}")

        return {
            "removed_directories": removed_dirs,
            "removed_files": removed_files,
        }

    def convert_project_emails_to_eml(project_name, project_path, mailbox_names):
        """
        Convert PST/MBOX files to EML format for all mailboxes in a project.
        Handles PST files first (using readpst), then MBOX files (using internal converter).

        Args:
            project_name (str): Name of the project
            project_path (str): Full path to the project directory
            mailbox_names (list): List of mailbox names to process

        Returns:
            bool: True if all conversions successful, False otherwise
        """
        try:
            conversion_success = True

            # Process each mailbox
            for mailbox_name in mailbox_names:
                raw_folder = os.path.join(project_path, mailbox_name, "raw")
                processed_folder = os.path.join(project_path, mailbox_name, "processed")

                # Check if raw folder exists
                if not os.path.exists(raw_folder):
                    st.warning(f"Raw data folder not found for mailbox '{mailbox_name}': {raw_folder}")
                    continue

                os.makedirs(processed_folder, exist_ok=True)

                # First, convert PST files directly to processed folder (readpst creates natural structure)
                pst_success = convert_pst_files(raw_folder, processed_folder, mailbox_name)
                if not pst_success:
                    conversion_success = False

                # Then, convert MBOX files following the same natural structure
                mbox_success = convert_mbox_files(raw_folder, processed_folder, mailbox_name)
                if not mbox_success:
                    conversion_success = False

                # Finally, ensure standalone EML files are available in processed
                raw_eml_files = []
                for root, _, files in os.walk(raw_folder):
                    for file in files:
                        if file.lower().endswith('.eml'):
                            raw_eml_files.append(os.path.join(root, file))

                processed_eml_exists = False
                for root, _, files in os.walk(processed_folder):
                    if any(file.lower().endswith('.eml') for file in files):
                        processed_eml_exists = True
                        break

                if raw_eml_files and not processed_eml_exists:
                    copied = 0
                    for src_path in raw_eml_files:
                        rel_path = os.path.relpath(src_path, raw_folder)
                        dest_path = os.path.join(processed_folder, rel_path)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        try:
                            shutil.copy2(src_path, dest_path)
                            copied += 1
                        except Exception as copy_error:
                            st.warning(f"Impossible de copier le fichier EML '{src_path}': {copy_error}")
                            conversion_success = False

                    if copied:
                        st.success(
                            f"Mailbox '{mailbox_name}': copied {copied} fichiers EML existants vers le dossier processed"
                        )

            return conversion_success

        except Exception as e:
            st.error(f"Error in email to EML conversion process: {e}")
            return False

    def convert_pst_files(raw_folder, processed_folder, mailbox_name):
        """
        Convert PST files to EML using readpst command.
        Outputs directly to processed folder to create natural mailbox structure.

        Args:
            raw_folder (str): Path to raw data folder
            processed_folder (str): Path to processed folder (where natural structure will be created)
            mailbox_name (str): Name of the mailbox for logging

        Returns:
            bool: True if successful or no PST files, False if conversion failed
        """
        try:
            # Find PST files
            pst_files = []
            for root, dirs, files in os.walk(raw_folder):
                for file in files:
                    if file.lower().endswith('.pst'):
                        pst_files.append(os.path.join(root, file))

            if not pst_files:
                st.info(f"No PST files found for mailbox '{mailbox_name}'")
                return True

            # Check if readpst is available
            try:
                subprocess.run(["which", "readpst"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                st.error(f"'readpst' is not installed. Cannot convert PST files for mailbox '{mailbox_name}'")
                st.info("Install readpst with: sudo apt-get install pst-utils (Linux) or brew install libpst (macOS)")
                return False

            st.info(f"Converting {len(pst_files)} PST files for mailbox: {mailbox_name}")

            for pst_file in pst_files:
                try:
                    # Run readpst to convert PST → EML directly to processed folder
                    # This creates the natural mailbox structure like:
                    # processed/username/Boîte de réception/, processed/username/Archive/, etc.
                    cmd = ["readpst", "-j", "0", "-e", "-o", processed_folder, pst_file]

                    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                    st.success(f"Successfully converted PST file: {os.path.basename(pst_file)}")
                    st.info(f"Natural mailbox structure created in: {processed_folder}")

                except subprocess.CalledProcessError as e:
                    st.error(f"Failed to convert PST file {os.path.basename(pst_file)}: {e}")
                    return False
                except Exception as e:
                    st.error(f"Error processing PST file {os.path.basename(pst_file)}: {e}")
                    return False

            return True

        except Exception as e:
            st.error(f"Error in PST conversion for mailbox '{mailbox_name}': {e}")
            return False

    def convert_mbox_files(raw_folder, processed_folder, mailbox_name):
        """
        Convert MBOX files to EML following the natural mailbox structure pattern.
        Creates structure similar to readpst output for consistency.

        Args:
            raw_folder (str): Path to raw data folder
            processed_folder (str): Path to processed folder (where natural structure will be created)
            mailbox_name (str): Name of the mailbox for logging

        Returns:
            bool: True if successful or no MBOX files, False if conversion failed
        """
        try:
            # Check if there are any MBOX files to convert
            mbox_files = []
            for root, dirs, files in os.walk(raw_folder):
                for file in files:
                    if file.endswith('.mbox') or file.endswith('.mbox.gz'):
                        mbox_files.append(os.path.join(root, file))

            if not mbox_files:
                st.info(f"No MBOX files found for mailbox '{mailbox_name}'")
                return True

            st.info(f"Converting {len(mbox_files)} MBOX files for mailbox: {mailbox_name}")

            # Create a natural mailbox structure for MBOX files
            # Follow pattern similar to readpst: processed/username/folder_name/

            total_emails = 0
            for mbox_file in mbox_files:
                try:
                    # Get MBOX filename without extension for folder name
                    mbox_filename = os.path.splitext(os.path.basename(mbox_file))[0]

                    # Create natural structure similar to readpst
                    # If MBOX file is named like "inbox.mbox", create folder "Boîte de réception"
                    # If MBOX file is named like "sent.mbox", create folder "Éléments envoyés"
                    folder_mapping = {
                        'inbox': 'Boîte de réception',
                        'sent': 'Éléments envoyés',
                        'archive': 'Archive',
                        'drafts': 'Brouillons',
                        'trash': 'Éléments supprimés',
                        'spam': 'Courrier indésirable'
                    }

                    # Check if mbox filename matches known folder types
                    folder_name = folder_mapping.get(mbox_filename.lower(), mbox_filename)

                    # Create the user folder structure (like readpst does)
                    user_folder = os.path.join(processed_folder, mailbox_name.lower())
                    mailbox_folder = os.path.join(user_folder, folder_name)
                    os.makedirs(mailbox_folder, exist_ok=True)

                    # Convert this MBOX file to EML files in the appropriate folder
                    email_count = mbox_to_eml(mbox_file, mailbox_folder)
                    total_emails += email_count

                    st.success(f"Converted {mbox_filename}.mbox: {email_count} emails → {folder_name}/")

                except Exception as e:
                    st.error(f"Failed to convert MBOX file {os.path.basename(mbox_file)}: {e}")
                    return False

            if total_emails > 0:
                st.success(f"Mailbox '{mailbox_name}': Converted {len(mbox_files)} MBOX files")
                st.info(f"Total emails extracted: {total_emails}")
                st.info(f"Natural mailbox structure created in: {processed_folder}")
                return True
            else:
                st.warning(f"No emails extracted from MBOX files for mailbox '{mailbox_name}'")
                return True

        except Exception as e:
            st.error(f"Error in MBOX conversion for mailbox '{mailbox_name}': {e}")
            return False

    # Function to handle adding a new mailbox
    def add_mailbox():
        st.session_state.project_form['mailboxes'].append({
            'id': str(uuid.uuid4()),
            'name': '',
            'entity_name': '',
            'is_physical_person': True,
            'email_address': '',
            'email_aliases': [],
            'alias_names': [],
            'organization_name': '',
            'organization_description': '',
            'positions': [
                {
                    'id': str(uuid.uuid4()),
                    'title': '',
                    'start_date': '',
                    'end_date': '',
                    'description': ''
                }
            ],
            'files': [],
            'data_source': 'upload',  # 'upload' or 's3'
            's3_project_name': ''  # Selected S3 project to download from
        })

    # Function to handle adding a new position
    def add_position(mailbox_idx):
        st.session_state.project_form['mailboxes'][mailbox_idx]['positions'].append({
            'id': str(uuid.uuid4()),
            'title': '',
            'start_date': '',
            'end_date': '',
            'description': ''
        })

    # Function to handle removing a mailbox
    def remove_mailbox(idx):
        mailboxes = st.session_state.project_form['mailboxes']
        if len(mailboxes) > 1:  # Ensure at least one mailbox remains
            del mailboxes[idx]
        else:
            st.error("At least one mailbox must remain")

    # Function to handle removing a position
    def remove_position(mailbox_idx, position_idx):
        positions = st.session_state.project_form['mailboxes'][mailbox_idx]['positions']
        if len(positions) > 1:  # Ensure at least one position remains
            del positions[position_idx]
        else:
            st.error("At least one position must remain")

    # Main interface logic
    # First, check if we're in project list view or form view
    if st.session_state.project_form['mode'] is None:
        if st.session_state.project_creation_error:
            st.error(st.session_state.project_creation_error)
            st.session_state.project_creation_error = None

        # We're in project list view - show all projects
        projects = find_projects()

        # Create a centered button for new project
        st.markdown("""
        <style>
        .centered-button-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="centered-button-container">', unsafe_allow_html=True)
        if st.button("Créer un Projet", key="new-project-btn", help="Create a new project", type="primary", use_container_width=True):
            start_new_project()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if not projects:
            st.info("No projects found. Create your first project by clicking the 'Créer un Projet' button.")
        else:
            st.subheader("Existing Projects")

            # Create a 2-column layout for project cards
            cols = st.columns(2)

            for i, project in enumerate(projects):
                col_idx = i % 2
                with cols[col_idx]:
                    # Project card with summary information
                    with st.container(border=True):
                        st.subheader(project["name"])

                        # Count mailboxes
                        mailbox_count = len(project["config"][project["name"]].get("mailboxs", {}))
                        st.write(f"📧 {mailbox_count} mailbox{'es' if mailbox_count != 1 else ''}")

                        # List the first few mailboxes
                        mailboxes = list(project["config"][project["name"]].get("mailboxs", {}).keys())
                        for j, mailbox in enumerate(mailboxes):
                            if j < 3:  # Show only first 3 mailboxes
                                st.write(f"- {mailbox}")
                            elif j == 3:
                                st.write(f"- ... {len(mailboxes) - 3} more")
                                break

                        # Get current active project from constants.py
                        constants_path = os.path.join(project_root, 'constants.py')
                        with open(constants_path, 'r', encoding='utf-8') as file:
                            constants_content = file.read()
                        match = re.search(r'ACTIVE_PROJECT = "(.*?)"', constants_content)
                        active_project = match.group(1) if match else ""

                        # Add some extra spacing before the buttons
                        st.write(" ")

                        # Edit button
                        if st.button("Edit", key=f"edit_{i}"):
                            load_project_for_edit(project)
                            st.rerun()

                        # Selection button with colored active project
                        if project["name"] == active_project:
                            st.markdown("""<div style='display: block; background-color: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px; text-align: center; margin-top: 10px; margin-bottom: 5px; width: fit-content;'>Projet Activé</div>""", unsafe_allow_html=True)
                        else:
                            if st.button("Sélectionner", key=f"select_{i}"):
                                if set_active_project(project["name"]):
                                    st.success(f"'{project['name']}' est maintenant le projet actif")
                                    st.rerun()
    else:
        # We're in form view - show project form
        form = st.session_state.project_form

        # Back button
        if st.button("← Back to Projects"):
            reset_form()
            st.rerun()

        # Form header
        if form['mode'] == 'create':
            st.header("Create New Project")
        else:
            st.header(f"Edit Project: {form['project_name']}")

        # Project name
        project_name = st.text_input(
            "Project Name",
            value=form['project_name'],
            disabled=form['mode'] == 'edit',  # Can't change project name in edit mode
            help="The name of your project"
        )
        st.session_state.project_form['project_name'] = project_name

        # Container for all mailboxes
        for i, mailbox in enumerate(form['mailboxes']):
            with st.expander(f"Mailbox: {mailbox['name'] or f'(Unnamed #{i+1}'}", expanded=True):
                # Two-column layout for mailbox basic info
                col1, col2 = st.columns(2)

                with col1:
                    # Mailbox name
                    mailbox_name = st.text_input(
                        "Mailbox Name",
                        value=mailbox['name'],
                        key=f"mb_name_{mailbox['id']}",
                        disabled=form['mode'] == 'edit',  # Can't change mailbox name in edit mode
                        help="Name of the mailbox (e.g., 'John's Mailbox')"
                    )
                    st.session_state.project_form['mailboxes'][i]['name'] = mailbox_name

                    # Entity info section
                    st.markdown("##### Entity Information")

                    # Entity name
                    entity_name = st.text_input(
                        "Entity Name",
                        value=mailbox['entity_name'],
                        key=f"entity_name_{mailbox['id']}",
                        disabled=form['mode'] == 'edit',  # Can't change entity name in edit mode
                        help="Name of the person or entity who owns this mailbox"
                    )
                    st.session_state.project_form['mailboxes'][i]['entity_name'] = entity_name

                    # Is physical person
                    is_physical = st.checkbox(
                        "Is a physical person",
                        value=mailbox['is_physical_person'],
                        key=f"is_physical_{mailbox['id']}",
                        disabled=form['mode'] == 'edit'  # Can't change in edit mode
                    )
                    st.session_state.project_form['mailboxes'][i]['is_physical_person'] = is_physical

                    # Email address
                    email = st.text_input(
                        "Primary Email Address",
                        value=mailbox['email_address'],
                        key=f"email_{mailbox['id']}",
                        disabled=form['mode'] == 'edit',  # Can't change email in edit mode
                        help="The main email address for this mailbox"
                    )
                    st.session_state.project_form['mailboxes'][i]['email_address'] = email

                    # Email aliases - using tags input
                    email_aliases_text = st.text_area(
                        "Email Aliases (one per line)",
                        value="\n".join(mailbox['email_aliases']),
                        key=f"email_aliases_{mailbox['id']}",
                        help="Alternative email addresses for this entity (one per line)"
                    )
                    aliases = [alias.strip() for alias in email_aliases_text.split("\n") if alias.strip()]
                    st.session_state.project_form['mailboxes'][i]['email_aliases'] = aliases

                    # Entity aliases - using tags input
                    name_aliases_text = st.text_area(
                        "Name Aliases (one per line)",
                        value="\n".join(mailbox['alias_names']),
                        key=f"name_aliases_{mailbox['id']}",
                        help="Alternative names for this entity (one per line)"
                    )
                    name_aliases = [alias.strip() for alias in name_aliases_text.split("\n") if alias.strip()]
                    st.session_state.project_form['mailboxes'][i]['alias_names'] = name_aliases

                with col2:
                    # Organization info section
                    st.markdown("##### Organization Information")

                    # Organization name
                    org_name = st.text_input(
                        "Organization Name",
                        value=mailbox['organization_name'],
                        key=f"org_name_{mailbox['id']}",
                        disabled=form['mode'] == 'edit',  # Can't change org name in edit mode
                        help="Name of the organization"
                    )
                    st.session_state.project_form['mailboxes'][i]['organization_name'] = org_name

                    # Organization description
                    org_desc = st.text_area(
                        "Organization Description",
                        value=mailbox['organization_description'],
                        key=f"org_desc_{mailbox['id']}",
                        help="Brief description of the organization"
                    )
                    st.session_state.project_form['mailboxes'][i]['organization_description'] = org_desc

                    # Data source selection (only in create mode)
                    if form['mode'] == 'create':
                        st.markdown("##### Email Data Source")

                        # Data source selection
                        data_source = st.selectbox(
                            "Choose data source",
                            ["upload", "s3"],
                            index=0 if mailbox.get('data_source', 'upload') == 'upload' else 1,
                            key=f"data_source_{mailbox['id']}",
                            format_func=lambda x: "📁 Upload local files" if x == "upload" else "☁️ Download from S3",
                            help="Choose whether to upload new files or download from existing S3 projects"
                        )
                        st.session_state.project_form['mailboxes'][i]['data_source'] = data_source

                        if data_source == 'upload':
                            # Local file upload
                            st.write("Upload mailbox data files (.pst, .eml, .mbox, .zip)")
                            uploaded_files = st.file_uploader(
                                "Drag and drop files here",
                                accept_multiple_files=True,
                                type=['pst', 'eml', 'mbox', 'zip'],
                                key=f"files_{mailbox['id']}",
                                help="Upload email archive files for this mailbox"
                            )

                            if uploaded_files:
                                st.session_state.project_form['mailboxes'][i]['files'] = uploaded_files
                                # Show list of uploaded files
                                st.write("📁 Uploaded files:")
                                for file in uploaded_files:
                                    file_size = round(file.size/1024/1024, 2) if file.size > 1024*1024 else round(file.size/1024, 2)
                                    size_unit = "MB" if file.size > 1024*1024 else "KB"
                                    st.text(f"- {file.name} ({file_size} {size_unit})")
                            else:
                                st.session_state.project_form['mailboxes'][i]['files'] = []

                        else:  # S3 source
                            # S3 project selection
                            try:
                                with st.spinner("Loading S3 projects..."):
                                    s3_handler = S3Handler()
                                    available_projects = s3_handler.list_directories(
                                        bucket_name="olkoa-projects"
                                    )

                                if available_projects:
                                    selected_project = st.selectbox(
                                        "Select S3 project to download from",
                                        [""] + available_projects,
                                        index=0 if not mailbox.get('s3_project_name') else available_projects.index(mailbox.get('s3_project_name', '')) + 1 if mailbox.get('s3_project_name') in available_projects else 0,
                                        key=f"s3_project_{mailbox['id']}",
                                        help="Choose which existing S3 project to download data from"
                                    )
                                    st.session_state.project_form['mailboxes'][i]['s3_project_name'] = selected_project

                                    if selected_project:
                                        st.success(f"☁️ Will download data from S3 project: {selected_project}")
                                        st.info(f"📁 Data will be downloaded to: {mailbox_name}/raw/")
                                    else:
                                        st.warning("Please select an S3 project to download from")
                                else:
                                    st.warning("No S3 projects found in 'olkoa-projects' bucket")
                                    st.info("💡 Upload files first using the upload mode to create S3 projects")

                            except Exception as e:
                                st.error(f"Failed to load S3 projects: {e}")
                                st.info("💡 Make sure S3 credentials are configured and the bucket exists")

                            # Clear files since we're using S3
                            st.session_state.project_form['mailboxes'][i]['files'] = []

                    else:
                        st.markdown("##### Email Data Files")
                        st.info("Files cannot be uploaded when editing a project. Use the file system to add files directly to the project's raw folder.")

                # Positions section
                st.markdown("##### Positions")
                for j, position in enumerate(mailbox['positions']):
                    pos_cols = st.columns([3, 2, 2, 3, 1])

                    # Position title
                    with pos_cols[0]:
                        pos_title = st.text_input(
                            "Title",
                            value=position['title'],
                            key=f"pos_title_{mailbox['id']}_{position['id']}",
                            label_visibility="collapsed",
                            placeholder="Position Title"
                        )
                        st.session_state.project_form['mailboxes'][i]['positions'][j]['title'] = pos_title

                    # Start date
                    with pos_cols[1]:
                        start_date = st.text_input(
                            "Start Date",
                            value=position['start_date'],
                            key=f"start_date_{mailbox['id']}_{position['id']}",
                            label_visibility="collapsed",
                            placeholder="Start Date (YYYY-MM-DD)"
                        )
                        st.session_state.project_form['mailboxes'][i]['positions'][j]['start_date'] = start_date

                    # End date
                    with pos_cols[2]:
                        end_date = st.text_input(
                            "End Date",
                            value=position['end_date'],
                            key=f"end_date_{mailbox['id']}_{position['id']}",
                            label_visibility="collapsed",
                            placeholder="End Date (YYYY-MM-DD)"
                        )
                        st.session_state.project_form['mailboxes'][i]['positions'][j]['end_date'] = end_date

                    # Description
                    with pos_cols[3]:
                        description = st.text_input(
                            "Description",
                            value=position['description'],
                            key=f"pos_desc_{mailbox['id']}_{position['id']}",
                            label_visibility="collapsed",
                            placeholder="Position Description"
                        )
                        st.session_state.project_form['mailboxes'][i]['positions'][j]['description'] = description

                    # Remove button
                    with pos_cols[4]:
                        if len(mailbox['positions']) > 1:
                            if st.button("🗑️", key=f"del_pos_{mailbox['id']}_{position['id']}", help="Remove position"):
                                remove_position(i, j)
                                st.rerun()

                # Button to add a new position
                if st.button("Add Position", key=f"add_pos_{mailbox['id']}"):
                    add_position(i)
                    st.rerun()

                # Remove mailbox button (only if more than 1 mailbox)
                if len(form['mailboxes']) > 1:
                    if st.button("Remove Mailbox", key=f"remove_mb_{mailbox['id']}"):
                        remove_mailbox(i)
                        st.rerun()

        # Button to add a new mailbox (max 5)
        if len(form['mailboxes']) < 5:
            if st.button("Add Mailbox", type="primary"):
                add_mailbox()
                st.rerun()
        else:
            st.info("Maximum of 5 mailboxes reached.")

        # Save button and cancelation
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("Save Project", type="primary", use_container_width=True):
                if save_project():
                    st.success("Project saved successfully!")
                    # Clear form and go back to project list after short delay
                    reset_form()
                    st.rerun()

        with col2:
            if st.button("Cancel", use_container_width=True):
                reset_form()
                st.rerun()

        with col3:
            if form['mode'] == 'edit':
                # Add delete option (disabled by default)
                enable_delete = st.checkbox("Enable project deletion", value=False)
                if enable_delete:
                    if st.button("Delete Project", type="primary", use_container_width=True):
                        # Here we would implement actual deletion logic
                        st.warning("Delete functionality is currently disabled for safety.")
                        # In a real implementation:
                        # 1. Mark the project as deactivated
                        # 2. Optionally move it to an archive folder
                        # 3. Update UI to reflect the change
