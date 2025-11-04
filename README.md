# Olkoa Email Archive Analytics

Olkoa is a Streamlit-based analytics workbench designed to ingest, normalize, and explore large historical mailboxes. Archivists and researchers can onboard raw PST/EML exports, consolidate them into DuckDB, explore communication patterns, run semantic search across message chunks, navigate BERTopic hierarchies, and issue retrieval-augmented queries against ColBERT indexes — all from the same UI.

This document captures the current state of the project and explains how the repository fits together, which pipelines power each page, and how to run or extend the system locally.

---

## Key Features

- **Guided ingestion pipeline** – Manage Projects orchestrates raw data uploads, PST/MBOX conversion, DuckDB generation, semantic-search chunking, topic modeling, and ColBERT indexing.
- **Interactive dashboard** – Timeline, contact charts, attachment stats, and network graphs update live against DuckDB views queried via `EmailAnalyzer`.
- **Advanced filtering** – A shared dropdown component allows mailbox, folder, direction, topic cluster, date, contact, and attachment filters to be applied consistently across pages.
- **Semantic and lexical search** – Chunk-level embedding search (Sentence Transformers) and keyword search (Elasticsearch-style) both surface results through the same AgGrid viewer with modal previews.
- **Hierarchical topic exploration** – BERTopic + k-medoids clustering feeds a multi-height cluster tree with summaries stored in DuckDB and displayed in the Topics page.
- **RAG workspace** – ColBERT indices unlock retrieval-augmented Q&A on the “Chat + RAG” page.
- **Object-storage integration** – S3 helpers let you sync raw mailboxes to cloud storage directly from the UI or CLI.
- **Docker-ready** – A production Dockerfile, compose file, and Make targets support local development and containerized deployments.

---

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| UI | [Streamlit](https://streamlit.io/), `st-aggrid`, Plotly, NetworkX, Pandas |
| Data storage | DuckDB (primary analytics store), JSON artifacts under `data/Projects/` |
| NLP & search | Sentence Transformers, BERTopic, UMAP, TSNE, pyclustering, scikit-learn, Elasticsearch (optional) |
| RAG | ColBERT via `ragatouille`, FAISS, Hugging Face embeddings |
| Backend helpers | Python 3.12+, Pandas, BeautifulSoup, boto3, tqdm |
| Deployment | Makefile, Docker, docker-compose, Model Context Protocol (optional dev tooling) |

Many modules assume access to Hugging Face, OpenAI, or Jina endpoints; see the environment variable section for required credentials.

---

## Repository Layout

```
├── app/                       # Streamlit application
│   ├── app.py                 # Main entry point with page routing
│   ├── components/            # Reusable UI + pipeline helpers
│   │   ├── email_viewer.py    # AgGrid table + modal viewer (uses Streamlit dialogs)
│   │   ├── working_dropdown_filters.py  # Unified filter menu
│   │   └── topic_modeling/    # BERTopic pipeline (extract → cluster → summarize → persist)
│   ├── pages/manage_projects.py  # Onboarding cockpit for projects/mailboxes
│   └── static/                # CSS, JSON, and cached assets
│
├── src/
│   ├── data/                  # Ingestion & persistence utilities
│   │   ├── eml_transformation.py   # Parse EML, build DuckDB tables, populate entities/attachments
│   │   ├── duckdb_utils.py         # Schema creation helpers
│   │   ├── email_analyzer.py       # High-level DuckDB queries used across the UI
│   │   ├── s3_utils.py             # Object storage upload/download helpers
│   │   └── mbox_to_eml.py, pst_converter.py, upload_*  # Format conversion utilities
│   ├── features/              # Feature engineering & pipeline logic
│   │   ├── pipeline_data_cleaning.py  # Semantic-search chunking + embedding pipeline
│   │   ├── search.py, elasticsearch_enhanced.py        # Keyword search helpers
│   │   └── embeddings.py (placeholder)                 # Legacy random embedding stub
│   ├── topic/                 # Lightweight topic-visualization helpers (used in app/app.py)
│   ├── rag/                   # ColBERT index build + retrieval APIs
│   ├── filters/               # Email filter metadata + convenience functions
│   ├── visualization/         # Timeline and network graph plotters
│   └── models/                # Pydantic definitions for DuckDB ingestion
│
├── data/
│   └── Projects/<Project>/    # Raw inputs, semantic artifacts, DuckDB files, topic outputs
├── constants.py               # Global flags (ACTIVE_PROJECT, sidebar state, UI defaults)
├── Makefile                   # `make setup`, `make run`, `make data`, etc.
├── Dockerfile / docker-compose.yml
└── requirements*.txt          # Pinned Python dependencies
```

See `README_V2.md` for additional deployment notes; it complements (rather than replaces) this document.

---

## Data Lifecycle

1. **Raw inputs**  
   Mailboxes arrive as ZIP, PST, MBOX, or loose EML files under `data/Projects/<Project>/<Mailbox>/raw/`.

2. **Conversion & normalization**  
   `mbox_to_eml.py`, `pst_converter.py`, and `upload_emls.py` generate consistent EML trees under `processed/`. `eml_transformation.generate_duck_db()` parses those messages, extracts metadata (entities, folders, attachments), and writes a DuckDB database (`<project>.duckdb`) with tables such as `receiver_emails`, `entities`, `email_topic_clusters`, and `topic_clusters`.

3. **Semantic search artifacts**  
   `src/features/pipeline_data_cleaning.prepare_semantic_search()` creates `semantic_search/topic/` artifacts:
   - `topics_chunks.npy`, `topics_embeddings.npy` – sentence-transformer embeddings (MiniLM).
   - 2D projections (`emb_2d.npy`) and cluster labels (`labels.npy`) for visualizations.
   - `chunk_metadata.pkl` – chunk → message metadata used to reconnect semantic hits to full emails.

4. **Topic modeling**  
   `app/components/topic_modeling/Topic_modeling.topic_build()` orchestrates:
   - Extraction of cleaned mail bodies (`eml_json`).
   - BERTopic modeling (`bertopicgpu.py`) with multilingual embeddings.
   - Dimensionality reduction (`transform_bert.py`), split sampling, GPT summaries (`gpt4_1.py`), k-medoids clustering, hierarchical clustering, and summary tree construction (`cluster_tree.py`).  
   Persisted CSV/JSON summaries are loaded back into DuckDB via `_persist_topics_to_db` for use in the UI.

5. **Retrieval-Augmented Generation**  
   `src/rag/indexing.py` builds ColBERT indices (FAISS + metadata) under `.ragatouille` and `data/processed/index`. `src/rag/retrieval.py` exposes answer generation for the Chat + RAG page.

6. **Object storage sync (optional)**  
   `src/data/s3_utils.S3Handler` can mirror raw inputs to `s3://olkoa-projects/<mailbox>/raw/` or download them back into the local project directory.

Each stage is available through Manage Projects as timed steps, but you can invoke any component directly from the CLI if needed.

---

## Streamlit Application Tour (`app/app.py`)

| Page | Purpose & Backing Modules |
|------|---------------------------|
| **Dashboard** | High-level metrics, attachments summary, contact charts, timeline, and communication network. Data comes from `EmailAnalyzer.get_app_dataframe_with_filters()` and `src.visualization` helpers. |
| **Chat + RAG** | Live retrieval-augmented Q&A using ColBERT (see `src/rag.initialization` + `src.rag.retrieval`). |
| **Topic** | Hierarchical topic exploration. Users choose a level/height (`EmailAnalyzer.get_topic_levels()`), inspect cluster summaries, and view Plotly graphs generated from topic artifacts. |
| **Graph** | Displays pre-generated D3/Plotly graphs from `data/Projects/<Project>/Graphs/`. |
| **Structure de la boîte mail** | Navigates mailbox folder trees built during DuckDB ingestion. |
| **Recherche Sémantique** | Embedding-based search over chunked mail content, deduplicated back to message-level hits using metadata produced by the semantic pipeline. Highlights matching snippets while letting users open full emails via `create_email_table_with_viewer`. |
| **Recherche ElasticSearch** | Traditional keyword & fuzziness search (`src.features.search` / `elasticsearch_enhanced`). |
| **Dashboard → Filters** | Shared dropdown menu from `working_dropdown_filters` supports mailbox switching, date ranges, direction, contacts, attachment presence, and topic cluster filters. |

Authentication is handled by `components/logins.py` (hashed credentials stored in a simple JSON DB). `constants.py` defines defaults such as `ACTIVE_PROJECT`, sidebar state, and email display mode (modal vs popover).

---

## Manage Projects Workflow (`app/pages/manage_projects.py`)

1. **Project discovery** – `find_projects()` scans `data/Projects/`, merges metadata from `project_config_file.json`, and orders entries using `PROJECT_ORDER` in `constants.py`. Selecting a project updates `constants.ACTIVE_PROJECT`, the `.env` file, and Streamlit session state.
2. **Mailbox administration** – Users can add/remove mailboxes, define aliases, positions, organizations, and upload raw archives. Files are persisted under `<project>/<mailbox>/raw/` via `save_uploaded_files`.
3. **Processing steps** – The “Pipeline” card runs a timed checklist:
   - Raw data validation (`mailboxes_missing_files`).
   - Conversion to EML (`convert_project_emails_to_eml`).
   - DuckDB generation (`generate_duck_db`).
   - Semantic search build (`prepare_semantic_search`).
   - ColBERT index initialization (`initialize_colbert_rag_system`).
   - Topic modeling (`topic_build`).
   Each step logs progress, surfaces errors to the UI, and aborts the sequence on failure.
4. **S3 synchronization** – Download or upload raw data for each mailbox via `S3Handler`. Credentials are read from environment variables (see below).
5. **Cache management** – The page clears Streamlit caches (`st.cache_data`) where necessary to avoid returning stale DuckDB or semantic artifacts after reprocessing.

Because Manage Projects mutates `constants.py`, remember to commit those changes (or stash them) when switching projects in version control.

---

## Setup & Configuration

### Prerequisites

- Python 3.12 (pyenv recommended).
- System packages for PST conversion (`pst-utils`), Graphviz (for topic plots), and GCC/Make if you plan to compile dependencies.
- Optional: Docker & Docker Compose for containerized runs.

### Installation

```bash
git clone https://github.com/<org>/olkoa.git
cd olkoa
make setup          # pip install -r requirements.txt
make data           # optional: seed sample mailboxes
```

### Environment Variables

Create a `.env` file at the repo root or export variables before launching Streamlit. Common keys include:

| Variable | Purpose |
|----------|---------|
| `ACTIVE_PROJECT` | Default project loaded by the UI (also stored in `constants.py`). |
| `DEVELOPER_MODE` | If `true`, bypasses the login screen. |
| `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `SCW_ACCESS_KEY`, `SCW_SECRET_KEY` | S3-compatible object storage credentials used by `src/data/s3_utils.py`. |
| `JINA_API_KEY`, `JINA_MODEL_URL`, `JINA_MODEL_NAME` | Embedding backends for semantic search. |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` | LLM summarization / RAG providers. |
| `HUGGINGFACEHUB_API_TOKEN` | Required if downloading transformers models behind authentication. |
| `COLBERT_DATA_DIR`, `SENTENCE_TRANSFORMERS_HOME` | Optional overrides for ColBERT and Hugging Face caches. |

`load_dotenv()` is called in multiple modules (Streamlit, pipelines), so `.env` values take precedence over `constants.py`.

---

## Running the Application

### Streamlit

```bash
make run          # streamlit run app/app.py with file watcher disabled
make run-debug    # same with Streamlit's debug mode
make run-normal   # default watcher enabled
```

Access the UI at [http://localhost:8501](http://localhost:8501). Use the credentials seeded by `components/logins.initialize_users_db()`, or add users from within the code.

### Docker

```bash
docker compose up --build
```

The compose file mounts `data/` and `.ragatouille/` so artifacts persist between runs. Environment variables can be supplied via `.env` or the compose file. See `README_V2.md` for more container tips.

### Model Context Protocol (optional)

For developers using Claude Desktop or other MCP clients, `make start_mcp` launches a filesystem MCP server rooted at the repository (`MCP_COMMAND` in the Makefile).

---

## Operating Pipelines Manually

While the UI provides one-click controls, you can run components directly:

```bash
# Regenerate DuckDB from processed EML
python -m src.data.eml_transformation --project <name> --mailboxes "<mailbox>=Boîte de réception"

# Rebuild semantic search artifacts
python - <<'PY'
from src.features.pipeline_data_cleaning import prepare_semantic_search
prepare_semantic_search(project="<Project>", force=True)
PY

# Run the BERTopic pipeline
python - <<'PY'
from app.components.topic_modeling.Topic_modeling import topic_build
topic_build()
PY

# Initialize ColBERT RAG index
python - <<'PY'
from src.rag.colbert_initialization import initialize_colbert_rag_system
initialize_colbert_rag_system(project_root=".", project_name="<Project>", force_rebuild=True)
PY
```

> **Tip:** Most scripts expect `ACTIVE_PROJECT` to be set. Export it before invoking CLI snippets or update `constants.py`.

---

## Object Storage Integration

- Upload raw data: `src/data/s3_utils.upload_raw_data_to_s3(local_raw_data_dir, mailbox_name, bucket='olkoa-projects')`.
- Download raw data: `download_project_raw_data_from_s3()` via Manage Projects.
- The helpers automatically create the bucket if missing and upload directories recursively.

Ensure your credentials allow `ListBuckets`, `CreateBucket`, and `PutObject` actions. When running in Docker, forward the same credentials through environment variables.

---

## Testing & Quality

- The project currently has minimal automated tests. Add PyTest suites under `tests/` and run with `pytest` from the repo root.
- Linting/formatting conventions: PEP 8, `black`, `isort`, and `flake8` as referenced in the Repository Guidelines.
- Streamlit caches (`st.cache_data`) may need manual clearing when underlying DuckDB data changes; Manage Projects already triggers `st.cache_data.clear()` in critical paths.

---

## Development Notes

- **Constants & session state** – `constants.py` drives default project selection and UI configuration. Manage Projects writes back to this file; track changes in Git.
- **Authentication** – Credentials live in `app/components/logins.py` via a JSON “database.” Update `initialize_users_db()` to seed new accounts.
- **Semantic search** – The AgGrid viewer relies on `chunk_metadata.pkl` produced by the semantic pipeline. If you see empty modals, rerun `prepare_semantic_search` to refresh metadata.
- **Topic summaries** – Summaries fall back to short sentences derived from underlying topics when GPT outputs are missing (`cluster_tree.get_summary_or_merge`).
- **External services** – Because BERTopic and Sentence Transformers download models from Hugging Face, environments behind SSL-inspecting proxies may require custom CA bundles (`REQUESTS_CA_BUNDLE` or `certifi`).

---

## Useful Commands

```bash
make help             # list Makefile commands
make clean            # remove generated sample data
python generate_samples.py   # create sample mailbox hierarchy under data/sample_*
pytest                # run (currently sparse) automated tests
docker compose exec olkoa bash  # enter running container
```

---

## Contributing

1. Run the relevant pipelines (`prepare_semantic_search`, `topic_build`, etc.) after modifying ingestion logic to keep artifacts in sync.
2. Update `README.md` and `README_V2.md` when changing architecture or external dependencies.
3. Provide screenshots or Looms for UI changes when preparing pull requests, and document any schema updates or new environment variables.

For questions about archival workflows or new feature requests, coordinate with the Archives départementales du Vaucluse stakeholders listed in the project charter.

---

Happy archiving! Curious about something that isn’t covered here? Browse the inline documentation throughout `src/` and `app/components/`, or open an issue to discuss the next iteration of the platform.
