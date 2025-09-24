"""
Global constants for the Okloa project.
"""

# Email display options: "MODAL" or "POPOVER"
EMAIL_DISPLAY_TYPE = "MODAL"  # Change to "POPOVER" for hover-based display

# UI Configuration
UI_LANGUAGE = "FRENCH"  # Options: "FRENCH", "ENGLISH"
SIDEBAR_STATE = "expanded"  # Options: "expanded", "collapsed"

# Features Configuration
ENABLE_ELASTICSEARCH = False  # Set to True to use real Elasticsearch instead of mock mode
ENABLE_RAG = True  # Set to False to disable RAG features

# RAG/LLM behaviour
ALLOW_LLM_UNRELATED_REQUESTS = False

###
ACTIVE_PROJECT = "joel_sample_v1"

# Project order - Most recently accessed projects will appear first
# Format: List of project names in display order
PROJECT_ORDER = ["joel_sample_v1", "single_eml_proj", "Projet Demo", "celinev3", "eldino_proj", "pst_proj", "dino_v2_proj", "dodo", "doni", "celinev2", "dinodelanight", "ledinovivra_proj", "newdino_proj", "dinofiable_proj", "diplodocus_proj", "din_proj", "dinosur_proj", "dinosisi", "ccccccc"]
