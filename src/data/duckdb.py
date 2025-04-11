from typing import Union
import duckdb
from pathlib import Path

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
        body_html TEXT,
        has_html BOOLEAN,
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
