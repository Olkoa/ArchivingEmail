"""
Simple export using pandas - alternative method.
"""

import os
import sys
import pandas as pd

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from constants import ACTIVE_PROJECT
from src.data.email_analyzer import EmailAnalyzer

def simple_rag_export(limit: int = 50000):
    """Simple export of RAG dataset using pandas."""
    
    # Get data
    db_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, f"{ACTIVE_PROJECT}.duckdb")
    email_analyzer = EmailAnalyzer(db_path)
    
    print(f"🔄 Getting RAG dataset (limit: {limit:,})...")
    df = email_analyzer.get_rag_email_dataset(limit=limit)
    
    # Export
    export_path = os.path.join(project_root, 'data', 'Projects', ACTIVE_PROJECT, 'rag_emails_for_colab.parquet')
    df.to_parquet(export_path, index=False)
    
    print(f"✅ Exported to: {export_path}")
    print(f"📊 Shape: {df.shape}")
    print(f"📁 Size: {os.path.getsize(export_path) / (1024*1024):.1f} MB")
    
    return export_path

if __name__ == "__main__":
    simple_rag_export()
