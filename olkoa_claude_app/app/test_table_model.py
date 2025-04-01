import streamlit as st
from streamlit_modal import Modal
import pandas as pd

# Set page title
st.title("Table with Modal Example")

# Sample data for the table
data = {
    "Name": ["Alice", "Bob", "Charlie", "David", "Eva"],
    "Age": [28, 34, 42, 25, 31]
}

# Create DataFrame
df = pd.DataFrame(data)

# Add an action column with buttons
df['Action'] = ['View Age' for _ in range(len(df))]

# Create a session state to track which person's age modal is being shown
if 'show_modal' not in st.session_state:
    st.session_state.show_modal = None

# Display table with clickable buttons
st.write("### People Table")
for index, row in df.iterrows():
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(row['Name'])
    
    with col2:
        # Empty column where age would normally be displayed
        st.write("")
    
    with col3:
        # Create a unique button for each row
        if st.button(f"View Age", key=f"view_age_{index}"):
            st.session_state.show_modal = index

# Show modal if a button was clicked
if st.session_state.show_modal is not None:
    # Get the index of the person whose details should be shown
    index = st.session_state.show_modal
    
    # Create and configure the modal
    modal = Modal(
        f"Age Details", 
        key=f"age_modal_{index}"
    )
    
    # Modal content
    with modal.container():
        st.write(f"### {df.iloc[index]['Name']}'s Age")
        st.write(f"**Age:** {df.iloc[index]['Age']}")
        
        if st.button("Close", key=f"close_modal_{index}"):
            st.session_state.show_modal = None
            st.rerun()
