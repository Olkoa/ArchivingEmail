import re
from collections import defaultdict

def parse_schema(schema_str):
    """Parse the SQL schema string into a structured format."""
    # Convert string representation to actual list of tuples
    schema_list = eval(schema_str)

    # Organize by table
    tables = defaultdict(list)
    for schema, table, column, data_type in schema_list:
        tables[table].append((column, data_type))

    return tables

def identify_relationships(tables):
    """Identify relationships between tables based on foreign key patterns."""
    relationships = []

    # Find foreign keys based on naming patterns
    fk_pattern = re.compile(r'(.+)_id$')

    for table_name, columns in tables.items():
        for column_name, _ in columns:
            # Skip primary key columns named 'id'
            if column_name == 'id':
                continue

            match = fk_pattern.match(column_name)
            if match:
                referenced_table = match.group(1)
                # Special case for email_id since there are two email tables
                if referenced_table == 'email':
                    # Check context to determine which email table it refers to
                    if table_name.startswith('email_recipients'):
                        relationships.append((table_name, 'receiver_emails', f"{table_name}.{column_name}"))
                    else:
                        # For attachments and others, we need to check if sender or receiver makes more sense
                        if 'sender' in table_name:
                            relationships.append((table_name, 'sender_emails', f"{table_name}.{column_name}"))
                        else:
                            relationships.append((table_name, 'receiver_emails', f"{table_name}.{column_name}"))
                # Special case for entity_id
                elif referenced_table == 'entity' and 'entities' in tables:
                    relationships.append((table_name, 'entities', f"{table_name}.{column_name}"))
                # Special case for sender_id in emails
                elif column_name == 'sender_id':
                    relationships.append((table_name, 'entities', f"{table_name}.{column_name}"))
                # Regular case - if the referenced table exists
                elif f"{referenced_table}s" in tables:
                    relationships.append((table_name, f"{referenced_table}s", f"{table_name}.{column_name}"))
                elif referenced_table in tables:
                    relationships.append((table_name, referenced_table, f"{table_name}.{column_name}"))

    # Add specific relationships based on domain knowledge
    relationships.append(('email_children', 'receiver_emails', 'email_children.parent_id'))
    relationships.append(('email_children', 'receiver_emails', 'email_children.child_id'))

    # Remove duplicates while preserving order
    unique_relationships = []
    for rel in relationships:
        if rel not in unique_relationships:
            unique_relationships.append(rel)

    return unique_relationships

def generate_mermaid(tables, relationships):
    """Generate a Mermaid ER diagram based on tables and relationships."""
    mermaid = ["```mermaid", "erDiagram"]

    # Add entities with attributes
    for table_name, columns in tables.items():
        entity_def = [f"    {table_name} {{"]

        for column_name, data_type in columns:
            # Format the data type to be lowercase
            formatted_type = data_type.lower()
            entity_def.append(f"        {formatted_type} {column_name}")

        entity_def.append("    }")
        mermaid.append("\n".join(entity_def))

    # Add relationships
    for from_table, to_table, fk in relationships:
        # Determine cardinality (simplified for this example - assuming many-to-one)
        if '_children' in from_table or '_recipients' in from_table:
            cardinality = "many-to-many"
            relation = "||--o{"
        elif from_table.endswith('s') and not to_table.endswith('s'):
            cardinality = "one-to-many"
            relation = "}o--||"
        else:
            cardinality = "many-to-one"
            relation = "}o--||"

        mermaid.append(f"    {from_table} {relation} {to_table} : \"{cardinality}\"")

    mermaid.append("```")
    return "\n".join(mermaid)

def sql_schema_to_mermaid(schema_str):
    """Main function to convert SQL schema to Mermaid ER diagram."""
    tables = parse_schema(schema_str)
    relationships = identify_relationships(tables)
    return generate_mermaid(tables, relationships)

# Example usage
if __name__ == "__main__":
    # Sample schema string from the example
    schema_str = """[('main', 'attachments', 'id', 'VARCHAR'), ('main', 'attachments', 'email_id', 'VARCHAR'), ('main', 'attachments', 'filename', 'VARCHAR'), ('main', 'attachments', 'content', 'BLOB'), ('main', 'attachments', 'content_type', 'VARCHAR'), ('main', 'attachments', 'size', 'INTEGER'), ('main', 'email_children', 'parent_id', 'VARCHAR'), ('main', 'email_children', 'child_id', 'VARCHAR'), ('main', 'email_recipients_bcc', 'email_id', 'VARCHAR'), ('main', 'email_recipients_bcc', 'entity_id', 'VARCHAR'), ('main', 'email_recipients_cc', 'email_id', 'VARCHAR'), ('main', 'email_recipients_cc', 'entity_id', 'VARCHAR'), ('main', 'email_recipients_to', 'email_id', 'VARCHAR'), ('main', 'email_recipients_to', 'entity_id', 'VARCHAR'), ('main', 'entities', 'id', 'VARCHAR'), ('main', 'entities', 'name', 'VARCHAR'), ('main', 'entities', 'email', 'VARCHAR'), ('main', 'entities', 'alias_names', 'JSON'), ('main', 'entities', 'is_physical_person', 'BOOLEAN'), ('main', 'entity_alias_emails', 'id', 'VARCHAR'), ('main', 'entity_alias_emails', 'entity_id', 'VARCHAR'), ('main', 'entity_alias_emails', 'email', 'VARCHAR'), ('main', 'entity_positions', 'entity_id', 'VARCHAR'), ('main', 'entity_positions', 'position_id', 'VARCHAR'), ('main', 'mailing_lists', 'id', 'VARCHAR'), ('main', 'mailing_lists', 'name', 'VARCHAR'), ('main', 'mailing_lists', 'description', 'VARCHAR'), ('main', 'mailing_lists', 'email_address', 'VARCHAR'), ('main', 'organizations', 'id', 'VARCHAR'), ('main', 'organizations', 'name', 'VARCHAR'), ('main', 'organizations', 'description', 'VARCHAR'), ('main', 'organizations', 'email_address', 'VARCHAR'), ('main', 'positions', 'id', 'VARCHAR'), ('main', 'positions', 'name', 'VARCHAR'), ('main', 'positions', 'start_date', 'TIMESTAMP'), ('main', 'positions', 'end_date', 'TIMESTAMP'), ('main', 'positions', 'description', 'VARCHAR'), ('main', 'positions', 'organization_id', 'VARCHAR'), ('main', 'receiver_emails', 'id', 'VARCHAR'), ('main', 'receiver_emails', 'sender_email_id', 'VARCHAR'), ('main', 'receiver_emails', 'sender_id', 'VARCHAR'), ('main', 'receiver_emails', 'reply_to_id', 'VARCHAR'), ('main', 'receiver_emails', 'timestamp', 'TIMESTAMP'), ('main', 'receiver_emails', 'subject', 'VARCHAR'), ('main', 'receiver_emails', 'body', 'VARCHAR'), ('main', 'receiver_emails', 'body_html', 'VARCHAR'), ('main', 'receiver_emails', 'has_html', 'BOOLEAN'), ('main', 'receiver_emails', 'is_deleted', 'BOOLEAN'), ('main', 'receiver_emails', 'folder', 'VARCHAR'), ('main', 'receiver_emails', 'is_spam', 'BOOLEAN'), ('main', 'receiver_emails', 'mailing_list_id', 'VARCHAR'), ('main', 'receiver_emails', 'importance_score', 'INTEGER'), ('main', 'receiver_emails', 'mother_email_id', 'VARCHAR'), ('main', 'receiver_emails', 'message_id', 'VARCHAR'), ('main', 'receiver_emails', 'references', 'VARCHAR'), ('main', 'receiver_emails', 'in_reply_to', 'VARCHAR'), ('main', 'sender_emails', 'id', 'VARCHAR'), ('main', 'sender_emails', 'sender_id', 'VARCHAR'), ('main', 'sender_emails', 'body', 'VARCHAR'), ('main', 'sender_emails', 'timestamp', 'TIMESTAMP')]"""

    mermaid_diagram = sql_schema_to_mermaid(schema_str)
    print(mermaid_diagram)
