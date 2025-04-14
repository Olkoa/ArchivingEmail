from typing import Union
import duckdb
from pathlib import Path
import logging


def setup_database(db_path: Union[str, Path]) -> duckdb.DuckDBPyConnection:
    """Set up the DuckDB database schema with proper types and indexes

    Args:
        db_path: Path to the DuckDB database file or ":memory:" for in-memory database

    Returns:
        A connection to the configured DuckDB database
    """
    # Connect to DuckDB database
    conn = duckdb.connect(db_path)

    # Create tables for each Pydantic model

    # Organizations table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        description VARCHAR,
        email_address VARCHAR
    )
    """)

    # Positions table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
        description VARCHAR,
        organization_id VARCHAR,
        FOREIGN KEY (organization_id) REFERENCES organizations(id)
    )
    """)

    # Entities table (for senders and recipients)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        email VARCHAR,
        alias_names JSON,
        is_physical_person BOOLEAN
    )
    """)

    # Entity alias emails table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS entity_alias_emails (
        id VARCHAR PRIMARY KEY,
        entity_id VARCHAR,
        email VARCHAR,
        FOREIGN KEY (entity_id) REFERENCES entities(id)
    )
    """)

    # Entity positions table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS entity_positions (
        entity_id VARCHAR,
        position_id VARCHAR,
        PRIMARY KEY (entity_id, position_id),
        FOREIGN KEY (entity_id) REFERENCES entities(id),
        FOREIGN KEY (position_id) REFERENCES positions(id)
    )
    """)

    # Mailing lists table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS mailing_lists (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        description VARCHAR,
        email_address VARCHAR
    )
    """)

    # Sender emails table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sender_emails (
        id VARCHAR PRIMARY KEY,
        sender_id VARCHAR,
        body TEXT,
        timestamp TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES entities(id)
    )
    """)

    # Receiver emails table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS receiver_emails (
        id VARCHAR PRIMARY KEY,
        sender_email_id VARCHAR,
        sender_id VARCHAR,
        reply_to_id VARCHAR,
        timestamp TIMESTAMP,
        subject VARCHAR,
        body TEXT,
        is_deleted BOOLEAN DEFAULT FALSE,
        folder VARCHAR DEFAULT 'inbox',
        is_spam BOOLEAN DEFAULT FALSE,
        mailing_list_id VARCHAR,
        importance_score INTEGER DEFAULT 0,
        mother_email_id VARCHAR,
        message_id VARCHAR,
        "references" TEXT,
        in_reply_to VARCHAR,
        FOREIGN KEY (sender_email_id) REFERENCES sender_emails(id),
        FOREIGN KEY (sender_id) REFERENCES entities(id),
        FOREIGN KEY (reply_to_id) REFERENCES entities(id),
        FOREIGN KEY (mailing_list_id) REFERENCES mailing_lists(id),
        FOREIGN KEY (mother_email_id) REFERENCES receiver_emails(id)
    )
    """)

    # Email recipients tables (to, cc, bcc)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS email_recipients_to (
        email_id VARCHAR,
        entity_id VARCHAR,
        PRIMARY KEY (email_id, entity_id),
        FOREIGN KEY (email_id) REFERENCES receiver_emails(id),
        FOREIGN KEY (entity_id) REFERENCES entities(id)
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS email_recipients_cc (
        email_id VARCHAR,
        entity_id VARCHAR,
        PRIMARY KEY (email_id, entity_id),
        FOREIGN KEY (email_id) REFERENCES receiver_emails(id),
        FOREIGN KEY (entity_id) REFERENCES entities(id)
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS email_recipients_bcc (
        email_id VARCHAR,
        entity_id VARCHAR,
        PRIMARY KEY (email_id, entity_id),
        FOREIGN KEY (email_id) REFERENCES receiver_emails(id),
        FOREIGN KEY (entity_id) REFERENCES entities(id)
    )
    """)

    # Attachments table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id VARCHAR PRIMARY KEY,
        email_id VARCHAR,
        filename VARCHAR,
        content BLOB,
        content_type VARCHAR,
        size INTEGER,
        FOREIGN KEY (email_id) REFERENCES receiver_emails(id)
    )
    """)

    # Create child email relationships table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS email_children (
        parent_id VARCHAR,
        child_id VARCHAR,
        PRIMARY KEY (parent_id, child_id),
        FOREIGN KEY (parent_id) REFERENCES receiver_emails(id),
        FOREIGN KEY (child_id) REFERENCES receiver_emails(id)
    )
    """)

    # Create indexes
    conn.execute('CREATE INDEX IF NOT EXISTS idx_receiver_emails_timestamp ON receiver_emails(timestamp)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_receiver_emails_folder ON receiver_emails(folder)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_receiver_emails_subject ON receiver_emails(subject)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_receiver_emails_message_id ON receiver_emails(message_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_entities_email ON entities(email)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_attachments_email_id ON attachments(email_id)')

    return conn



def find_email_references(db_path: Union[str, Path], email_id: str) -> dict:
    """
    Find all references to a specific email ID across all tables in the database.

    Args:
        db_path: Path to the DuckDB database file
        email_id: The email ID to search for

    Returns:
        dict: A dictionary with table names as keys and lists of matching column names as values
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info(f"Connecting to database at {db_path}")
    conn = duckdb.connect(db_path)

    try:
        # Get a list of all tables
        tables_result = conn.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """).fetchall()
        tables = [row[0] for row in tables_result]

        logger.info(f"Found {len(tables)} tables to check")

        # Get a list of all columns in each table
        all_tables_columns = {}
        for table in tables:
            cols_result = conn.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'main' AND table_name = '{table}'
            """).fetchall()
            all_tables_columns[table] = [(row[0], row[1]) for row in cols_result]

        # Check each table for references to the email ID
        references = {}

        for table, columns in all_tables_columns.items():
            logger.info(f"Checking table: {table}")

            table_references = []

            for column_name, data_type in columns:
                # Only check string-like columns that could hold IDs
                if 'char' in data_type.lower() or 'varchar' in data_type.lower():
                    try:
                        result = conn.execute(f"""
                            SELECT COUNT(*)
                            FROM {table}
                            WHERE {column_name} = ?
                        """, [email_id]).fetchone()

                        count = result[0] if result else 0

                        if count > 0:
                            logger.info(f"Found {count} references in {table}.{column_name}")
                            table_references.append(column_name)

                            # Get some sample rows to better understand the reference
                            sample_rows = conn.execute(f"""
                                SELECT *
                                FROM {table}
                                WHERE {column_name} = ?
                                LIMIT 3
                            """, [email_id]).fetchall()

                            # Get column names for this table
                            col_names = [col[0] for col in all_tables_columns[table]]

                            # Log sample rows
                            for row in sample_rows:
                                row_dict = {col_names[i]: row[i] for i in range(len(col_names))}
                                logger.info(f"Sample row: {row_dict}")

                    except Exception as e:
                        logger.error(f"Error checking {table}.{column_name}: {e}")

            if table_references:
                references[table] = table_references

        if not references:
            logger.info(f"No references found for email ID: {email_id}")
        else:
            logger.info(f"Found references in {len(references)} tables: {list(references.keys())}")

        return references

    except Exception as e:
        logger.error(f"Error in find_email_references: {e}")
        raise

    finally:
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    db_path="data/Projects/database.duckdb"

    # Example usage
    # email_id = "509779ea-9914-4b3b-8a9a-edfc32498383"  # The problematic ID from the error message
    # references = find_email_references(db_path, email_id)
