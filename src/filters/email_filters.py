"""
Filter utilities for the Olkoa project.

This module provides functions to get filter options and apply filters to email data.
"""

import streamlit as st
import pandas as pd
import os
import sys

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.email_analyzer import EmailAnalyzer


class EmailFilters:
    """Class to handle email filtering operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.analyzer = EmailAnalyzer(db_path)
    
    @st.cache_data
    def get_mailing_lists(_self, mailbox_selection=None):
        """Get available mailing lists from the database
        
        Args:
            mailbox_selection: Optional mailbox filter
            
        Returns:
            List of mailing list email addresses
        """
        try:
            conn = _self.analyzer.connect()
            
            query = """
            SELECT DISTINCT ml.email_address as mailing_list_email
            FROM receiver_emails re
            LEFT JOIN mailing_lists ml ON re.mailing_list_id = ml.id
            WHERE ml.email_address IS NOT NULL
            """
            
            # Add mailbox filter if specified
            if mailbox_selection and mailbox_selection != "All Mailboxes":
                query += f" AND re.folder = '{mailbox_selection}'"
                
            query += " ORDER BY ml.email_address"
            
            result = conn.execute(query).fetchall()
            mailing_lists = [row[0] for row in result if row[0]]
            
            return mailing_lists
            
        except Exception as e:
            print(f"Error getting mailing lists: {e}")
            return []
    
    @st.cache_data  
    def get_folders(_self, mailbox_selection=None):
        """Get available folders from the database
        
        Args:
            mailbox_selection: Optional mailbox filter
            
        Returns:
            List of folder names
        """
        try:
            conn = _self.analyzer.connect()
            
            query = """
            SELECT DISTINCT folder
            FROM receiver_emails
            WHERE folder IS NOT NULL
            """
            
            # Add mailbox filter if specified
            if mailbox_selection and mailbox_selection != "All Mailboxes":
                query += f" AND folder = '{mailbox_selection}'"
                
            query += " ORDER BY folder"
            
            result = conn.execute(query).fetchall()
            folders = [row[0] for row in result if row[0]]
            
            return folders
            
        except Exception as e:
            print(f"Error getting folders: {e}")
            return []

    def apply_filters(self, df, filters):
        """Apply multiple filters to a dataframe
        
        Args:
            df: DataFrame to filter
            filters: Dictionary containing filter criteria
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
            
        filtered_df = df.copy()
        
        # Apply mailing list filter
        if filters.get('mailing_list_email') and filters['mailing_list_email'] != 'All':
            if filters['mailing_list_email'] == 'None':
                # Filter for emails not associated with any mailing list
                # This requires checking if the email has mailing list data
                # We'll need to get this info from the comprehensive dataset
                filtered_df = self._filter_by_mailing_list(filtered_df, None)
            else:
                # Filter for specific mailing list
                filtered_df = self._filter_by_mailing_list(filtered_df, filters['mailing_list_email'])
        
        # Apply direction filter
        if filters.get('direction') and filters['direction'] != 'All':
            direction_value = 'sent' if filters['direction'] == 'Envoyé' else 'received'
            filtered_df = filtered_df[filtered_df['direction'] == direction_value]
        
        # Apply folder filter
        if filters.get('folder') and filters['folder'] != 'All':
            if 'folder' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['folder'] == filters['folder']]
            elif 'mailbox' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['mailbox'] == filters['folder']]
        
        return filtered_df
    
    def _filter_by_mailing_list(self, df, mailing_list_email):
        """Filter dataframe by mailing list
        
        This is a helper method that may need to be enhanced based on
        how mailing list data is stored in the current dataframe structure.
        """
        # For now, we'll implement a basic version
        # This might need to be enhanced based on the actual data structure
        
        if mailing_list_email is None:
            # Filter for emails NOT associated with mailing lists
            # This is a simplified approach - might need enhancement
            return df
        else:
            # Filter for specific mailing list
            # This might need to be done at the database level for accuracy
            return df

    def get_filter_summary(self, filters):
        """Generate a summary of active filters
        
        Args:
            filters: Dictionary containing filter criteria
            
        Returns:
            String describing active filters
        """
        active_filters = []
        
        if filters.get('mailing_list_email') and filters['mailing_list_email'] != 'All':
            if filters['mailing_list_email'] == 'None':
                active_filters.append("📭 Non-mailing list emails")
            else:
                active_filters.append(f"📮 Mailing list: {filters['mailing_list_email']}")
        
        if filters.get('direction') and filters['direction'] != 'All':
            direction_emoji = "📤" if filters['direction'] == 'Envoyé' else "📥"
            active_filters.append(f"{direction_emoji} Direction: {filters['direction']}")
        
        if filters.get('folder') and filters['folder'] != 'All':
            active_filters.append(f"📁 Folder: {filters['folder']}")
        
        if active_filters:
            return " • ".join(active_filters)
        else:
            return "No additional filters active"


def create_sidebar_filters(email_filters, mailbox_selection):
    """Create sidebar filter UI elements
    
    Args:
        email_filters: EmailFilters instance
        mailbox_selection: Currently selected mailbox
        
    Returns:
        Dictionary containing filter values
    """
    filters = {}
    
    # Mailing List filter
    st.sidebar.subheader("Mailing Lists")
    mailing_lists = email_filters.get_mailing_lists(mailbox_selection)
    mailing_list_options = ['All', 'None'] + mailing_lists
    
    filters['mailing_list_email'] = st.sidebar.selectbox(
        "Mailing List:",
        options=mailing_list_options,
        index=0,
        help="Filter by mailing list. 'None' shows emails not from mailing lists."
    )
    
    # Direction filter
    st.sidebar.subheader("Direction")
    direction_options = ['All', 'Envoyé', 'Reçu']
    
    filters['direction'] = st.sidebar.selectbox(
        "Direction:",
        options=direction_options,
        index=0,
        help="Filter by email direction (sent/received)"
    )
    
    # Folder filter
    st.sidebar.subheader("Folder")
    folders = email_filters.get_folders(mailbox_selection)
    folder_options = ['All'] + folders
    
    filters['folder'] = st.sidebar.selectbox(
        "Folder:",
        options=folder_options,
        index=0,
        help="Filter by folder/mailbox location"
    )
    
    return filters


def apply_all_filters(df, date_range, additional_filters, email_filters):
    """Apply all filters (date + additional) to a dataframe
    
    Args:
        df: DataFrame to filter
        date_range: Date range tuple (start_date, end_date)
        additional_filters: Dictionary with additional filter criteria
        email_filters: EmailFilters instance
        
    Returns:
        Filtered DataFrame and filter summary
    """
    # Apply date filter first (as done before)
    filtered_df = apply_date_filter(df, date_range)
    
    # Apply additional filters
    filtered_df = email_filters.apply_filters(filtered_df, additional_filters)
    
    # Generate filter summary
    filter_summary = email_filters.get_filter_summary(additional_filters)
    
    return filtered_df, filter_summary


def apply_date_filter(df, date_range):
    """Apply date range filter to a dataframe
    
    This is a copy of the function from app.py to maintain consistency
    """
    if df.empty:
        return df
        
    # Ensure date column exists and is in datetime format
    if 'date' not in df.columns:
        return df
        
    # Convert date column to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Handle different date_range formats
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]
    else:
        return df  # No valid date range provided
    
    # Convert dates to pandas Timestamp for comparison
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # End of day
    
    # Apply filter
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    return filtered_df
