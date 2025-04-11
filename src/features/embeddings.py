"""
Email embedding generation for the Okloa project.

This module provides functions for generating embeddings from email content,
which can be used for search, clustering, and other NLP tasks.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Union, Any
import os

# Placeholder for actual embedding model
# In a real implementation, we would use a model like Sentence-BERT
def generate_embeddings(texts: List[str], model_name: str = None) -> np.ndarray:
    """
    Generate embeddings for a list of text documents.
    
    Args:
        texts: List of text documents to embed
        model_name: Name of the embedding model to use (optional)
        
    Returns:
        Array of embeddings, shape (n_documents, embedding_dim)
    """
    # Placeholder implementation - will be replaced with actual model
    # This returns random vectors for development purposes
    embedding_dim = 384  # Common dimension for sentence embeddings
    return np.random.normal(0, 1, (len(texts), embedding_dim))


def generate_email_embeddings(df: pd.DataFrame, 
                             content_col: str = "body",
                             model_name: str = None) -> pd.DataFrame:
    """
    Generate embeddings for email content and add them to the DataFrame.
    
    Args:
        df: DataFrame containing email data
        content_col: Column name containing the text to embed
        model_name: Name of the embedding model to use (optional)
        
    Returns:
        DataFrame with added 'embedding' column
    """
    if content_col not in df.columns:
        raise ValueError(f"Column '{content_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Get list of texts to embed
    texts = result_df[content_col].fillna("").tolist()
    
    # Generate embeddings
    embeddings = generate_embeddings(texts, model_name)
    
    # Add embeddings to DataFrame
    result_df['embedding'] = list(embeddings)
    
    return result_df


def save_embeddings(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame with embeddings to a file.
    
    Args:
        df: DataFrame with 'embedding' column
        output_path: Path to save the embeddings
    """
    if 'embedding' not in df.columns:
        raise ValueError("DataFrame does not contain 'embedding' column")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert embeddings to list for serialization
    df_to_save = df.copy()
    df_to_save['embedding'] = df_to_save['embedding'].apply(lambda x: x.tolist())
    
    # Save to CSV or Parquet
    if output_path.endswith('.csv'):
        df_to_save.to_csv(output_path, index=False)
    elif output_path.endswith('.parquet'):
        df_to_save.to_parquet(output_path, index=False)
    else:
        raise ValueError("Output path must end with .csv or .parquet")


def load_embeddings(input_path: str) -> pd.DataFrame:
    """
    Load DataFrame with embeddings from a file.
    
    Args:
        input_path: Path to the saved embeddings
        
    Returns:
        DataFrame with 'embedding' column
    """
    # Load from CSV or Parquet
    if input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    elif input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    else:
        raise ValueError("Input path must end with .csv or .parquet")
    
    # Convert embeddings back to numpy arrays
    if 'embedding' in df.columns:
        df['embedding'] = df['embedding'].apply(lambda x: np.array(eval(x)) if isinstance(x, str) else np.array(x))
    
    return df


if __name__ == "__main__":
    # Example usage
    import pandas as pd
    from src.data.loading import load_mailboxes
    
    # Load sample data
    emails_df = load_mailboxes(["mailbox_1"])
    
    # Generate embeddings
    emails_with_embeddings = generate_email_embeddings(emails_df)
    
    # Display sample
    print(f"Generated embeddings of shape: {emails_with_embeddings['embedding'].iloc[0].shape}")
    
    # Save embeddings
    output_dir = os.path.join("..", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    save_embeddings(emails_with_embeddings, os.path.join(output_dir, "embeddings.parquet"))