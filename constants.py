"""
Global constants for the Olkoa project.
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
ACTIVE_PROJECT = "5_Joel_Gombin"

# Project order - Most recently accessed projects will appear first
# Format: List of project names in display order
PROJECT_ORDER = ["5_Joel_Gombin", "5_Joel_G", "5_Celine_full", "5_Celine", "5_Joel_sample", "CelineWithSemSearch", "4_Joel_Sample", "3_joel_sample", "enrontodelete", "3_Celine", "psttodelete", "idiro", "3_Dino", "joel_sample_v1", "3_3pst", "pst_test_graph", "Dino test", "celinev3", "dino_v2_proj", "pst_proj", "single_eml_proj", "dinodelanight", "joel_zip_full_proj", "Projet Demo", "eldino_proj", "dodo", "doni", "celinev2", "ledinovivra_proj", "newdino_proj", "dinofiable_proj", "diplodocus_proj", "din_proj", "dinosur_proj", "dinosisi", "ccccccc"]
