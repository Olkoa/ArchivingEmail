"""Semantic search configuration utilities."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _active_project(project: str | None = None) -> str:
    project_name = project or os.getenv("ACTIVE_PROJECT")
    if not project_name:
        raise RuntimeError(
            "ACTIVE_PROJECT environment variable is not set; semantic search paths "
            "cannot be resolved."
        )
    return project_name


def project_data_dir(project: str | None = None) -> Path:
    return PROJECT_ROOT / "data" / "Projects" / _active_project(project)


def semantic_base_dir(project: str | None = None) -> Path:
    return project_data_dir(project) / "semantic_search"


def topic_dir(project: str | None = None) -> Path:
    return semantic_base_dir(project) / "topic"


def embeddings_path(project: str | None = None) -> Path:
    return topic_dir(project) / "topics_embeddings.npy"


def chunks_path(project: str | None = None) -> Path:
    return topic_dir(project) / "topics_chunks.npy"


def vis_emb_2d_path(project: str | None = None) -> Path:
    return topic_dir(project) / "emb_2d.npy"


def vis_labels_path(project: str | None = None) -> Path:
    return topic_dir(project) / "labels.npy"


def vis_chunks_path(project: str | None = None) -> Path:
    return topic_dir(project) / "chunks.pkl"


def results_dir(project: str | None = None) -> Path:
    return semantic_base_dir(project) / "results"


# Stopwords pour le Bag-of-Words
STOPWORDS = [
    "alors",
    "au",
    "aucuns",
    "aussi",
    "autre",
    "avant",
    "avec",
    "avoir",
    "bon",
    "car",
    "ce",
    "cela",
    "ces",
    "ceux",
    "chaque",
    "ci",
    "comme",
    "comment",
    "dans",
    "des",
    "du",
    "dedans",
    "dehors",
    "depuis",
    "devrait",
    "doit",
    "donc",
    "dos",
    "droite",
    "début",
    "elle",
    "elles",
    "en",
    "encore",
    "essai",
    "est",
    "et",
    "eu",
    "fait",
    "faites",
    "fois",
    "font",
    "hors",
    "ici",
    "il",
    "ils",
    "je",
    "juste",
    "la",
    "le",
    "les",
    "leur",
    "là",
    "ma",
    "maintenant",
    "mais",
    "mes",
    "mine",
    "moins",
    "mon",
    "mot",
    "même",
    "ni",
    "nommés",
    "notre",
    "nous",
    "nouveaux",
    "ou",
    "où",
    "par",
    "parce",
    "parole",
    "pas",
    "personnes",
    "peut",
    "peu",
    "pièce",
    "plupart",
    "pour",
    "pourquoi",
    "quand",
    "que",
    "quel",
    "quelle",
    "quelles",
    "quels",
    "qui",
    "sa",
    "sans",
    "ses",
    "seulement",
    "si",
    "sien",
    "son",
    "sont",
    "sous",
    "soyez",
    "sujet",
    "sur",
    "ta",
    "tandis",
    "tellement",
    "tels",
    "tes",
    "ton",
    "tous",
    "tout",
    "trop",
    "très",
    "tu",
    "valeur",
    "voie",
    "voient",
    "vont",
    "votre",
    "vous",
    "vu",
    "ça",
    "étaient",
    "état",
    "étions",
    "été",
    "être",
]
