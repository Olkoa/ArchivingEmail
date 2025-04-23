"""
Olkoa - Interface de Gestion de Projets

Créez, modifiez et gérez vos projets d’archivage d’e-mails.
Chaque projet peut contenir plusieurs boîtes mail avec des métadonnées sur les personnes et les organisations impliquées.
"""


import streamlit as st
import os
import sys
import json
import shutil
import uuid
from datetime import datetime
import tempfile
import re

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Get project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# Page configuration
# st.set_page_config(
#     page_title="Olkoa - Project Management",
#     page_icon="📁",
#     layout="wide",
# )

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
    try:
        with open(constants_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Use regex to replace the ACTIVE_PROJECT value
        new_content = re.sub(r'ACTIVE_PROJECT = ".*?"', f'ACTIVE_PROJECT = "{project_name}"', content)

        with open(constants_path, 'w', encoding='utf-8') as file:
            file.write(new_content)

        # Update project order
        update_project_order(project_name)

        return True
    except Exception as e:
        st.error(f"Error setting active project: {str(e)}")
        return False

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

    return True

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
        'files': []
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

                # File upload section (only in create mode)
                if form['mode'] == 'create':
                    st.markdown("##### Email Data Files")
                    st.write("Upload mailbox data files (.pst, .eml, .mbox)")

                    uploaded_files = st.file_uploader(
                        "Drag and drop files here",
                        accept_multiple_files=True,
                        type=['pst', 'eml', 'mbox'],
                        key=f"files_{mailbox['id']}",
                        help="Upload email archive files for this mailbox"
                    )

                    if uploaded_files:
                        st.session_state.project_form['mailboxes'][i]['files'] = uploaded_files
                        # Show list of uploaded files
                        st.write("Uploaded files:")
                        for file in uploaded_files:
                            st.text(f"- {file.name} ({round(file.size/1024, 2)} KB)")
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
