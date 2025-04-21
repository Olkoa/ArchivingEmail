from src.data.eml_transformation import process_eml_files

import argparse

def main() -> bool:
    pass

    # for folder in


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process EML files into a DuckDB database')
    parser.add_argument('path_to_eml', nargs='?', default="data/processed/celine_readpst_with_S",
                        help='Path to the directory containing EML files')
    parser.add_argument('path_for_db', nargs='?', default="data/Projects/Boîte mail de Céline/celine.duckdb",
                        help='Path where the DuckDB file should be created')

    # Parse arguments
    args = parser.parse_args()

    # Process the files using the provided arguments
    process_eml_files(args.path_to_eml, args.path_for_db)
