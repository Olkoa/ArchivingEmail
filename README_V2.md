# Okloa Email Archive Analytics — README v2

## Overview
Okloa is a Streamlit application that archives, normalizes, and explores historical mailboxes. The default UI (`app/app.py`) authenticates users, keeps the active project in sync with `constants.py`, and exposes analytics ranging from timeline plots to RAG-assisted question answering. This README documents how to operate the tool locally, with Docker, and from the command line when synchronizing mailboxes to object storage.

## Repository Layout
- `app/`: Streamlit code, including `app.py`, the `pages/` directory (e.g. `pages/manage_projects.py`), reusable `components/`, and static assets.
- `src/`: Backend helpers. Data ingestion lives in `src/data/`, feature engineering in `src/features/`, retrieval in `src/rag/`, and LLM adapters in `src/llm/`.
- `data/`: Project workspaces (`data/Projects/<Project>/<Mailbox>/...`) and sample corpora.
- `constants.py`: Global flags such as `ACTIVE_PROJECT`, UI defaults, and display options referenced at runtime.
- `Makefile`: Opinionated entry points (`make setup`, `make run`, etc.).
- `Dockerfile` & `docker-compose.yml`: Containerized deployment assets.

## Environment Preparation
1. **Python toolchain**: Install Python 3.11 and system packages for DuckDB/Graphviz if you plan to run locally.
2. **Dependencies**: From repo root, run `make setup`. This installs Python requirements using the pinned `requirements.txt` without polluting the cache.
3. **Environment variables**: Create a `.env` file or export variables before launching. The Streamlit entry point relies on:
   - `ACTIVE_PROJECT`, `DEVELOPER_MODE` — current mailbox workspace and optional auth bypass.
   - `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `SCW_ACCESS_KEY`, `SCW_SECRET_KEY` — S3-compatible object store access.
   - `JINA_API_KEY`, `JINA_MODEL_URL`, `JINA_MODEL_NAME`, `OPENAI_BASE_URL`, `OPENAI_API_KEY` — embedding / LLM backends.
   - Any additional secrets consumed by modules in `src/features` or `src/rag`.
4. **Data layout**: For each project under `data/Projects/<Project Name>/`, keep `raw/` PST, MBOX, ZIP, or EML source files and `processed/` derivatives. The UI and CLI helpers expect this convention.

## Running the Streamlit App Locally
1. Export the desired `ACTIVE_PROJECT` or let the value from `constants.py` load.
2. Start the UI with `make run` (hot reloading) or `make run-normal` (default Streamlit watcher). `make run-debug` adds verbose logging.
3. Browse to http://localhost:8501. Unless `DEVELOPER_MODE` is true, you will encounter the login form from `components/logins.py`. Credentials are stored in the lightweight JSON database seed created by `initialize_users_db()`.
4. Navigation is grouped by category (Dashboard, Chat + RAG, Topic, Graph, Visualization, Search). Page selection is stored in Streamlit session state so returning users stay on the last view.
5. Feature highlights from `app/app.py`:
   - Email ingestion via `src.data.loading.load_mailboxes()` and analytics from `src.data.email_analyzer.EmailAnalyzer`.
   - Embedding generation (`src.features.embeddings.generate_embeddings`) and enhanced semantic search (`src.features.elasticsearch_enhanced.enhanced_search_emails`).
   - Visual timelines and network graphs through `src.visualization.timeline.create_timeline` and `src.visualization.email_network.create_network_graph`.
   - RAG question answering initialized by `src.rag.initialization.initialize_rag_system()` and served with `src.rag.retrieval.get_rag_answer()`.

## Managing Projects in the UI (`pages/manage_projects.py`)
The **Manage Projects** page is the operational cockpit for mailbox onboarding.

1. **Project discovery and ordering**: `find_projects()` crawls `data/Projects/`, reads each `project_config_file.json`, and sorts items using `PROJECT_ORDER` from `constants.py`. Editing a project automatically moves it to the top of that list via `update_project_order()`.
2. **Session-driven form state**: Project composition (mailboxes, aliases, positions, organizations) is stored in `st.session_state.project_form`, enabling multi-step edits without immediate disk writes.
3. **File handling**:
   - Upload widgets persist files under `<project>/<mailbox>/raw/` (`save_uploaded_files`).
   - ZIP archives are extracted by `extract_project_zip_files`, PST/MBOX archives convert to EML through `convert_project_emails_to_eml` (`src.data.mbox_to_eml`).
4. **S3 synchronization**: When requested, `download_project_raw_data_from_s3()` pulls selected mailboxes, while uploads reuse the shared `S3Handler` from `src/data/s3_utils.py`.
5. **Pipeline orchestration**:
   - Verifies raw data presence (`mailboxes_missing_files`).
   - Generates DuckDB datasets via `src.data.eml_transformation.generate_duck_db()` and ensures expected tables (e.g. `receiver_emails`) exist.
   - Builds fresh ColBERT indices with `src.rag.colbert_initialization.initialize_colbert_rag_system()`.
6. **State synchronization**: Switching projects updates `constants.py`, `.env`, in-memory environment vars, and clears Streamlit caches to avoid stale results.

Once the pipeline succeeds, the dashboard pages immediately reflect the new corpus without restarting the app.

## Docker & Container Deployment
- **Image build**: The `Dockerfile` starts from `python:3.11-slim`, installs system deps (Graphviz, build toolchain, Git, GL libraries), then copies `requirements.txt`, `Makefile`, and `constants.py` to leverage Docker layer caching before installing Python packages.
- **Application copy**: The image embeds `.ragatouille`, `app/`, `data/`, and `src/`, plus `.env`. Entry point `app/entrypoint.sh` launches Streamlit and automatically restarts on crashes with a configurable `APP_RESTART_DELAY`.
- **Runtime configuration**: `docker-compose.yml` exposes port 8501 and forwards environment variables for S3/Jina/OpenAI credentials. Volumes mount `.ragatouille` (for ColBERT indices) and `data/` so generated artifacts persist across restarts.

**Getting started with Docker Compose**
1. Provide the required environment variables (either via `.env` file at repo root or inline `export`).
2. Build and run: `docker compose up --build`. The service health check polls `/_stcore/health` until Streamlit is ready.
3. To rebuild embeddings or DuckDB artifacts inside the container, shell into it (`docker compose exec okloa bash`) and reuse the same Makefile / Python commands.

## Command-line Mailbox Upload to S3
`src/data/s3_utils.py` centralizes object-storage interactions and now includes the `upload_raw_data_to_s3` helper (see `src/data/s3_utils.py:729`). This function encapsulates the steps needed to push a mailbox's `raw/` folder to the `olkoa-projects` bucket.

### S3 prerequisites
- Export `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `SCW_ACCESS_KEY`, and `SCW_SECRET_KEY` so `boto3` can reach your S3-compatible endpoint.
- Ensure your account has permission to list buckets and create the `olkoa-projects` bucket if it does not exist.

### Upload workflow (Linux shell)
1. Activate the same virtual environment you created with `make setup` so the repository code is on `PYTHONPATH`.
2. Change into the repository root where the `data/` directory lives.
3. Trigger the upload helper from a Python shell or one-off script:

```bash
python - <<'PY'
from src.data.s3_utils import upload_raw_data_to_s3

# The helper currently targets the demo mailbox path and pushes it under <mailbox_name>/raw/.
# Adjust 'mailbox_name' to control the S3 prefix.
upload_raw_data_to_s3(
    local_raw_data_dir="data/Projects/Projet Demo/Boîte mail de Céline/raw/",
    mailbox_name="BoiteMailDeCeline"
)
PY
```

The helper performs the following:
- Instantiates `S3Handler` with credentials loaded from environment variables.
- Lists existing buckets and creates `olkoa-projects` if needed.
- Uploads the demo raw folder to `s3://olkoa-projects/<mailbox_name>/raw/` using the recursive `upload_directory` method.

> **Note:** The current implementation overwrites the `local_raw_data_dir` argument with the demo path inside the function body to mirror the UI defaults. If you want to reuse the helper for other mailboxes, update the constant path before running the script or wrap the call in your own function that sets the directory you need.

### Verifying the upload
- From the CLI: `python - <<'PY'` followed by `from src.data.s3_utils import S3Handler; print(S3Handler().list_objects("olkoa-projects", prefix="BoiteMailDeCeline/raw/"))`
- From the UI: open **Manage Projects**, select the mailbox, and choose the S3 sync action to ensure the files round-trip correctly.

## Recommended Next Steps
- Run `pytest` or `pytest tests` after modifying ingestion logic to validate downstream assumptions.
- When operating in Docker, rebuild the image after changing Python dependencies so the container includes the new packages.
- Keep `constants.py` in sync with project additions to ensure the UI highlights the correct default mailbox.
