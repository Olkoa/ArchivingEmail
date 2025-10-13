# Retrieval-Augmented Generation (RAG) for Olkoa

This module implements a Retrieval-Augmented Generation (RAG) system for the Olkoa project, enabling a conversational interface to query the email corpus.

## Architecture

The RAG system consists of several components:

1. **Indexing**: Uses ColBERT to create dense vector embeddings for email content, which are then indexed using FAISS for efficient similarity search.

2. **Retrieval**: Given a user query, the system retrieves the most relevant emails based on vector similarity.

3. **Generation**: The system uses a language model to generate coherent answers based on the retrieved email content.

## Key Files

- `indexing.py`: Contains the ColBERTIndexer class for creating and managing indexes.
- `retrieval.py`: Contains the ColBERTRetriever and RAGSystem classes for retrieving relevant documents and generating answers.
- `initialization.py`: Contains utilities to initialize the RAG system.

## How It Works

1. **Index Building**:
   - Each email is processed into embeddings using a transformer model (by default, Sentence-BERT).
   - Both the email body and subject are indexed separately for better retrieval.
   - The embeddings are stored in a FAISS index for efficient similarity search.

2. **Retrieval Process**:
   - User queries are encoded using the same model.
   - The system retrieves the most similar documents based on cosine similarity.
   - Metadata about the emails (sender, recipient, date) is preserved to provide context.

3. **Answer Generation**:
   - Retrieved emails are formatted into a context prompt.
   - A language model generates a coherent answer based on the retrieved information.
   - The system returns both the answer and the source emails used to generate it.

## Usage

```python
# Initialize the RAG system
from src.rag.initialization import initialize_rag_system
index_dir = initialize_rag_system(emails_df)

# Get answers from the RAG system
from src.rag.retrieval import get_rag_answer
answer, sources = get_rag_answer("When is the next committee meeting?", index_dir)
```

## Models

The system uses the following models by default:

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Generation Model**: `facebook/bart-large`

These can be customized via environment variables:
- `COLBERT_MODEL`: For the embedding model
- `LLM_MODEL`: For the generation model

## Performance Considerations

- The first query may take longer due to model loading.
- Index building is a one-time operation but can be memory-intensive.
- For large email corpora, consider using a GPU for better performance.
