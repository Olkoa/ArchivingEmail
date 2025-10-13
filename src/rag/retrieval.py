"""
Retrieval functionality for the Olkoa RAG system.

This module provides functions for retrieving relevant documents from the email index
and generating responses based on retrieved content.
"""

import os
import pandas as pd
import numpy as np
import torch
from typing import List, Dict, Union, Optional, Any, Tuple
import pickle
import json
import faiss
from transformers import AutoTokenizer, AutoModel
import textwrap

from .indexing import ColBERTIndexer

# Load environment variables or set defaults
COLBERT_MODEL = os.environ.get('COLBERT_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')


class ColBERTRetriever:
    """ColBERT-based retriever for email content."""
    
    def __init__(self, index_dir: str, model_name: Optional[str] = None, max_length: int = 512):
        """
        Initialize the ColBERT retriever.
        
        Args:
            index_dir: Directory containing the index
            model_name: Name of the pretrained model (if None, load from index)
            max_length: Maximum sequence length for the tokenizer
        """
        # Use the provided model or load from index
        if model_name is None:
            # Load model info from index
            with open(os.path.join(index_dir, 'model_info.json'), 'r') as f:
                model_info = json.load(f)
            self.model_name = model_info['model_name']
            self.max_length = model_info['max_length']
        else:
            self.model_name = model_name
            self.max_length = max_length
        
        # Load the tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
        
        # Load index
        self.faiss_index = faiss.read_index(os.path.join(index_dir, 'faiss_index.bin'))
        
        # Load document texts, IDs, and metadata
        with open(os.path.join(index_dir, 'document_texts.pkl'), 'rb') as f:
            self.document_texts = pickle.load(f)
            
        with open(os.path.join(index_dir, 'document_ids.pkl'), 'rb') as f:
            self.document_ids = pickle.load(f)
            
        with open(os.path.join(index_dir, 'document_metadata.pkl'), 'rb') as f:
            self.document_metadata = pickle.load(f)
    
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
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant documents for a query.
        
        Args:
            query: Query string
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        # Encode query
        query_embedding = self._encode_query(query)
        
        # Normalize query vector for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search the index
        scores, indices = self.faiss_index.search(query_embedding, top_k)
        
        # Collect results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.document_texts):
                result = {
                    'text': self.document_texts[idx],
                    'id': self.document_ids[idx],
                    'metadata': self.document_metadata[idx],
                    'score': float(scores[0][i])
                }
                results.append(result)
                
        return results


class RAGSystem:
    """Retrieval-Augmented Generation system for email queries."""
    
    def __init__(self, index_dir: str):
        """
        Initialize the RAG system.
        
        Args:
            index_dir: Directory containing the index
        """
        self.retriever = ColBERTRetriever(index_dir)
        # No longer using the transformer pipeline to avoid errors
        # self.generator = pipeline('text2text-generation', model=llm_model)
        
    def _format_retrieved_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context for the generator.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs):
            metadata = doc['metadata']
            
            # Format based on document type
            if metadata['type'] == 'body':
                context_str = f"EMAIL {i+1}:\n"
                context_str += f"De: {metadata['from']}\n"
                context_str += f"À: {metadata['to']}\n"
                context_str += f"Sujet: {metadata['subject']}\n"
                context_str += f"Date: {metadata['date']}\n"
                context_str += f"Contenu: {doc['text']}\n\n"
            else:  # subject
                context_str = f"SUJET EMAIL {i+1}:\n"
                context_str += f"De: {metadata['from']}\n"
                context_str += f"À: {metadata['to']}\n"
                context_str += f"Sujet: {metadata['subject']}\n"
                context_str += f"Date: {metadata['date']}\n\n"
                
            context_parts.append(context_str)
            
        return "".join(context_parts)
    
    def _generate_prompt(self, query: str, context: str) -> str:
        """
        Generate a prompt for the LLM.
        
        Args:
            query: User query
            context: Retrieved context
            
        Returns:
            Complete prompt for the LLM
        """
        return f"""En vous basant sur les informations d'emails suivantes, veuillez répondre à cette question:
Question: {query}

Informations d'emails récupérées:
{context}

Réponse:"""
    
    def answer_query(self, query: str, top_k: int = 3) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Answer a query using RAG.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Tuple of (generated answer, retrieved documents)
        """
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query, top_k=top_k)
        
        # If no documents retrieved, return default message
        if not retrieved_docs:
            return "Je n'ai pas trouvé d'informations pertinentes dans les archives d'emails pour répondre à votre question.", []
        
        # Format context
        context = self._format_retrieved_context(retrieved_docs)
        
        # Generate prompt
        prompt = self._generate_prompt(query, context)
        
        # Generate answer
        try:
            # Use a simple approach to generate a response based on the retrieved information
            # Format a basic response instead of using a complex language model to avoid errors
            
            # Extract key information from retrieved documents
            key_info = []
            for doc in retrieved_docs:
                metadata = doc['metadata']
                # Add sender information
                if metadata.get('from') and 'from' not in key_info:
                    key_info.append(f"De: {metadata['from']}")
                # Add subject if relevant
                if metadata.get('subject') and 'subject' not in key_info:
                    key_info.append(f"Sujet: {metadata['subject']}")
                # Add date if relevant
                if metadata.get('date') and 'date' not in key_info:
                    key_info.append(f"Date: {metadata['date']}")
            
            # Craft a simple response in French
            response = f"D'après les emails récupérés, j'ai trouvé des informations liées à votre question.\n\n"
            response += "Voici ce que j'ai trouvé:\n"
            for doc in retrieved_docs[:2]:  # Use just the top 2 documents
                if doc['metadata']['type'] == 'body':
                    # Get full text without truncation
                    excerpt = doc['text']
                    sender = doc['metadata']['from']
                    response += f"\n- Email de {sender} mentionne: \"{excerpt}\""
            
            return response, retrieved_docs
            
        except Exception as e:
            return f"J'ai rencontré une erreur lors de la génération d'une réponse: {str(e)}", retrieved_docs


def format_email_preview(doc: Dict[str, Any]) -> str:
    """
    Format an email document for preview display.
    
    Args:
        doc: Document dictionary with metadata
        
    Returns:
        Formatted preview string
    """
    metadata = doc['metadata']
    
    preview = f"**De:** {metadata['from']}\n"
    preview += f"**À:** {metadata['to']}\n"
    preview += f"**Sujet:** {metadata['subject']}\n"
    preview += f"**Date:** {metadata['date']}\n"
    
    # For body documents, include a snippet of content
    if metadata['type'] == 'body' and doc['text']:
        # Include full content
        body_text = doc['text']
        
        # Wrap to multiple lines for better readability
        wrapped_text = textwrap.fill(body_text, width=80)
        preview += f"**Contenu:**\n```\n{wrapped_text}\n```\n"
        
    return preview


def get_rag_answer(
    query: str,
    index_dir: str,
    top_k: int = 3
) -> Tuple[str, List[str]]:
    """
    Get RAG answer to a query about emails.
    
    Args:
        query: User query
        index_dir: Directory containing the index
        top_k: Number of documents to retrieve
        
    Returns:
        Tuple of (answer, list of source previews)
    """
    # Initialize RAG system
    rag = RAGSystem(index_dir)
    
    # Get answer and sources
    answer, sources = rag.answer_query(query, top_k=top_k)
    
    # Format sources for display
    source_previews = [format_email_preview(doc) for doc in sources]
    
    return answer, source_previews


if __name__ == "__main__":
    # Test code for retrieval
    import os
    
    # Set up index directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    index_dir = os.path.join(project_root, 'data', 'processed', 'index')
    
    # Test query
    test_query = "When is the next committee meeting?"
    
    # Initialize retriever
    retriever = ColBERTRetriever(index_dir)
    
    # Retrieve documents
    docs = retriever.retrieve(test_query, top_k=3)
    
    # Print results
    print(f"Query: {test_query}")
    print(f"Retrieved {len(docs)} documents")
    for i, doc in enumerate(docs):
        print(f"Result {i+1} (score: {doc['score']:.4f}):")
        print(f"  ID: {doc['id']}")
        print(f"  Type: {doc['metadata']['type']}")
        print(f"  Subject: {doc['metadata']['subject']}")
        if doc['metadata']['type'] == 'body':
            print(f"  Content (first 100 chars): {doc['text'][:100]}...")
        print()
