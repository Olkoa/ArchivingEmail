# Okloa: Email Archive Analytics Platform

run MCP server with npm: npx -y @modelcontextprotocol/server-filesystem /mnt/c/Users/julie/Projects
file at C:\Users\julie\AppData\Roaming\Claude\claude_desktop_config.json

## Overview

Okloa is an R&D project focused on making archived email data valuable and accessible through advanced analytics, visualization, and conversational interfaces. The project aims to valorize archived emails from the Departmental Archives of Vaucluse by making them searchable, analyzable, and queryable.

## Objectives

- **Valorization of archives**: Transform static email archives into valuable, accessible resources
- **Operational email archive exploitation**: Make archived emails easily searchable and explorable
- **Advanced analytics**: Extract insights and patterns from email correspondence
- **Knowledge discovery**: Identify relationships, entities, and events within the corpus

## Project Phases

### Sprint 1: Visualization and Corpus Exploration ✅
- Email embedding and Elasticsearch integration
- Macro visualization and search functionality
- Large corpus visualization based on NomicAI approach
- Development with Streamlit framework

### Sprint 2: Retrieval-Augmented Generation (RAG) ✅
- Conversational interface to query the email corpus
- Natural language-based exploration of archives

### Sprint 3: Named Entity Recognition 🔄
- Identification of people, companies, and locations
- Temporal information extraction
- Event recognition and linking

## Getting Started

### Prerequisites

- Python 3.9+ (recommended: Python 3.10 or 3.12)
- Elasticsearch 8.x (optional for advanced search features)
- Other dependencies listed in `requirements.txt`

### Installation

```bash
# Clone the repository (if using Git)
# git clone https://github.com/your-organization/okloa.git
# cd okloa

# Create a virtual environment
python -m venv venv
# On Windows: 
venv\Scripts\activate
# On Linux/Mac: 
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Generating Sample Data

Before running the application, you need to generate sample email data:

```bash
# Generate sample mailboxes with test data
python generate_samples.py
```

This will create three sample mailboxes with 5 sent and 5 received emails each in the `data/raw` directory.

### Running the Application

```bash
# Start the Streamlit web application
cd app
streamlit run app.py
```

The application will open in your default web browser at http://localhost:8501.

## Features

### Email Exploration and Visualization

Okloa provides multiple visualizations to explore your email archive:

- **Dashboard**: Overview of key metrics and email activity
- **Email Explorer**: Browse and search through individual emails
- **Network Analysis**: Visualize the communication network between contacts
- **Timeline**: View email activity over time

### Conversation with Email Archives (RAG)

The Chat interface allows you to ask natural language questions about your email archive. The system uses ColBERT-based Retrieval-Augmented Generation (RAG) to:

1. Retrieve relevant emails based on your query
2. Generate informative answers
3. Provide sources for verification

#### Example Questions

- "When is the next committee meeting?"
- "What's the status of the digitization project?"
- "Who is responsible for the restoration of parish registers?"
- "What was discussed in the last email from Marie Durand?"

#### Command-line RAG Index Creation

You can also build the RAG index from the command line:

```bash
python -c "from src.rag.initialization import initialize_rag_system; from src.data.loading import load_mailboxes; import os; emails_df = load_mailboxes(['mailbox_1', 'mailbox_2', 'mailbox_3'], os.path.join(os.getcwd(), 'data', 'raw')); initialize_rag_system(emails_df, force_rebuild=True)"
```

## Data Structure

The project uses email data from three former agents of the Departmental Archives of Vaucluse. For development and testing, sample mailboxes are provided in the `data/raw/` directory.

Each mailbox contains:
- Email bodies and metadata
- Sent and received messages
- Date, sender, recipient, and subject information

### Data Organization

```
data/
├── raw/                  # Raw email data
│   ├── mailbox_1/        # Marie Durand (Conservateur en chef)
│   │   ├── emails.mbox   # Mailbox file
│   │   └── metadata.json # Metadata about the emails
│   ├── mailbox_2/        # Thomas Berger (Responsable numérisation)
│   │   ├── emails.mbox
│   │   └── metadata.json
│   └── mailbox_3/        # Sophie Martin (Archiviste documentaliste)
│       ├── emails.mbox
│       └── metadata.json
└── processed/            # Processed data (indices, embeddings)
    └── index/            # RAG system indices
```

## Using the RAG System

The Retrieval-Augmented Generation system allows you to have conversations with your email archive using natural language. Here's how to use it:

### Through the Web Interface

1. Start the application: `streamlit run app.py`
2. Navigate to the "Chat" tab
3. Type your question in the input box
4. View the answer and the source emails used to generate it

### Through Python Code

```python
# Import necessary modules
from src.data.loading import load_mailboxes
from src.rag.initialization import initialize_rag_system
from src.rag.retrieval import get_rag_answer
import os

# Load emails
project_root = os.path.abspath(os.getcwd())
base_dir = os.path.join(project_root, 'data', 'raw')
emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)

# Initialize RAG system
index_dir = initialize_rag_system(emails_df, project_root)

# Get answers to questions
query = "When is the next committee meeting?"
answer, sources = get_rag_answer(query, index_dir)
print(f"Query: {query}")
print(f"Answer: {answer}")
print(f"Based on {len(sources)} sources")
```

## License

[Specify your license here]

## Contributors

[Your name/organization]
