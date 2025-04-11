import duckdb
import pandas as pd
import re


class EmailAnalyzer:
    """Class for analyzing the email database using DuckDB"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to the database"""
        if not self.conn:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_email_summary(self):
        """Get a summary of emails in the database"""
        conn = self.connect()

        # Get basic statistics
        stats = {}

        # Total emails
        result = conn.execute("SELECT COUNT(*) FROM receiver_emails").fetchone()
        stats['total_emails'] = result[0]

        # Emails by folder
        result = conn.execute("""
            SELECT folder, COUNT(*) as count
            FROM receiver_emails
            GROUP BY folder
            ORDER BY count DESC
        """).fetchall()
        stats['emails_by_folder'] = [{"folder": row[0], "count": row[1]} for row in result]

        # Emails by year
        result = conn.execute("""
            SELECT strftime('%Y', timestamp) AS year, COUNT(*) AS count
            FROM receiver_emails
            GROUP BY year
            ORDER BY year
        """).fetchall()
        stats['emails_by_year'] = [{"year": row[0], "count": row[1]} for row in result]

        # Top senders
        result = conn.execute("""
            SELECT e.name AS "from", COUNT(*) AS count
            FROM receiver_emails re
            JOIN entities e ON re.sender_id = e.id
            GROUP BY e.name
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        stats['top_senders'] = [{"from": row[0], "count": row[1]} for row in result]

        # Emails with attachments
        result = conn.execute("""
            SELECT COUNT(DISTINCT email_id)
            FROM attachments
        """).fetchone()
        stats['emails_with_attachments'] = result[0]

        return stats

    def search_emails(self, query, limit=100):
        """Search emails by text content"""
        conn = self.connect()

        # In the receiver_emails table, we use body field
        search_column = 'body'

        # Perform the search
        result = conn.execute(f"""
            SELECT re.message_id, re.subject,
                   sender.name AS "from",
                   (SELECT string_agg(e.name, ', ')
                    FROM email_recipients_to ert
                    JOIN entities e ON ert.entity_id = e.id
                    WHERE ert.email_id = re.id) AS "to",
                   re.timestamp AS date, re.folder
            FROM receiver_emails re
            JOIN entities sender ON re.sender_id = sender.id
            WHERE re.body LIKE ?
            ORDER BY re.timestamp DESC
            LIMIT ?
        """, (f'%{query}%', limit)).fetchall()

        return [self._row_to_dict(row, ["message_id", "subject", "from", "to", "date", "folder"])
                for row in result]

    def get_email_content(self, message_id):
        """Get full content of a specific email by message_id"""
        conn = self.connect()

        query = """
            SELECT re.*,
                sender.name AS sender_name,
                sender.email AS sender_email,
                (SELECT string_agg(e.name, ', ')
                 FROM email_recipients_to ert
                 JOIN entities e ON ert.entity_id = e.id
                 WHERE ert.email_id = re.id) AS to_recipients,
                (SELECT string_agg(e.name, ', ')
                 FROM email_recipients_cc ercc
                 JOIN entities e ON ercc.entity_id = e.id
                 WHERE ercc.email_id = re.id) AS cc_recipients,
                CASE WHEN has_html = TRUE THEN body_html ELSE body END AS content
            FROM receiver_emails re
            JOIN entities sender ON re.sender_id = sender.id
            WHERE re.message_id = ?
        """

        result = conn.execute(query, (message_id,)).fetchone()
        if result:
            # Get column names to create dictionary
            columns = conn.execute("SELECT * FROM receiver_emails WHERE 1=0").description
            base_column_names = [col[0] for col in columns]
            # Add additional columns from the joined query
            all_column_names = base_column_names + ['sender_name', 'sender_email', 'to_recipients', 'cc_recipients', 'content']
            return self._row_to_dict(result, all_column_names)
        return None

    def get_conversation_thread(self, message_id):
        """Get all emails in the same conversation thread"""
        conn = self.connect()

        # First get the current email to find its references or in-reply-to
        result = conn.execute("""
            SELECT message_id, "references", in_reply_to, subject
            FROM receiver_emails
            WHERE message_id = ?
        """, (message_id,)).fetchone()

        if not result:
            return []

        email = self._row_to_dict(result, ["message_id", "references", "in_reply_to", "subject"])

        # Find related messages by references, in-reply-to, or subject thread
        message_ids = set()

        # Add current message
        message_ids.add(email['message_id'])

        # Add messages this email is replying to
        if email['in_reply_to']:
            message_ids.add(email['in_reply_to'])

        # Add messages referenced
        if email['references']:
            ref_ids = re.findall(r'<([^>]+)>', email['references'])
            message_ids.update(ref_ids)

        # Find messages that reply to this one
        result = conn.execute("""
            SELECT message_id
            FROM receiver_emails
            WHERE in_reply_to = ?
        """, (email['message_id'],)).fetchall()

        for row in result:
            message_ids.add(row[0])

        # Also find messages with the same subject (ignoring Re:, Fwd:, etc.)
        if email['subject']:
            clean_subject = re.sub(r'^(Re|Fwd|Fw|TR)(\[\d+\])?:\s*', '', email['subject'], flags=re.IGNORECASE)
            if clean_subject:
                result = conn.execute("""
                    SELECT message_id
                    FROM receiver_emails
                    WHERE subject LIKE ? AND message_id != ?
                """, (f'%{clean_subject}%', email['message_id'])).fetchall()

                for row in result:
                    message_ids.add(row[0])

        # Now get all the emails in the thread
        if message_ids:
            placeholders = ', '.join(['?'] * len(message_ids))
            result = conn.execute(f"""
                SELECT re.message_id, re.subject,
                       sender.name AS "from",
                       re.timestamp AS date,
                       (SELECT string_agg(e.name, ', ')
                        FROM email_recipients_to ert
                        JOIN entities e ON ert.entity_id = e.id
                        WHERE ert.email_id = re.id) AS "to",
                       (SELECT string_agg(e.name, ', ')
                        FROM email_recipients_cc ercc
                        JOIN entities e ON ercc.entity_id = e.id
                        WHERE ercc.email_id = re.id) AS cc
                FROM receiver_emails re
                JOIN entities sender ON re.sender_id = sender.id
                WHERE re.message_id IN ({placeholders})
                ORDER BY re.timestamp
            """, list(message_ids)).fetchall()

            column_names = ["message_id", "subject", "from", "date", "to", "cc"]
            return [self._row_to_dict(row, column_names) for row in result]
        return []

    def export_to_dataframe(self, query=None, limit=None):
        """Export emails to a pandas DataFrame for analysis"""
        conn = self.connect()

        if query:
            sql = f"{query}"
            if limit:
                sql += f" LIMIT {limit}"
            # DuckDB can return pandas DataFrame directly
            df = conn.execute(sql).df()
        else:
            # Default query to get important fields
            sql = """
                SELECT re.message_id, re.subject,
                       sender.name AS "from",
                       (SELECT string_agg(e.name, ', ')
                        FROM email_recipients_to ert
                        JOIN entities e ON ert.entity_id = e.id
                        WHERE ert.email_id = re.id) AS "to",
                       re.timestamp AS date,
                       re.folder,
                       (SELECT COUNT(*) FROM attachments a WHERE a.email_id = re.id) AS attachment_count,
                       re.body
                FROM receiver_emails re
                JOIN entities sender ON re.sender_id = sender.id
            """
            if limit:
                sql += f" LIMIT {limit}"
            df = conn.execute(sql).df()

        # DuckDB should already return timestamp columns in the correct format
        # but we'll make sure just in case
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        return df

    def _row_to_dict(self, row, column_names):
        """Helper method to convert a row tuple to a dictionary"""
        return {column_names[i]: row[i] for i in range(len(column_names)) if i < len(row)}
