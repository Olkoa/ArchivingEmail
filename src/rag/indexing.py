"""
Indexing functionality for the Okloa RAG system.

This module provides functions for creating and maintaining indexes
from email content, which can then be used for retrieval in the RAG system.
"""

import os
import pandas as pd
import numpy as np
import torch
from typing import List, Dict, Union, Optional, Any
from transformers import AutoTokenizer, AutoModel
import faiss
import pickle
import json

# Load environment variable or set default model
COLBERT_MODEL = os.environ.get('COLBERT_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

class ColBERTIndexer:
    """ColBERT-based indexer for email content."""
    
    def __init__(self, model_name: str = COLBERT_MODEL, max_length: int = 512):
        """
        Initialize the ColBERT indexer.
        
        Args:
            model_name: Name of the pretrained model to use
            max_length: Maximum sequence length for the tokenizer
        """
        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
        
        # Placeholders for index data
        self.document_embeddings = None
        self.document_ids = None
        self.document_texts = None
        self.faiss_index = None
        
    def _prepare_documents(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Prepare documents from DataFrame for indexing.
        
        Args:
            df: DataFrame containing email data
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        for _, row in df.iterrows():
            # Create document for email body
            if pd.notna(row.get('body')) and row.get('body'):
                doc = {
                    'id': f"{row.get('message_id', 'unknown')}_body",
                    'text': row.get('body', ''),
                    'metadata': {
                        'message_id': row.get('message_id', 'unknown'),
                        'date': row.get('date'),
                        'from': row.get('from', ''),
                        'to': row.get('to', ''),
                        'subject': row.get('subject', ''),
                        'direction': row.get('direction', ''),
                        'mailbox': row.get('mailbox', ''),
                        'type': 'body'
                    }
                }
                documents.append(doc)
                
            # Create separate document for subject
            if pd.notna(row.get('subject')) and row.get('subject'):
                doc = {
                    'id': f"{row.get('message_id', 'unknown')}_subject",
                    'text': row.get('subject', ''),
                    'metadata': {
                        'message_id': row.get('message_id', 'unknown'),
                        'date': row.get('date'),
                        'from': row.get('from', ''),
                        'to': row.get('to', ''),
                        'subject': row.get('subject', ''),
                        'direction': row.get('direction', ''),
                        'mailbox': row.get('mailbox', ''),
                        'type': 'subject'
                    }
                }
                documents.append(doc)
                
        return documents
    
    def _encode_documents(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """
        Encode documents using ColBERT.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Document embeddings matrix
        """
        document_texts = [doc['text'] for doc in documents]
        embeddings = []
        
        # Process in batches to avoid OOM
        batch_size = 8
        
        for i in range(0, len(document_texts), batch_size):
            batch_texts = document_texts[i:i+batch_size]
            
            inputs = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=self.max_length,
                return_tensors='pt'
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embeddings for the document representation
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.append(batch_embeddings)
                
        # Concatenate all batches
        return np.vstack(embeddings)
    
    def _encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query using ColBERT.
        
        Args:
            query: Query string
            
        Returns:
            Query embedding vector
        """
        inputs = self.tokenizer(
            query, 
            padding=True, 
            truncation=True, 
            max_length=self.max_length,
            return_tensors='pt'
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token embedding for the query representation
            query_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
        return query_embedding
    
    def build_index(self, df: pd.DataFrame) -> None:
        """
        Build the index from email DataFrame.
        
        Args:
            df: DataFrame containing email data
        """
        # Prepare documents
        documents = self._prepare_documents(df)
        if not documents:
            raise ValueError("No valid documents found in the DataFrame")
        
        # Store document texts and IDs
        self.document_texts = [doc['text'] for doc in documents]
        self.document_ids = [doc['id'] for doc in documents]
        self.document_metadata = [doc['metadata'] for doc in documents]
        
        # Encode documents
        self.document_embeddings = self._encode_documents(documents)
        
        # Build FAISS index
        dimension = self.document_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(self.document_embeddings)
        
        # Add vectors to the index
        self.faiss_index.add(self.document_embeddings)
        
    def save_index(self, output_dir: str) -> None:
        """
        Save the index to files.
        
        Args:
            output_dir: Directory to save the index
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.faiss_index, os.path.join(output_dir, 'faiss_index.bin'))
        
        # Save document texts, IDs, and metadata
        with open(os.path.join(output_dir, 'document_texts.pkl'), 'wb') as f:
            pickle.dump(self.document_texts, f)
            
        with open(os.path.join(output_dir, 'document_ids.pkl'), 'wb') as f:
            pickle.dump(self.document_ids, f)
            
        with open(os.path.join(output_dir, 'document_metadata.pkl'), 'wb') as f:
            pickle.dump(self.document_metadata, f)
            
        # Save model info
        model_info = {
            'model_name': self.model_name,
            'max_length': self.max_length
        }
        
        with open(os.path.join(output_dir, 'model_info.json'), 'w') as f:
            json.dump(model_info, f)
            
    def load_index(self, index_dir: str) -> None:
        """
        Load the index from files.
        
        Args:
            index_dir: Directory containing the index files
        """
        # Load FAISS index
        self.faiss_index = faiss.read_index(os.path.join(index_dir, 'faiss_index.bin'))
        
        # Load document texts, IDs, and metadata
        with open(os.path.join(index_dir, 'document_texts.pkl'), 'rb') as f:
            self.document_texts = pickle.load(f)
            
        with open(os.path.join(index_dir, 'document_ids.pkl'), 'rb') as f:
            self.document_ids = pickle.load(f)
            
        with open(os.path.join(index_dir, 'document_metadata.pkl'), 'rb') as f:
            self.document_metadata = pickle.load(f)
            
        # Load model info
        with open(os.path.join(index_dir, 'model_info.json'), 'r') as f:
            model_info = json.load(f)
            
        # Update model if different
        if model_info['model_name'] != self.model_name:
            self.model_name = model_info['model_name']
            self.max_length = model_info['max_length']
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()


def create_email_index(
    df: pd.DataFrame, 
    output_dir: str, 
    model_name: str = COLBERT_MODEL
) -> None:
    """
    Create an index from email DataFrame and save it to disk.
    
    Args:
        df: DataFrame containing email data
        output_dir: Directory to save the index
        model_name: Name of the model to use for indexing
    """
    # Initialize indexer
    indexer = ColBERTIndexer(model_name=model_name)
    
    # Build index
    indexer.build_index(df)
    
    # Save index
    indexer.save_index(output_dir)
    
    
if __name__ == "__main__":
    # Test code for indexing
    import pandas as pd
    from src.data.loading import load_mailboxes
    import os
    
    # Load sample data
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    base_dir = os.path.join(project_root, 'data', 'raw')
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)
    
    # Create index output directory
    index_dir = os.path.join(project_root, 'data', 'processed', 'index')
    os.makedirs(index_dir, exist_ok=True)
    
    # Create index
    create_email_index(emails_df, index_dir)
    
    print(f"Created index with {len(emails_df)} emails")
