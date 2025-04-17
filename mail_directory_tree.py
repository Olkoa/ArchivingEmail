import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np
from urllib.parse import quote

def create_interactive_folder_viz(df, folder_column='folders', count_column=None,
                                 base_url="test"):
    """
    Creates an interactive folder visualization where users can click on folders
    to navigate to different pages in the Streamlit app.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing the folder data
    folder_column : str, default='folders'
        Name of the column containing folder paths
    count_column : str or None, default=None
        Name of the column containing counts. If None, will use value_counts
    base_url : str, default="test"
        Base URL path for navigation

    Returns:
    --------
    plotly figure object
    """
    # Get folder counts
    if count_column is None:
        folder_counts = df[folder_column].value_counts()
    else:
        # If count column is provided, group by folder and sum
        folder_counts = df.groupby(folder_column)[count_column].sum()

    # Convert to DataFrame for processing
    folder_df = pd.DataFrame({
        'path': folder_counts.index,
        'count': folder_counts.values
    })

    # Process data for sunburst chart
    def process_for_sunburst(folder_df):
        # Create a list to hold the processed data
        processed_data = []

        for _, row in folder_df.iterrows():
            path = row['path']
            count = row['count']

            # Split the path into components
            parts = path.split('/')

            # Process each level of the path
            current_path = ""
            for i, part in enumerate(parts):
                if i == 0:
                    parent = ""
                else:
                    parent = '/'.join(parts[:i])

                if current_path:
                    current_path += "/" + part
                else:
                    current_path = part

                # Only add the count to the leaf node
                node_count = count if current_path == path else 0

                processed_data.append({
                    'id': current_path,
                    'parent': parent,
                    'name': part,
                    'count': node_count,
                    'depth': i+1
                })

        # Convert to DataFrame
        result = pd.DataFrame(processed_data)

        # Aggregate duplicate entries (same id)
        if not result.empty:
            result = result.groupby(['id', 'parent', 'name', 'depth']).sum().reset_index()

        return result

    # Process the data
    sunburst_data = process_for_sunburst(folder_df)

    if sunburst_data.empty:
        st.error("No folder data to visualize.")
        return None

    # Create URL for each folder
    sunburst_data['url'] = sunburst_data['id'].apply(
        lambda x: f"{base_url}/{quote(x)}" if x else ""
    )

    # Define color scheme
    folder_types = {
        'Boîte de réception': '#4285F4',
        'Inbox': '#4285F4',
        'Éléments envoyés': '#34A853',
        'Sent': '#34A853',
        'Brouillons': '#FBBC05',
        'Drafts': '#FBBC05',
        'Éléments supprimés': '#EA4335',
        'Trash': '#EA4335',
        'Courrier indésirable': '#8E24AA',
        'Spam': '#8E24AA',
        'Archive': '#0097A7'
    }

    # Assign colors based on folder name
    def assign_folder_color(name):
        for folder_type, color in folder_types.items():
            if folder_type.lower() in name.lower():
                return color
        return '#78909C'  # Default color

    sunburst_data['color'] = sunburst_data['name'].apply(assign_folder_color)

    # Create labels with counts
    sunburst_data['label'] = sunburst_data.apply(
        lambda row: f"{row['name']} ({row['count']})" if row['count'] > 0 else row['name'],
        axis=1
    )

    # Create the sunburst chart
    fig = go.Figure(go.Sunburst(
        ids=sunburst_data['id'],
        labels=sunburst_data['label'],
        parents=sunburst_data['parent'],
        values=sunburst_data['count'].apply(lambda x: max(x, 1)),  # Ensure non-zero values for visibility
        branchvalues='total',
        marker=dict(
            colors=sunburst_data['color'],
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{label}</b><br>Path: %{id}<br>Emails: %{value}<extra></extra>',
        customdata=sunburst_data['url']  # Store URLs in customdata
    ))

    # Update layout
    fig.update_layout(
        title="Interactive Email Folder Structure",
        margin=dict(t=30, l=0, r=0, b=0),
        height=700,
        uniformtext=dict(minsize=10, mode='hide'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

# For Streamlit implementation
def interactive_folder_navigator():
    st.title("Email Folder Navigator")

    # Sample data - replace with your actual data
    data = {
        "celine.guyon/Boîte de réception": 12499,
        "celine.guyon/Éléments envoyés": 5559,
        "celine.guyon/Boîte de réception/Archives calssifiees": 423,
        "celine.guyon/Éléments supprimés": 277,
        "celine.guyon/Boîte de réception/gestioncrise": 75,
        "celine.guyon/Boîte de réception/Instances": 60,
        "celine.guyon/Courrier indésirable": 45,
        "celine.guyon/Brouillons": 41,
        "celine.guyon/Boîte de réception/RH": 40,
        "celine.guyon/Boîte de réception/Plaidoyer": 38,
        "celine.guyon/Boîte de réception/gestioncrise/Ateliers": 28,
        "root": 20,
        "celine.guyon/Boîte de réception/Idees": 18,
        "celine.guyon/Archive": 10,
        "celine.guyon/Boîte de réception/Gazette": 10,
        "celine.guyon/Boîte de réception/AG": 6,
        "celine.guyon/Boîte de réception/Conflit": 6,
        "celine.guyon/Boîte de réception/Formation à distance": 2
    }

    # Create DataFrame
    df = pd.DataFrame({'folders': list(data.keys()), 'count': list(data.values())})

    # Create the visualization
    fig = create_interactive_folder_viz(df, folder_column='folders', count_column='count')

    # Display instructions
    st.info("📌 Click on any folder to view its emails")

    # Add a callback for clicking on the chart
    selected_folder = st.plotly_chart(fig, use_container_width=True, key="folder_chart")

    # Read and handle click events with JavaScript
    st.markdown("""
    <script>
        // Wait for the chart to be fully loaded
        const waitForElement = setInterval(function() {
            const plot = document.querySelector('.js-plotly-plot');
            if (plot) {
                clearInterval(waitForElement);

                // Add click event listener
                plot.on('plotly_click', function(data) {
                    const pointData = data.points[0];
                    const folderUrl = pointData.customdata;

                    // Navigate to the folder URL
                    if (folderUrl) {
                        window.location.href = folderUrl;
                    }
                });
            }
        }, 100);
    </script>
    """, unsafe_allow_html=True)

    # Optional: Add current path parameter processing
    current_path = st.experimental_get_query_params().get("path", [""])[0]

    if current_path:
        st.subheader(f"Emails in: {current_path}")
        # Here you would load emails for the selected folder
        st.write(f"Loading emails for folder: {current_path}")


####################################
####################################
####################################
####################################
####################################

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np
from urllib.parse import quote

def create_interactive_folder_viz(df, folder_column='folders', count_column=None):
    """
    Creates an interactive folder visualization that works with Streamlit's click detection.
    """
    # Same data processing code as before...

    # Get folder counts
    if count_column is None:
        folder_counts = df[folder_column].value_counts()
    else:
        folder_counts = df.groupby(folder_column)[count_column].sum()

    # Convert to DataFrame for processing
    folder_df = pd.DataFrame({
        'path': folder_counts.index,
        'count': folder_counts.values
    })

    # Process data for sunburst chart - similar to previous function
    # [data processing code...]

    # Create the sunburst chart
    fig = go.Figure(go.Sunburst(
        ids=sunburst_data['id'],
        labels=sunburst_data['label'],
        parents=sunburst_data['parent'],
        values=sunburst_data['count'].apply(lambda x: max(x, 1)),
        branchvalues='total',
        marker=dict(
            colors=sunburst_data['color'],
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{label}</b><br>Path: %{id}<br>Emails: %{value}<extra></extra>',
    ))

    # Update layout
    fig.update_layout(
        title="Interactive Email Folder Structure",
        margin=dict(t=30, l=0, r=0, b=0),
        height=700
    )

    return fig, sunburst_data['id'].tolist()

# Main Streamlit App
def folder_navigator_app():
    st.title("Email Folder Navigator")

    # Initialize session state to keep track of selected folder
    if 'selected_folder' not in st.session_state:
        st.session_state.selected_folder = None

    # Sample data
    data = {
        "celine.guyon/Boîte de réception": 12499,
        "celine.guyon/Éléments envoyés": 5559,
        # [other data...]
    }

    # Create DataFrame
    df = pd.DataFrame({'folders': list(data.keys()), 'count': list(data.values())})

    # Create the visualization
    fig, folder_ids = create_interactive_folder_viz(df, folder_column='folders', count_column='count')

    # Display visualization and capture clicks
    st.info("📌 Click on any folder to view its emails")

    # Display the chart and get click data
    clicked_point = plotly_events(fig, click_event=True, hover_event=False)

    # Process click data
    if clicked_point:
        # The clicked point contains the data for the clicked section
        clicked_id = clicked_point[0].get('id')
        if clicked_id in folder_ids:
            st.session_state.selected_folder = clicked_id
            # Use Streamlit's navigation to change URL
            st.experimental_set_query_params(folder=clicked_id)

    # Show content based on selected folder
    if st.session_state.selected_folder:
        selected_folder = st.session_state.selected_folder
        st.subheader(f"Emails in: {selected_folder}")

        # Here you would load and display emails for the selected folder
        # This is where you'd implement your email display logic
        st.write(f"Displaying emails for folder: {selected_folder}")

        # You could add a dataframe of emails here
        emails_df = load_emails_for_folder(selected_folder)  # You'd implement this function
        st.dataframe(emails_df)

####################################
####################################
####################################
####################################
####################################

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

def create_folder_visualization(df, folder_column='folders', count_column=None):
    """
    Creates a folder visualization with Plotly for Streamlit.
    Returns the figure and processed data.
    """
    # Data processing code...
    # [same as before]

    # Return both the figure and the processed data
    return fig, sunburst_data

def folder_navigator():
    st.title("Email Folder Navigator")

    # Sample data
    data = {
        "celine.guyon/Boîte de réception": 12499,
        "celine.guyon/Éléments envoyés": 5559,
        # [other folders...]
    }

    # Create DataFrame
    df = pd.DataFrame({'folders': list(data.keys()), 'count': list(data.values())})

    # Create visualization
    fig, folder_data = create_folder_visualization(df, folder_column='folders', count_column='count')

    # Sidebar for folder selection
    st.sidebar.header("Folder Navigation")

    # Create a hierarchical dropdown for folder selection
    top_level_folders = folder_data[folder_data['depth'] == 1]['name'].unique()
    selected_top = st.sidebar.selectbox("Main Folder", options=top_level_folders)

    # Get the ID of the selected top folder
    top_id = folder_data[folder_data['name'] == selected_top]['id'].iloc[0]

    # Filter subfolders based on the selected top folder
    sub_folders = folder_data[
        (folder_data['parent'] == top_id) &
        (folder_data['count'] > 0)
    ]

    if not sub_folders.empty:
        selected_sub = st.sidebar.selectbox(
            "Sub Folder",
            options=sub_folders['name'].tolist(),
            format_func=lambda x: f"{x} ({sub_folders[sub_folders['name']==x]['count'].iloc[0]})"
        )

        # Get the complete path of the selected subfolder
        selected_path = sub_folders[sub_folders['name'] == selected_sub]['id'].iloc[0]
    else:
        selected_path = top_id

    # Display the visualization
    st.plotly_chart(fig, use_container_width=True)

    # Display emails for the selected folder
    st.header(f"Emails in: {selected_path}")

    # Here you would implement your email loading and display logic
    # Example:
    # emails = load_emails_for_folder(selected_path)
    # st.dataframe(emails)

    # Create a button to navigate to a dedicated page
    if st.button(f"View all emails in {selected_path}"):
        # You could use this to set query parameters or redirect
        st.experimental_set_query_params(folder=selected_path)
        st.experimental_rerun()

# Check for folder parameter in URL
query_params = st.experimental_get_query_params()
selected_folder = query_params.get("folder", [None])[0]

if selected_folder:
    # Display the emails for the selected folder
    st.title(f"Emails in {selected_folder}")
    # Your email display code here
else:
    # Show the navigator
    folder_navigator()

####################################
####################################
####################################
####################################
####################################

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np

def create_interactive_folder_treemap(df, folder_column='folders', count_column=None):
    """
    Creates an interactive treemap visualization that works well in Streamlit.
    """
    # Get folder counts
    if count_column is None:
        folder_counts = df[folder_column].value_counts()
    else:
        folder_counts = df.groupby(folder_column)[count_column].sum()

    # Process data for treemap
    data = []

    for path, count in folder_counts.items():
        parts = path.split('/')
        depth = len(parts)

        # Create hierarchy
        for i in range(depth):
            current_path = '/'.join(parts[:i+1])
            parent = '/'.join(parts[:i]) if i > 0 else ''

            # Only assign count to the complete path
            value = count if current_path == path else 0

            data.append({
                'path': current_path,
                'parent': parent,
                'name': parts[i],
                'count': value,
                'depth': i+1
            })

    # Convert to DataFrame and group duplicates
    tree_df = pd.DataFrame(data)
    if not tree_df.empty:
        tree_df = tree_df.groupby(['path', 'parent', 'name', 'depth']).sum().reset_index()

    # Calculate total for each path (sum of all children and self)
    path_totals = {}

    # Start with leaf nodes
    for _, row in tree_df.sort_values('depth', ascending=False).iterrows():
        path = row['path']
        count = row['count']
        parent = row['parent']

        # Initialize if not exists
        if path not in path_totals:
            path_totals[path] = count
        else:
            path_totals[path] += count

        # Add to parent
        if parent and parent in path_totals:
            path_totals[parent] += count

    # Add total counts back to DataFrame
    tree_df['total'] = tree_df['path'].map(path_totals)

    # Create treemap data
    labels = tree_df['name'].tolist()
    parents = tree_df['parent'].tolist()
    ids = tree_df['path'].tolist()
    values = tree_df['total'].apply(lambda x: max(x, 1)).tolist()  # Ensure minimum size

    # Create custom hover text
    hover_text = []
    for _, row in tree_df.iterrows():
        hover_text.append(
            f"<b>{row['name']}</b><br>" +
            f"Path: {row['path']}<br>" +
            f"Emails: {row['total']}"
        )

    # Create color mapping
    folder_colors = {
        'Boîte de réception': '#4285F4',
        'Inbox': '#4285F4',
        'Éléments envoyés': '#34A853',
        'Sent': '#34A853',
        'Brouillons': '#FBBC05',
        'Drafts': '#FBBC05',
        'Éléments supprimés': '#EA4335',
        'Trash': '#EA4335',
        'Courrier indésirable': '#8E24AA',
        'Spam': '#8E24AA',
        'Archive': '#0097A7'
    }

    # Assign colors
    colors = []
    for name in tree_df['name']:
        for folder_type, color in folder_colors.items():
            if folder_type.lower() in name.lower():
                colors.append(color)
                break
        else:
            colors.append('#78909C')  # Default color

    # Create treemap
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        ids=ids,
        values=values,
        branchvalues="total",
        marker=dict(
            colors=colors,
            line=dict(width=1, color='white')
        ),
        text=[f"{count}" for count in tree_df['total']],
        hovertext=hover_text,
        hoverinfo="text",
        textinfo="label+text"
    ))

    # Update layout
    fig.update_layout(
        title="Email Folder Structure <br><sup>Click on any folder to view its emails</sup>",
        margin=dict(t=50, l=0, r=0, b=0),
        font=dict(family="Arial", size=12),
        height=700,
        colorway=list(folder_colors.values())
    )

    return fig, tree_df

def main():
    st.title("Email Folder Explorer")

    # Sample data
    data = {
        "celine.guyon/Boîte de réception": 12499,
        "celine.guyon/Éléments envoyés": 5559,
        "celine.guyon/Boîte de réception/Archives calssifiees": 423,
        "celine.guyon/Éléments supprimés": 277,
        "celine.guyon/Boîte de réception/gestioncrise": 75,
        "celine.guyon/Boîte de réception/Instances": 60,
        "celine.guyon/Courrier indésirable": 45,
        "celine.guyon/Brouillons": 41,
        "celine.guyon/Boîte de réception/RH": 40,
        "celine.guyon/Boîte de réception/Plaidoyer": 38,
        "celine.guyon/Boîte de réception/gestioncrise/Ateliers": 28,
        "root": 20,
        "celine.guyon/Boîte de réception/Idees": 18,
        "celine.guyon/Archive": 10,
        "celine.guyon/Boîte de réception/Gazette": 10,
        "celine.guyon/Boîte de réception/AG": 6,
        "celine.guyon/Boîte de réception/Conflit": 6,
        "celine.guyon/Boîte de réception/Formation à distance": 2
    }

    # Create DataFrame
    df = pd.DataFrame({'folders': list(data.keys()), 'count': list(data.values())})

    # Create the visualization
    fig, folder_data = create_interactive_folder_treemap(df)

    # Add info message
    st.info("👆 Click on any folder in the visualization to view its emails")

    # Display the treemap
    selected_points = st.plotly_chart(fig, use_container_width=True, key="folder_viz")

    # Handle click events
    if "clickData" in st.session_state:
        clicked_folder = st.session_state.clickData["points"][0]["id"]

        # Show emails for the selected folder
        st.header(f"Emails in folder: {clicked_folder}")

        # Here you would load and display the emails
        # For example:
        st.write(f"Found {folder_data[folder_data['path'] == clicked_folder]['total'].iloc[0]} emails")

        # Create a button to navigate to a dedicated page
        if st.button("View in dedicated page"):
            # Navigate to a new page
            st.experimental_set_query_params(folder=clicked_folder)
            st.experimental_rerun()

    # URL parameter processing
    query_params = st.experimental_get_query_params()
    if "folder" in query_params:
        selected_folder = query_params["folder"][0]

        # Display folder contents
        st.title(f"Folder: {selected_folder}")

        # Load and display emails for this folder
        # Your code to load emails goes here

        # Add a back button
        if st.button("← Back to folder explorer"):
            st.experimental_set_query_params()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
