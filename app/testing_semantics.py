import sys
import os

# Add the necessary paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Get project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(project_root)
# Import constants module so we can refresh values when configuration changes
import constants


from src.features.pipeline_data_cleaning import prepare_semantic_search

prepare_semantic_search()