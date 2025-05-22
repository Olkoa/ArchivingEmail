"""
Export DuckDB data to Parquet files for use in Google Colab.
"""

import os
import sys
import duckdb
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from constants import ACTIVE_PROJECT

def export_duckdb_to_parquet(project_name: str = None):
    """
    Export all tables from DuckDB to Parquet files.
    
    Args:
        project_name: Name of the project (uses ACTIVE_PROJECT if None)
    """
    if project_name is None:
        project_name = ACTIVE_PROJECT
    
    # Paths
    db_path = os.path.join(project_root, 'data', 'Projects', project_name, f"{project_name}.duckdb")
    export_dir = os.path.join(project_root, 'data', 'Projects', project_name, 'parquet_export')
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    # Connect to DuckDB
    conn = duckdb.connect(db_path)
    
    try:
        # Get list of all tables
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"Found {len(tables)} tables in {project_name}.duckdb:")
        
        for table_info in tables:
            table_name = table_info[0]
            print(f"  - {table_name}")
            
            # Export each table to parquet
            parquet_path = os.path.join(export_dir, f"{table_name}.parquet")
            
            # DuckDB direct export to parquet
            export_query = f"COPY {table_name} TO '{parquet_path}' (FORMAT PARQUET)"
            conn.execute(export_query)
            
            print(f"    ✅ Exported to {parquet_path}")
            
            # Get table info
            count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = count_result[0] if count_result else 0
            print(f"    📊 {row_count:,} rows")
        
        print(f"\n🎉 All tables exported to: {export_dir}")
        return export_dir
        
    finally:
        conn.close()

def export_rag_dataset_to_parquet(project_name: str = None, limit: int = None):
    """
    Export specifically the RAG email dataset to Parquet.
    
    Args:
        project_name: Name of the project (uses ACTIVE_PROJECT if None)
        limit: Limit number of rows (None for all)
    """
    if project_name is None:
        project_name = ACTIVE_PROJECT
    
    # Import EmailAnalyzer
    from src.data.email_analyzer import EmailAnalyzer
    
    # Paths
    db_path = os.path.join(project_root, 'data', 'Projects', project_name, f"{project_name}.duckdb")
    export_dir = os.path.join(project_root, 'data', 'Projects', project_name, 'parquet_export')
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    # Get RAG dataset
    email_analyzer = EmailAnalyzer(db_path)
    
    print(f"🔄 Extracting RAG email dataset...")
    if limit:
        print(f"   Limited to {limit:,} rows")
        rag_df = email_analyzer.get_rag_email_dataset(limit=limit)
    else:
        print("   Getting all available rows")
        rag_df = email_analyzer.get_rag_email_dataset()
    
    # Export to parquet
    parquet_path = os.path.join(export_dir, "rag_email_dataset.parquet")
    rag_df.to_parquet(parquet_path, index=False)
    
    print(f"✅ RAG dataset exported to: {parquet_path}")
    print(f"📊 {len(rag_df):,} rows, {len(rag_df.columns)} columns")
    print(f"📁 File size: {os.path.getsize(parquet_path) / (1024*1024):.1f} MB")
    
    return parquet_path

if __name__ == "__main__":
    print("="*60)
    print("DuckDB to Parquet Export Tool")
    print("="*60)
    
    # Export all tables
    print("\n1️⃣ Exporting all database tables...")
    export_dir = export_duckdb_to_parquet()
    
    # Export RAG dataset specifically
    print("\n2️⃣ Exporting RAG email dataset...")
    rag_parquet = export_rag_dataset_to_parquet(limit=50000)  # Adjust limit as needed
    
    print("\n" + "="*60)
    print("EXPORT COMPLETE!")
    print("="*60)
    print(f"📂 All exports saved to: {export_dir}")
    print(f"🚀 Ready for Google Colab!")
    print("\nFiles to upload to Colab:")
    
    # List all exported files
    for file in os.listdir(export_dir):
        if file.endswith('.parquet'):
            file_path = os.path.join(export_dir, file)
            size_mb = os.path.getsize(file_path) / (1024*1024)
            print(f"  - {file} ({size_mb:.1f} MB)")
