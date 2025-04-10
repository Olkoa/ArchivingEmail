"""
Email timeline visualization for the Okloa project.

This module provides functions for creating timeline visualizations of email activity.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional


def create_timeline(df: pd.DataFrame, time_unit: str = "W") -> go.Figure:
    """
    Create a timeline visualization of email activity.
    
    Args:
        df: DataFrame containing email data with 'date' and 'direction' columns
        time_unit: Time unit for aggregation ('D' for daily, 'W' for weekly, 'M' for monthly)
        
    Returns:
        Plotly figure object
    """
    # Ensure date column is datetime
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with missing dates
    df_clean = df.dropna(subset=['date'])
    
    # Handle empty DataFrame
    if len(df_clean) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for timeline",
            showarrow=False,
            font=dict(size=20),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5
        )
        fig.update_layout(
            title="Email Activity Over Time",
            xaxis_title="Date",
            yaxis_title="Number of Emails",
            template="plotly_white"
        )
        return fig
    
    # Resample by time unit
    sent_series = (df_clean[df_clean['direction'] == 'sent']
                 .set_index('date')
                 .resample(time_unit)
                 .size())
    
    received_series = (df_clean[df_clean['direction'] == 'received']
                     .set_index('date')
                     .resample(time_unit)
                     .size())
    
    # Create common date range to ensure same length
    all_dates = pd.concat([sent_series.to_frame(), received_series.to_frame()]).index.unique()
    
    # Create a DataFrame with all dates and fill with zeros for missing values
    timeline_df = pd.DataFrame(index=all_dates)
    timeline_df['sent'] = sent_series.reindex(all_dates, fill_value=0)
    timeline_df['received'] = received_series.reindex(all_dates, fill_value=0)
    timeline_df = timeline_df.reset_index()
    timeline_df = timeline_df.rename(columns={'index': 'date'})
    timeline_df = timeline_df.sort_values('date')
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['sent'],
        mode='lines+markers',
        name='Sent',
        line=dict(color='rgba(31, 119, 180, 0.8)', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['received'],
        mode='lines+markers',
        name='Received',
        line=dict(color='rgba(255, 127, 14, 0.8)', width=2),
        marker=dict(size=8)
    ))
    
    # Add titles and labels
    time_unit_label = {
        'D': 'Daily',
        'W': 'Weekly',
        'M': 'Monthly'
    }.get(time_unit, time_unit)
    
    fig.update_layout(
        title=f'{time_unit_label} Email Activity',
        xaxis_title='Date',
        yaxis_title='Number of Emails',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_heatmap_calendar(df: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap calendar of email activity.
    
    Args:
        df: DataFrame containing email data with 'date' column
        
    Returns:
        Plotly figure object
    """
    # Ensure date column is datetime
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with missing dates
    df_clean = df.dropna(subset=['date'])
    
    # Handle empty DataFrame
    if len(df_clean) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for heatmap calendar",
            showarrow=False,
            font=dict(size=20),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5
        )
        fig.update_layout(
            title='Email Activity by Day and Month',
            xaxis_title='Month',
            yaxis_title='Day of Week',
            template='plotly_white'
        )
        return fig
    
    # Extract date components
    df_clean['day'] = df_clean['date'].dt.day_name()
    df_clean['month'] = df_clean['date'].dt.month_name()
    df_clean['week'] = df_clean['date'].dt.isocalendar().week
    
    # Count emails by day of week and month
    heatmap_data = df_clean.groupby(['day', 'month']).size().reset_index(name='count')
    
    # Define order for days and months
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months_order = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    # Create heatmap
    fig = px.density_heatmap(
        heatmap_data,
        x='month',
        y='day',
        z='count',
        category_orders={'day': days_order, 'month': months_order},
        color_continuous_scale='Blues',
        title='Email Activity by Day and Month'
    )
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Day of Week',
        template='plotly_white'
    )
    
    return fig


def create_category_timeline(df: pd.DataFrame, category_col: str) -> go.Figure:
    """
    Create a timeline visualization showing email activity by category.
    
    Args:
        df: DataFrame containing email data with 'date' and category columns
        category_col: Column name containing category information
        
    Returns:
        Plotly figure object
    """
    if category_col not in df.columns:
        raise ValueError(f"Column '{category_col}' not found in DataFrame")
    
    # Ensure date column is datetime
    if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Drop rows with missing dates or categories
    df_clean = df.dropna(subset=['date', category_col])
    
    # Group by date (monthly) and category
    monthly_counts = (df_clean
                     .set_index('date')
                     .groupby([pd.Grouper(freq='M'), category_col])
                     .size()
                     .reset_index(name='count'))
    
    # Create figure
    fig = px.line(
        monthly_counts,
        x='date',
        y='count',
        color=category_col,
        markers=True,
        title=f'Monthly Email Activity by {category_col}'
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Number of Emails',
        template='plotly_white',
        legend_title=category_col.capitalize()
    )
    
    return fig


if __name__ == "__main__":
    # Example usage
    import pandas as pd
    from src.data.loading import load_mailboxes
    
    # Load sample data
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"])
    
    # Create timeline
    fig1 = create_timeline(emails_df, time_unit="W")
    fig1.show()
    
    # Create heatmap calendar
    fig2 = create_heatmap_calendar(emails_df)
    fig2.show()