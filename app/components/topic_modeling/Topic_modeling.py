import nltk
import os
from pathlib import Path
import importlib
import sys
from dotenv import load_dotenv
load_dotenv()

ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

from .eml_json import run_email_extraction
from .bertopicgpu import bertopic_modeling
from .transform_bert import transform_bert
from .split_topic import split_topics
from .gpt4_1 import summarize_topics
from .k_medioid import run_kmedoid_clustering
from .k_plot import kmedoid_plotting
from .merge import merge_topic_summaries
from .data_proc import data_proc
from .kdist import k_distance_plot
from .data_proc2 import update_df_with_medoid_indices
from .hierachical_clust import hierarchical_clustering
from .cluster_tree import build_cluster_tree


# Resolve repository root (…/olkoa)
REPO_ROOT = Path(__file__).resolve().parents[3]

TOPICS_GRAPHS_PATH = REPO_ROOT / "data" / "Projects" / (ACTIVE_PROJECT or "") / "Topics_GRAPHS_PATHS.json"

def topic_build(topics_graphs_path: Path | None = None):
    """Extract EML content for the active project to support topic modeling."""
    nltk.download("stopwords")

    if not ACTIVE_PROJECT:
        print("🔁 ACTIVE_PROJECT environment variable is not set; skipping topic_build.")
        return

    eml_folder = REPO_ROOT / "data" / "Projects" / ACTIVE_PROJECT
    if not eml_folder.exists():
        print(f"⚠️ No EML directory found at {eml_folder}")
        return

    print(f"🔎 Scanning EML files under: {eml_folder}")
    run_email_extraction(
        EML_FOLDER=str(eml_folder),
        MAILBOX_NAME="Boîte envoyés",
        MAILBOX_PATH=str(eml_folder),
    ) # eml_json

    bertopic_modeling() # bertopicgpu

    #### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    transform_bert() # transform_bert

    #### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    split_topics()  # split_topic 

    #### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    summarize_topics()  # gpt4_1
    
    #### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    run_kmedoid_clustering()  # k_medioid

    #### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    kmedoid_plotting() # k_plot

    ##### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    merge_topic_summaries() # merge

    ##### Ugly hardcoded split into two topics while we should grow the number of splits based on arbitrary mailbox size
    data_proc() # data_proc

    k_distance_plot() # kdist

    ## Not needed imo import score_plot

    update_df_with_medoid_indices() # data_proc2
    
    hierarchical_clustering() # hierachical_clust

    build_cluster_tree(TOPICS_GRAPHS_PATH) # cluster_tree

if __name__ == "__main__":
    topic_build(TOPICS_GRAPHS_PATH)
