# ColBERT RAG System Updates

## Summary of Changes

The ColBERT RAG system has been updated to work with the new architecture where:
1. The index creation is handled separately by `colbert_initialization.py`
2. The app focuses only on using the pre-built index for search and Q&A
3. Index building is only allowed through the rebuild button in the Configuration tab

## Key Changes Made

### 1. Updated `colbert_rag_component.py`

- **Import Updates**: Fixed import indentation - moved `from constants import ACTIVE_PROJECT` inside the try block
- **Removed automatic index building**: The component no longer tries to build the index automatically except when the rebuild button is clicked
- **Index paths**: Corrected to match the actual locations from `colbert_rag.py`:
  - Metadata: `data/Projects/{ACTIVE_PROJECT}/colbert_indexes/email_metadata.pkl`
  - RAGAtouille index: `.ragatouille/colbert/indexes/emails_index`
- **Search functionality**: Now uses `colbert_rag_answer` instead of just `search_with_colbert` for better results with generated answers
- **Index check**: Added warning when index doesn't exist
- **Simplified flow**: Removed unnecessary index initialization calls except in the rebuild button

### 2. Updated `app.py`

- Added error handling for the ColBERT RAG page to catch import errors

## New Function Signatures

### From `colbert_rag.py`:

```python
def search_with_colbert(
    query: str, 
    path_to_metadata: str, 
    ragatouille_index_path: str, 
    top_k: int = 5
) -> List[Dict[str, Any]]

def colbert_rag_answer(
    query: str, 
    path_to_metadata: str, 
    ragatouille_index_path: str, 
    top_k: int = 5
) -> Tuple[str, List[str]]
```

### From `colbert_initialization.py`:

```python
def initialize_colbert_rag_system(
    ids_series: Optional[pd.DataFrame] = None,
    project_root: Optional[str] = None,
    force_rebuild: bool = False,
    test_mode: bool = False,
) -> str
```

## Index Locations

The indexes are stored in two locations:
1. **Metadata**: `{project_root}/data/Projects/{ACTIVE_PROJECT}/colbert_indexes/email_metadata.pkl`
2. **RAGAtouille index**: `{project_root}/.ragatouille/colbert/indexes/emails_index`

## Usage Notes

1. **Index Creation**: The index must be created before using the app:
   - Either run `python src/rag/colbert_initialization.py` directly
   - Or use the "Créer/Recréer l'index" button in the Configuration tab
2. **No Auto-initialization**: The app will not automatically create indexes - it expects them to exist
3. **Search Tab**: Now uses `colbert_rag_answer` which provides both an answer and source emails
4. **Q&A Tab**: Uses the same `colbert_rag_answer` function for consistent behavior

## Testing

To test the updated system:
1. Ensure the `ACTIVE_PROJECT` constant in `constants.py` matches your project name
2. Create the index using one of the methods above
3. Launch the app and navigate to the "Colbert RAG" page
4. Try both search and Q&A functionality
5. The Configuration tab should show the index status and allow rebuilding
