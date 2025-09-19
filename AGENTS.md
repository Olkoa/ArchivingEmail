# Repository Guidelines

## Project Structure & Module Organization
`app/` hosts the Streamlit interface, with `components/`, `pages/`, and `static/` for reusable UI pieces and assets. Core logic sits in `src/`: `data/` (ingestion), `features/` (analytics), `rag/` (retrieval), and `llm/` (model adapters). Use `constants.py` and `templates/` for shared config and layouts. Store datasets under `data/`, marketing assets in `assets/`, and keep exploratory notebooks and scripts inside `notebooks/` and `examples/` only.

## Build, Test, and Development Commands
Use the Makefile to stay consistent: `make setup` installs dependencies, `make data` refreshes sample mailboxes, and `make run` or `make run-debug` launches the Streamlit app. `make run-normal` restores the default watcher, and `make clean` purges derived data. For CLI flows, `python generate_samples.py` seeds test mailboxes and the RAG snippet in `app/README.md` rebuilds embeddings.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, snake_case functions, and PascalCase classes. Format with `black src app main.py`, sort imports via `isort`, and lint using `flake8 src app`. Streamlit pages should mirror their route name (e.g., `pages/01_Home.py`), while shared constants belong in `constants.py` or module-level `settings.py` files.

## Testing Guidelines
Run `pytest` from the repo root, or scope to UI scaffolds with `pytest app/test_table_model.py` and backend logic with `pytest tests`. For coverage checks, use `pytest --cov=src --cov=app`. Name tests `test_<feature>.py`, co-locate them with the code, and favor fixtures drawn from `data/sample_*` or generated via `generate_samples.py`.

## Commit & Pull Request Guidelines
Keep commits small with short, present-tense subjects (e.g., `Refactor S3 upload function`); reference issues via `#123` and call out dependency or schema changes in the body. Pull requests need a crisp summary, testing notes (`pytest`, Streamlit checks), and screenshots or GIFs for UI work. Highlight data migrations, MCP path updates, or infrastructure impacts explicitly.

## Data & Configuration Tips
Only sanitized mailboxes belong in git; exclude real archives. Load secrets from environment variables or `.env` files consumed by `src/features` and `rag`. When adjusting MCP integrations, confirm `make start_mcp` paths remain valid for macOS and WSL setups, and document extra tooling in the PR.
