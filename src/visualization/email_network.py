"""
Email network visualization for the Okloa project.

This module provides functions for creating network graphs of email communications.
"""

import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Tuple


def extract_contacts_from_df(df: pd.DataFrame) -> List[Tuple[str, str, int]]:
    """
    Extract sender-recipient pairs from email DataFrame with counts.
    
    Args:
        df: DataFrame containing email data with 'from' and 'to' columns
        
    Returns:
        List of tuples (sender, recipient, count)
    """
    # Handle multiple recipients (semicolon separated)
    edges = []
    
    for _, row in df.iterrows():
        sender = row['from']
        # Split recipients if there are multiple
        recipients = [r.strip() for r in row['to'].split(';') if r.strip()]
        
        for recipient in recipients:
            edges.append((sender, recipient))
    
    # Count frequencies
    edge_counts = {}
    for sender, recipient in edges:
        key = (sender, recipient)
        edge_counts[key] = edge_counts.get(key, 0) + 1
    
    # Convert to list of tuples
    return [(sender, recipient, count) for (sender, recipient), count in edge_counts.items()]


def create_network_graph(df: pd.DataFrame) -> go.Figure:
    """
    Create a network graph visualization of email communications.
    
    Args:
        df: DataFrame containing email data
        
    Returns:
        Plotly figure object
    """
    # Handle empty dataframe
    if len(df) == 0 or 'from' not in df.columns or 'to' not in df.columns:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for network graph",
            showarrow=False,
            font=dict(size=20),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5
        )
        fig.update_layout(
            title={
                'text': 'Email Communication Network',
                'font': {'size': 16}
            },
            showlegend=False,
            plot_bgcolor='rgba(248,248,248,1)'
        )
        return fig
        
    # Extract network edges with weights
    edges = extract_contacts_from_df(df)
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add edges with weights
    for sender, recipient, weight in edges:
        G.add_edge(sender, recipient, weight=weight)
    
    # Compute positions using a layout algorithm
    pos = nx.spring_layout(G, seed=42)
    
    # Identify internal vs external domains
    internal_domain = "archives-vaucluse.fr"
    internal_nodes = [node for node in G.nodes() if internal_domain in node]
    external_nodes = [node for node in G.nodes() if internal_domain not in node]
    
    # Calculate node sizes based on degree
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    node_size = {node: 10 + (in_degree.get(node, 0) + out_degree.get(node, 0)) * 2 
                 for node in G.nodes()}
    
    # Create edge traces
    edge_traces = []
    for sender, recipient, weight in edges:
        x0, y0 = pos[sender]
        x1, y1 = pos[recipient]
        width = 1 + weight * 0.5  # Scale width by weight
        
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=width, color='rgba(150, 150, 150, 0.6)'),
            hoverinfo='none',
            mode='lines'
        )
        edge_traces.append(edge_trace)
    
    # Create node traces for internal and external nodes
    node_trace_internal = go.Scatter(
        x=[pos[node][0] for node in internal_nodes],
        y=[pos[node][1] for node in internal_nodes],
        text=[f"{node}<br>In: {in_degree.get(node, 0)}<br>Out: {out_degree.get(node, 0)}" for node in internal_nodes],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            size=[node_size[node] for node in internal_nodes],
            color='rgba(31, 119, 180, 0.8)',
            line=dict(width=1, color='rgba(31, 119, 180, 1)')
        )
    )
    
    node_trace_external = go.Scatter(
        x=[pos[node][0] for node in external_nodes],
        y=[pos[node][1] for node in external_nodes],
        text=[f"{node}<br>In: {in_degree.get(node, 0)}<br>Out: {out_degree.get(node, 0)}" for node in external_nodes],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            size=[node_size[node] for node in external_nodes],
            color='rgba(255, 127, 14, 0.8)',
            line=dict(width=1, color='rgba(255, 127, 14, 1)')
        )
    )
    
    # Create figure
    fig = go.Figure(
        data=edge_traces + [node_trace_internal, node_trace_external],
        layout=go.Layout(
            title={
                'text': 'Email Communication Network',
                'font': {'size': 16}
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(248,248,248,1)',
            annotations=[
                dict(
                    text="Internal contacts",
                    x=0.02,
                    y=0.98,
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    bgcolor="rgba(31, 119, 180, 0.8)",
                    font=dict(color="white")
                ),
                dict(
                    text="External contacts",
                    x=0.02,
                    y=0.93,
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    bgcolor="rgba(255, 127, 14, 0.8)",
                    font=dict(color="white")
                )
            ]
        )
    )
    
    return fig


if __name__ == "__main__":
    # Example usage
    import pandas as pd
    from src.data.loading import load_mailboxes
    
    # Load sample data
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"])
    
    # Create network graph
    fig = create_network_graph(emails_df)
    
    # Show the figure
    fig.show()