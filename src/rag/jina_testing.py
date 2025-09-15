
import os
import sys
import pandas as pd
from typing import Optional
import time


import os
import time
# import mailbox
from typing import List, Dict, Any, Tuple
import pickle
# from pathlib import Path
import textwrap
import sys


# Quick fix to ensure AdamW is available
import transformers
from torch.optim import AdamW
transformers.AdamW = AdamW

from ragatouille import RAGPretrainedModel




# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


from src.rag.colbert_rag import (
    initialize_colbert_rag,
    prepare_email_for_rag
    # load_and_prepare_emails,
    # get_all_mbox_paths
)

from src.data.email_analyzer import EmailAnalyzer

from constants import ACTIVE_PROJECT

# These models work better on Apple Silicon without flash_attn
models_to_try = [
    "sentence-transformers/all-MiniLM-L6-v2",  # Lightweight, Mac-friendly
    "colbert-ir/colbertv2.0",                  # Standard ColBERT
    "answerdotai/answerai-colbert-small-v1"    # Smaller model
]

for model_name in models_to_try:
    try:
        rag_model = RAGPretrainedModel.from_pretrained(model_name)
        print(f"Successfully loaded: {model_name}")
        break
    except Exception as e:
        print(f"Failed: {model_name} - {e}")
        continue