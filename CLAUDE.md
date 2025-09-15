# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Okloa is an R&D platform for making archived email data valuable and accessible through advanced analytics, visualization, and conversational interfaces. The project transforms static email archives into searchable, analyzable resources using AI/ML techniques.

**Current Development Status**: Sprint 2 - Retrieval-Augmented Generation (RAG) implementation with ColBERT

## Quick Start Commands

### Development Setup
```bash
# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: Install embedding-specific dependencies
pip install -r requirements_embeddings.txt
```

### Running the Application
```bash
# Start the main Streamlit application
cd app
streamlit run app.py
# Application opens at http://localhost:8501
```

### Data Processing
```bash
# Process EML files into DuckDB (main data pipeline)
python main.py [path_to_eml] [path_for_db]

# Setup new project from scratch
python src/setup/setup.py

# Convert PST to EML format (Linux/Ubuntu only)
readpst -j 0 -e -o output_path path_to_pst_file
```

### Testing
```bash
# Run tests
pytest

# Run specific test files
python app/test_modal.py
python src/llm/test_chat_rag.py
```

## Architecture Overview

### Core Technology Stack
- **Backend**: Python with DuckDB for data storage
- **Frontend**: Streamlit for web interface
- **AI/ML**: ColBERT (via RAGAtouille), Sentence Transformers, FAISS
- **Search**: Elasticsearch integration (optional), semantic search with embeddings
- **Data Processing**: Pandas, email parsing libraries

### Key Directory Structure
```
src/
├── data/           # Data processing and database utilities
├── rag/            # Retrieval-Augmented Generation system
├── features/       # Core feature implementations (search, embeddings)
├── llm/            # Language model and agent implementations
├── visualization/ # Chart and graph generation
└── filters/       # Email filtering systems

app/
├── app.py         # Main Streamlit application
├── components/    # Reusable UI components
└── pages/         # Individual page implementations

data/
├── Projects/      # Project-specific data storage
└── processed/     # Processed indexes and embeddings
```

### Database Schema
The application uses DuckDB with these main tables:
- `receiver_emails`: Core email data with metadata
- `entities`: Contact information and relationships
- `attachments`: File attachment tracking
- `relationships`: Email thread relationships

### RAG System Architecture
1. **Indexing**: ColBERT creates dense vector embeddings for email content
2. **Retrieval**: FAISS enables efficient similarity search
3. **Generation**: Language models generate answers from retrieved context
4. **Storage**: Indexes stored per project in `.ragatouille/colbert/indexes/`

## Configuration

### Project Management
- Active project set in `constants.py` via `ACTIVE_PROJECT` variable
- Project data stored in `data/Projects/{PROJECT_NAME}/`
- Each project has a `project_config_file.json` with mailbox configuration

### Feature Toggles
In `constants.py`:
- `ENABLE_ELASTICSEARCH`: Toggle real vs mock Elasticsearch
- `ENABLE_RAG`: Enable/disable RAG features
- `EMAIL_DISPLAY_TYPE`: "MODAL" or "POPOVER" for email viewing
- `UI_LANGUAGE`: "FRENCH" or "ENGLISH"

### Authentication
- Simple user authentication system in `app/components/logins.py`
- User database stored in session state
- Demo credentials available for testing

## Development Guidelines

### Data Processing Pipeline
1. **Email Import**: PST → EML → DuckDB via `src/data/eml_transformation.py`
2. **Analysis**: Use `EmailAnalyzer` class for database queries
3. **Embedding**: Generate embeddings with `src/features/embeddings.py`
4. **Indexing**: Build ColBERT indexes with `src/rag/colbert_initialization.py`

### Adding New Features
- Follow the existing component structure in `app/components/`
- Use the enhanced filter system in `components/working_dropdown_filters.py`
- Implement new visualizations in `src/visualization/`
- Add RAG capabilities through `src/rag/` modules

### Email Processing Specifics
- Email addresses normalized automatically (removing dots, handling + symbols)
- Support for both sent and received email analysis
- Attachment format analysis and visualization
- Contact categorization (humans vs mailing lists)

### Multi-Project Support
- Each project maintains separate DuckDB database
- ColBERT indexes named with project prefix: `{ACTIVE_PROJECT}_emails_index`
- Project switching through UI in manage_projects page

## Known Issues & Limitations

### Current Development Challenges
- Email address parsing edge cases with malformed headers
- Foreign key constraint violations during database optimization
- Streamlit session state management for complex filtering
- 200MB practical limit for email processing

### Platform Dependencies
- PST to EML conversion requires Linux `pst-utils` package
- ColBERT requires significant memory for large email corpora
- GPU acceleration recommended for embedding generation

## Data Security & Privacy

### GDPR Compliance Features
- No external API calls to prevent data leakage
- Local processing only within controlled environment
- Pseudonymization mechanisms available
- Authentication system for access control

### Archive Processing
- Designed for Departmental Archives of Vaucluse email corpus
- Support for French language email processing
- Date formatting considerations for archival standards

## Performance Considerations

- First RAG query may be slow due to model loading
- Index building is memory-intensive but one-time operation
- Large email corpora benefit from GPU acceleration
- DuckDB provides efficient analytics on email metadata

## Troubleshooting

### Common Issues
- **"No emails found"**: Check project configuration and database path
- **RAG system errors**: Verify ColBERT index exists and is accessible
- **Memory issues**: Consider using smaller embedding models or chunking data
- **Authentication problems**: Clear session state or reset user database

### Debug Mode
- Enable detailed logging in email processing modules
- Use `EmailAnalyzer.get_email_summary()` for database diagnostics
- Check `.ragatouille/` directory for index status