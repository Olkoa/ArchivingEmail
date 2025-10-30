import nltk
import os
from pathlib import Path
import importlib
import sys
import json

import pandas as pd
import duckdb
from dotenv import load_dotenv

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

def _persist_topics_to_db(project_name: str, module_dir: Path):
    try:
        clusters_path = module_dir / "clusters_by_height_filtered.csv"
        topics_path = module_dir / "bertopic_output.csv"
        outputs_dir = module_dir / "outputs_by_height"

        if not clusters_path.exists() or not topics_path.exists():
            print("[topics] Required files not found; skipping persistence.")
            return

        clusters_df = pd.read_csv(clusters_path)
        if 'topic' not in clusters_df.columns:
            print("[topics] clusters_by_height_filtered.csv missing 'topic' column.")
            return

        height_columns = [col for col in clusters_df.columns if col.startswith('height_')]
        if not height_columns:
            print("[topics] No height columns detected; skipping persistence.")
            return

        clusters_df = clusters_df.copy()
        clusters_df['topic'] = pd.to_numeric(clusters_df['topic'], errors='coerce').astype('Int64')
        clusters_df = clusters_df.dropna(subset=['topic'])
        clusters_df['topic'] = clusters_df['topic'].astype(int)

        topic_assignments = []
        available_heights = []
        for col in height_columns:
            try:
                height_value = float(col.split('_', 1)[1])
            except (IndexError, ValueError):
                continue

            sub = clusters_df[['topic', col]].rename(columns={col: 'cluster_id'}).copy()
            sub['height'] = height_value
            sub['cluster_id'] = pd.to_numeric(sub['cluster_id'], errors='coerce').astype('Int64')
            sub = sub.dropna(subset=['cluster_id'])
            sub['cluster_id'] = sub['cluster_id'].astype(int)
            topic_assignments.append(sub)
            available_heights.append(height_value)

        if not topic_assignments:
            print("[topics] No topic assignments generated; skipping persistence.")
            return

        topic_assignment_df = pd.concat(topic_assignments, ignore_index=True)

        topics_df = pd.read_csv(topics_path)
        if 'topic' not in topics_df.columns or 'message_id' not in topics_df.columns:
            print("[topics] bertopic_output.csv missing required columns; skipping persistence.")
            return

        email_topics_df = topics_df[['message_id', 'topic']].copy()
        email_topics_df = email_topics_df.dropna(subset=['message_id'])
        email_topics_df['topic'] = pd.to_numeric(email_topics_df['topic'], errors='coerce').astype('Int64')
        email_topics_df = email_topics_df.dropna(subset=['topic'])
        email_topics_df = email_topics_df[email_topics_df['topic'] != -1]
        email_topics_df['topic'] = email_topics_df['topic'].astype(int)

        email_cluster_df = email_topics_df.merge(
            topic_assignment_df,
            left_on='topic',
            right_on='topic',
            how='left'
        )
        email_cluster_df = email_cluster_df.dropna(subset=['cluster_id'])
        email_cluster_df['cluster_id'] = email_cluster_df['cluster_id'].astype(int)

        summaries_records = []
        unique_heights = sorted({float(f"{h:.2f}") for h in available_heights})

        for height_value in unique_heights:
            clusters_for_height = topic_assignment_df[topic_assignment_df['height'] == height_value]['cluster_id'].unique()
            summary_file = outputs_dir / f"topic_summaries_{height_value}.json"
            summaries_data = {}
            if summary_file.exists():
                try:
                    with summary_file.open('r', encoding='utf-8') as sf:
                        raw = json.load(sf)
                        summaries_data = {
                            (int(key.split('_', 1)[1]) if str(key).startswith('topic_') else int(key)): value
                            for key, value in raw.items() if str(key).strip()
                        }
                except Exception as summary_error:
                    print(f"[topics] Failed to load summaries for height {height_value}: {summary_error}")

            for cluster_id in clusters_for_height:
                summary_text = summaries_data.get(cluster_id)
                if not summary_text or not str(summary_text).strip():
                    summary_text = f"Cluster {cluster_id}"
                summaries_records.append({
                    'height': height_value,
                    'cluster_id': int(cluster_id),
                    'summary': str(summary_text)
                })

        level_map = {height: idx + 1 for idx, height in enumerate(unique_heights)}
        summaries_records = [
            {
                'level': level_map[record['height']],
                'height': record['height'],
                'cluster_id': record['cluster_id'],
                'summary': record['summary']
            }
            for record in summaries_records
        ]

        summaries_df = pd.DataFrame(summaries_records)
        email_cluster_df = email_cluster_df.merge(
            summaries_df,
            on=['height', 'cluster_id'],
            how='left'
        )

        email_cluster_df['level'] = email_cluster_df['level'].astype(int)
        summaries_df['level'] = summaries_df['level'].astype(int)

        db_path = REPO_ROOT / "data" / "Projects" / project_name / f"{project_name}.duckdb"
        if not db_path.exists():
            print(f"[topics] DuckDB database not found at {db_path}; skipping persistence.")
            return

        with duckdb.connect(str(db_path)) as con:
            con.execute("DROP TABLE IF EXISTS topic_clusters")
            con.execute("DROP TABLE IF EXISTS email_topic_clusters")
            con.execute("DROP TABLE IF EXISTS topic_settings")

            con.execute(
                """
                CREATE TABLE topic_clusters (
                    project_name TEXT,
                    level INTEGER,
                    height DOUBLE,
                    cluster_id INTEGER,
                    summary TEXT
                )
                """
            )
            con.execute(
                """
                CREATE TABLE email_topic_clusters (
                    project_name TEXT,
                    message_id TEXT,
                    topic_id INTEGER,
                    level INTEGER,
                    height DOUBLE,
                    cluster_id INTEGER,
                    summary TEXT
                )
                """
            )
            con.execute(
                """
                CREATE TABLE topic_settings (
                    project_name TEXT PRIMARY KEY,
                    selected_level INTEGER,
                    selected_height DOUBLE
                )
                """
            )

            topic_clusters_insert = [
                {
                    'project_name': project_name,
                    'level': record['level'],
                    'height': record['height'],
                    'cluster_id': record['cluster_id'],
                    'summary': record['summary']
                }
                for record in summaries_records
            ]

            clusters_insert_df = pd.DataFrame(topic_clusters_insert).drop_duplicates(subset=["project_name", "level", "cluster_id"])
            if not clusters_insert_df.empty:
                con.register("temp_topic_clusters", clusters_insert_df)
                con.execute(
                    "INSERT INTO topic_clusters SELECT project_name, level, height, cluster_id, summary FROM temp_topic_clusters"
                )
                con.unregister("temp_topic_clusters")

            email_insert_df = email_cluster_df[['message_id', 'topic', 'level', 'height', 'cluster_id', 'summary']].copy()
            email_insert_df.rename(columns={'topic': 'topic_id'}, inplace=True)
            email_insert_df['project_name'] = project_name
            email_insert_df = email_insert_df[['project_name', 'message_id', 'topic_id', 'level', 'height', 'cluster_id', 'summary']]
            email_insert_df = email_insert_df.drop_duplicates(subset=["project_name", "message_id", "level"])

            if not email_insert_df.empty:
                con.register("temp_email_topics", email_insert_df)
                con.execute(
                    "INSERT INTO email_topic_clusters SELECT project_name, message_id, topic_id, level, height, cluster_id, summary FROM temp_email_topics"
                )
                con.unregister("temp_email_topics")

            if not summaries_records:
                default_level = None
                default_height = None
            else:
                max_level = max(level_map.values()) if level_map else None
                if max_level is None:
                    default_level = None
                    default_height = None
                else:
                    default_level = min(4, max_level)
                    for height_value, level_value in level_map.items():
                        if level_value == default_level:
                            default_height = height_value
                            break

            if default_level is not None:
                con.execute(
                    "INSERT INTO topic_settings (project_name, selected_level, selected_height) VALUES (?, ?, ?) "
                    "ON CONFLICT(project_name) DO UPDATE SET "
                    "selected_level = excluded.selected_level, selected_height = excluded.selected_height",
                    [project_name, int(default_level), float(default_height)]
                )

        print(f"[topics] Persisted topic data for project {project_name}.")
    except Exception as error:
        print(f"[topics] Unexpected error while persisting topics: {error}")


def topic_build(topics_graphs_path: Path | None = None):
    """Extract EML content for the active project to support topic modeling."""
    nltk.download("stopwords")

    load_dotenv()

    ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT")

    if not ACTIVE_PROJECT:
        print("🔁 ACTIVE_PROJECT environment variable is not set; skipping topic_build.")
        return

    module_dir = Path(__file__).resolve().parent
    TOPICS_GRAPHS_PATH = REPO_ROOT / "data" / "Projects" / (ACTIVE_PROJECT or "") / "Topics_GRAPHS_PATHS.json"

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
    _persist_topics_to_db(ACTIVE_PROJECT, module_dir=module_dir)

if __name__ == "__main__":
    pass
    # topic_build(TOPICS_GRAPHS_PATH)
