# Colbert RAG Implementation for Olkoa

This directory contains the implementation of a RAG (Retrieval-Augmented Generation) system using ColBERT for the Olkoa email analytics platform.

## Overview

The Colbert RAG system enhances email search and question answering capabilities by using semantic search rather than traditional keyword matching. It leverages the [ColBERTv2.0](https://github.com/stanford-futuredata/ColBERT) model from Stanford NLP via the [RAGAtouille](https://github.com/bclavie/RAGatouille) library.

## Key Components

1. **ColBERT Indexing**: Processes and indexes emails using the ColBERT model
2. **Semantic Search**: Retrieves relevant emails based on the meaning of queries
3. **Question Answering**: Generates answers to user questions based on retrieved emails

## Features

- **Semantic Understanding**: Captures the meaning behind queries instead of just matching keywords
- **Contextual Retrieval**: Ranks results based on semantic relevance to the query
- **Email Chunking**: Automatically splits long emails into digestible chunks for more precise retrieval
- **Question-Answering Interface**: Allows users to ask natural language questions about their email archives

## Implementation Details

The implementation consists of three main files:

1. `colbert_rag.py`: Core functionality for working with the RAGAtouille library and ColBERT model
2. `colbert_initialization.py`: Handles system initialization and index building
3. `app/pages/colbert_rag.py`: Streamlit interface for interacting with the Colbert RAG system

## Requirements

- RAGAtouille library (`pip install ragatouille`)
- PyTorch (`pip install torch`)
- Streamlit (`pip install streamlit`)
- Other dependencies specified in the project's requirements.txt

## Usage

The Colbert RAG system can be accessed through the "Colbert RAG" option in the main navigation of the Olkoa application. The interface provides tabs for:

1. **Semantic Search**: Search for emails using natural language queries
2. **Question-Answering**: Ask questions about your email archives
3. **Configuration**: Manage the Colbert RAG index and settings

## Implementation Based on RAG_process.ipynb

This implementation is based on the workflow outlined in the RAG_process.ipynb notebook, adapting the approach for the specific needs of email data processing. Key adaptations include:

1. Processing of .mbox files instead of PDFs or markdown files
2. Email-specific document structure (from, to, subject, body)
3. Integration with the existing Olkoa email analytics platform
4. User interface adapted for email search and question answering

## Credit

- [ColBERT](https://github.com/stanford-futuredata/ColBERT) - Stanford NLP
- [RAGAtouille](https://github.com/bclavie/RAGatouille) - Benjamin Clavié and contributors
