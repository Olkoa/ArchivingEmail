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

        # Debug: Check total entries in receiver_emails right away
        try:
            total = conn.execute("SELECT COUNT(*) FROM receiver_emails").fetchone()[0]
            print(f"[DEBUG] Total entries in receiver_emails: {total}")
        except Exception as e:
            print(f"[ERROR] Failed to fetch count from receiver_emails: {e}")
            return {}

        stats = {}

        # Total emails
        try:
            result = conn.execute("SELECT COUNT(*) FROM receiver_emails").fetchone()
            stats['total_emails'] = result[0]
            print(f"[DEBUG] Total emails: {stats['total_emails']}")
        except Exception as e:
            print(f"[ERROR] Total emails query failed: {e}")

        # Emails by folder
        try:
            result = conn.execute("""
                SELECT folder, COUNT(*) as count
                FROM receiver_emails
                GROUP BY folder
                ORDER BY count DESC
            """).fetchall()
            stats['emails_by_folder'] = [{"folder": row[0], "count": row[1]} for row in result]
            print(f"[DEBUG] Emails by folder: {stats['emails_by_folder']}")
        except Exception as e:
            print(f"[ERROR] Emails by folder query failed: {e}")

        # Emails by year
        try:
            result = conn.execute("""
                SELECT strftime('%Y', timestamp) AS year, COUNT(*) AS count
                FROM receiver_emails
                GROUP BY year
                ORDER BY year
            """).fetchall()
            stats['emails_by_year'] = [{"year": row[0], "count": row[1]} for row in result]
            print(f"[DEBUG] Emails by year: {stats['emails_by_year']}")
        except Exception as e:
            print(f"[ERROR] Emails by year query failed: {e}")

        # Top senders
        try:
            result = conn.execute("""
                SELECT e.name AS "from", COUNT(*) AS count
                FROM receiver_emails re
                JOIN entities e ON re.sender_id = e.id
                GROUP BY e.name
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            stats['top_senders'] = [{"from": row[0], "count": row[1]} for row in result]
            print(f"[DEBUG] Top senders: {stats['top_senders']}")
        except Exception as e:
            print(f"[ERROR] Top senders query failed: {e}")

        # Emails with attachments
        try:
            result = conn.execute("""
                SELECT COUNT(DISTINCT email_id)
                FROM attachments
            """).fetchone()
            stats['emails_with_attachments'] = result[0]
            print(f"[DEBUG] Emails with attachments: {stats['emails_with_attachments']}")
        except Exception as e:
            print(f"[ERROR] Attachments query failed: {e}")

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
                body AS content
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
                SELECT re.message_id, re.subject, re.mailbox_name, re.direction,
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
                ORDER BY re.timestamp DESC
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

    def get_comprehensive_email_dataset_agg_recipients(self, limit=None):
        """
        Get a comprehensive dataset combining relevant information from all tables.
        This creates a single dataframe with emails and all their associated metadata.

        Args:
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with comprehensive email data
        """
        conn = self.connect()

        query = """
        SELECT
            -- Email core data
            re.id AS email_id,
            re.message_id,
            re.mailbox_name,
            re.direction,
            re.timestamp,
            re.subject,
            re.body,
            re.folder,
            re.is_deleted,
            re.is_spam,
            re.importance_score,
            re.in_reply_to,
            re."references",

            -- Sender information
            sender.id AS sender_id,
            sender.name AS sender_name,
            sender.email AS sender_email,
            sender.is_physical_person AS sender_is_person,

            -- Reply-to information
            reply_to.id AS reply_to_id,
            reply_to.name AS reply_to_name,
            reply_to.email AS reply_to_email,

            -- Recipients (aggregated)
            (SELECT string_agg(e.name, ', ')
            FROM email_recipients_to ert
            JOIN entities e ON ert.entity_id = e.id
            WHERE ert.email_id = re.id) AS to_recipients,

            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_to ert
            JOIN entities e ON ert.entity_id = e.id
            WHERE ert.email_id = re.id) AS to_emails,

            (SELECT string_agg(e.name, ', ')
            FROM email_recipients_cc ercc
            JOIN entities e ON ercc.entity_id = e.id
            WHERE ercc.email_id = re.id) AS cc_recipients,

            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_cc ercc
            JOIN entities e ON ercc.entity_id = e.id
            WHERE ercc.email_id = re.id) AS cc_emails,

            (SELECT string_agg(e.name, ', ')
            FROM email_recipients_bcc erbcc
            JOIN entities e ON erbcc.entity_id = e.id
            WHERE erbcc.email_id = re.id) AS bcc_recipients,

            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_bcc erbcc
            JOIN entities e ON erbcc.entity_id = e.id
            WHERE erbcc.email_id = re.id) AS bcc_emails,

            -- Mailing list information
            ml.id AS mailing_list_id,
            ml.name AS mailing_list_name,
            ml.email_address AS mailing_list_email,

            -- Attachment information (counts and aggregate info)
            (SELECT COUNT(*) FROM attachments a WHERE a.email_id = re.id) AS attachment_count,
            (SELECT string_agg(a.filename, ', ') FROM attachments a WHERE a.email_id = re.id) AS attachment_filenames,
            (SELECT SUM(a.size) FROM attachments a WHERE a.email_id = re.id) AS total_attachment_size,

            -- Thread information
            (SELECT COUNT(*) FROM email_children ec WHERE ec.parent_id = re.id) AS child_email_count,
            re.mother_email_id
        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        LEFT JOIN
            entities reply_to ON re.reply_to_id = reply_to.id
        LEFT JOIN
            mailing_lists ml ON re.mailing_list_id = ml.id
        ORDER BY
            re.timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        # Execute the query and convert to DataFrame
        df = conn.execute(query).df()

        # Convert timestamps to proper datetime format
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        return df

    def get_comprehensive_email_dataset(self, limit=None):
        """
        Get a comprehensive dataset with emails and their recipients,
        creating one row per recipient rather than aggregating.

        Args:
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with comprehensive email data and one row per recipient
        """
        conn = self.connect()

        # First get the core email data without recipient aggregation
        core_query = """
        SELECT
            -- Email core data
            re.id AS email_id,
            re.message_id,
            re.mailbox_name,
            re.direction,
            re.timestamp,
            re.subject,
            re.body,
            re.folder,
            re.is_deleted,
            re.is_spam,
            re.importance_score,
            re.in_reply_to,
            re."references",

            -- Sender information
            sender.id AS sender_id,
            sender.name AS sender_name,
            sender.email AS sender_email,
            sender.is_physical_person AS sender_is_person,

            -- Reply-to information
            reply_to.id AS reply_to_id,
            reply_to.name AS reply_to_name,
            reply_to.email AS reply_to_email,

            -- Mailing list information
            ml.id AS mailing_list_id,
            ml.name AS mailing_list_name,
            ml.email_address AS mailing_list_email,

            -- Attachment information (counts and aggregate info)
            (SELECT COUNT(*) FROM attachments a WHERE a.email_id = re.id) AS attachment_count,
            (SELECT string_agg(a.filename, ', ') FROM attachments a WHERE a.email_id = re.id) AS attachment_filenames,
            (SELECT SUM(a.size) FROM attachments a WHERE a.email_id = re.id) AS total_attachment_size,

            -- Thread information
            (SELECT COUNT(*) FROM email_children ec WHERE ec.parent_id = re.id) AS child_email_count,
            re.mother_email_id
        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        LEFT JOIN
            entities reply_to ON re.reply_to_id = reply_to.id
        LEFT JOIN
            mailing_lists ml ON re.mailing_list_id = ml.id
        ORDER BY
            re.timestamp DESC
        """

        if limit:
            core_query += f" LIMIT {limit}"

        # Get the core data first
        core_df = conn.execute(core_query).df()

        # Now get "to" recipients as separate rows
        to_query = """
        SELECT
            re.id AS email_id,
            e.id AS entity_id,
            e.name AS recipient_name,
            e.email AS recipient_email,
            'to' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_to ert ON re.id = ert.email_id
        JOIN
            entities e ON ert.entity_id = e.id
        """

        if limit:
            to_query += f" WHERE re.id IN (SELECT id FROM receiver_emails LIMIT {limit})"

        to_df = conn.execute(to_query).df()

        # Get CC recipients
        cc_query = """
        SELECT
            re.id AS email_id,
            e.id AS entity_id,
            e.name AS recipient_name,
            e.email AS recipient_email,
            'cc' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_cc ercc ON re.id = ercc.email_id
        JOIN
            entities e ON ercc.entity_id = e.id
        """

        if limit:
            cc_query += f" WHERE re.id IN (SELECT id FROM receiver_emails LIMIT {limit})"

        cc_df = conn.execute(cc_query).df()

        # Get BCC recipients
        bcc_query = """
        SELECT
            re.id AS email_id,
            e.id AS entity_id,
            e.name AS recipient_name,
            e.email AS recipient_email,
            'bcc' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_bcc erbcc ON re.id = erbcc.email_id
        JOIN
            entities e ON erbcc.entity_id = e.id
        """

        if limit:
            bcc_query += f" WHERE re.id IN (SELECT id FROM receiver_emails LIMIT {limit})"

        bcc_df = conn.execute(bcc_query).df()

        # Combine all recipients
        all_recipients = pd.concat([to_df, cc_df, bcc_df])

        # Merge core data with recipients to get one row per recipient
        merged_df = pd.merge(
            core_df,
            all_recipients,
            on='email_id',
            how='inner'
        )

        # Convert timestamps to proper datetime format
        if 'timestamp' in merged_df.columns and not pd.api.types.is_datetime64_any_dtype(merged_df['timestamp']):
            merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'], errors='coerce')

        return merged_df

    def get_app_DataFrame(self, mailbox=None, limit=None):
        """
        Get a dataframe with specific columns needed for the application,
        creating one row per recipient rather than one per email.

        Args:
            mailbox: Optional filter for specific mailbox
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with columns: message_id, date, from, recipient_email,
            recipient_type, subject, body, attachments, has_attachments,
            direction, mailbox
        """
        conn = self.connect()

        # Get core email data first
        core_query = """
        SELECT
            re.id AS email_id,
            re.message_id,
            re.timestamp AS date,
            re.mailbox_name,
            re.direction,
            sender.email AS "from",
            re.subject,
            re.body,
            (SELECT string_agg(a.filename, '|')
            FROM attachments a
            WHERE a.email_id = re.id) AS attachments,
            (SELECT COUNT(*) > 0
            FROM attachments a
            WHERE a.email_id = re.id) AS has_attachments,
            re.folder AS mailbox
        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        """

        # Add mailbox filter if specified
        if mailbox:
            core_query += f" WHERE re.folder = '{mailbox}'"
        
        # Add ORDER BY to sort by date descending (newest first)
        core_query += " ORDER BY re.timestamp DESC"

        # Add limit if specified
        if limit:
            core_query += f" LIMIT {limit}"

        # Execute the core query and convert to DataFrame
        core_df = conn.execute(core_query).df()

        # Now get "to" recipients as separate rows
        to_query = """
        SELECT
            re.id AS email_id,
            e.email AS recipient_email,
            'to' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_to ert ON re.id = ert.email_id
        JOIN
            entities e ON ert.entity_id = e.id
        """

        if mailbox:
            to_query += f" WHERE re.folder = '{mailbox}'"

        if limit:
            limit_clause = f" re.id IN (SELECT id FROM receiver_emails"
            if mailbox:
                limit_clause += f" WHERE folder = '{mailbox}'"
            limit_clause += f" LIMIT {limit})"

            if mailbox:
                to_query += f" AND {limit_clause}"
            else:
                to_query += f" WHERE {limit_clause}"

        to_df = conn.execute(to_query).df()

        # Get CC recipients
        cc_query = """
        SELECT
            re.id AS email_id,
            e.email AS recipient_email,
            'cc' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_cc ercc ON re.id = ercc.email_id
        JOIN
            entities e ON ercc.entity_id = e.id
        """

        if mailbox:
            cc_query += f" WHERE re.folder = '{mailbox}'"

        if limit:
            limit_clause = f" re.id IN (SELECT id FROM receiver_emails"
            if mailbox:
                limit_clause += f" WHERE folder = '{mailbox}'"
            limit_clause += f" LIMIT {limit})"

            if mailbox:
                cc_query += f" AND {limit_clause}"
            else:
                cc_query += f" WHERE {limit_clause}"

        cc_df = conn.execute(cc_query).df()

        # Get BCC recipients
        bcc_query = """
        SELECT
            re.id AS email_id,
            e.email AS recipient_email,
            'bcc' AS recipient_type
        FROM
            receiver_emails re
        JOIN
            email_recipients_bcc erbcc ON re.id = erbcc.email_id
        JOIN
            entities e ON erbcc.entity_id = e.id
        """

        if mailbox:
            bcc_query += f" WHERE re.folder = '{mailbox}'"

        if limit:
            limit_clause = f" re.id IN (SELECT id FROM receiver_emails"
            if mailbox:
                limit_clause += f" WHERE folder = '{mailbox}'"
            limit_clause += f" LIMIT {limit})"

            if mailbox:
                bcc_query += f" AND {limit_clause}"
            else:
                bcc_query += f" WHERE {limit_clause}"

        bcc_df = conn.execute(bcc_query).df()

        # Combine all recipients
        all_recipients = pd.concat([to_df, cc_df, bcc_df])

        # Merge core data with recipients to get one row per recipient
        merged_df = pd.merge(
            core_df,
            all_recipients,
            on='email_id',
            how='inner'
        )

        # Drop the email_id column as it was just used for merging
        if 'email_id' in merged_df.columns:
            merged_df = merged_df.drop('email_id', axis=1)

        # Convert timestamps to proper datetime format
        if 'date' in merged_df.columns and not pd.api.types.is_datetime64_any_dtype(merged_df['date']):
            merged_df['date'] = pd.to_datetime(merged_df['date'], errors='coerce')

        # Convert attachments to a list format if needed
        if 'attachments' in merged_df.columns:
            merged_df['attachments'] = merged_df['attachments'].apply(
                lambda x: x.split('|') if isinstance(x, str) and x else []
            )

        print(merged_df.columns)
        return merged_df


    def get_app_dataframe_agg_recipients(self, mailbox=None, limit=None):
        """
        Get a dataframe with specific columns needed for the application,
        creating one row per email with aggregated recipient information.

        This method is an alternative to get_app_DataFrame that provides
        aggregated recipient data instead of one row per recipient.

        Args:
            mailbox: Optional filter for specific mailbox
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with columns compatible with app expectations:
            message_id, date, from, recipient_email, subject, body, attachments,
            has_attachments, direction, mailbox
        """
        conn = self.connect()

        query = """
        SELECT
            re.message_id,
            re.timestamp AS date,
            sender.email AS "from",
            -- Aggregate all recipients into a single string
            COALESCE(
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_to ert
                 JOIN entities e ON ert.entity_id = e.id
                 WHERE ert.email_id = re.id), ''
            ) ||
            CASE WHEN
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_to ert
                 JOIN entities e ON ert.entity_id = e.id
                 WHERE ert.email_id = re.id) IS NOT NULL AND
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_cc ercc
                 JOIN entities e ON ercc.entity_id = e.id
                 WHERE ercc.email_id = re.id) IS NOT NULL
            THEN ', ' ELSE '' END ||
            COALESCE(
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_cc ercc
                 JOIN entities e ON ercc.entity_id = e.id
                 WHERE ercc.email_id = re.id), ''
            ) AS recipient_email,
            re.subject,
            re.body,
            (SELECT string_agg(a.filename, '|')
             FROM attachments a
             WHERE a.email_id = re.id) AS attachments,
            (SELECT COUNT(*) > 0
             FROM attachments a
             WHERE a.email_id = re.id) AS has_attachments,
            re.direction,
            COALESCE(re.mailbox_name, re.folder) AS mailbox,
            re.mailbox_name
        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        """

        # Add mailbox filter if specified
        if mailbox:
            query += f" WHERE COALESCE(re.mailbox_name, re.folder) = '{mailbox}'"
        
        # Add ORDER BY to sort by date descending (newest first)
        query += " ORDER BY re.timestamp DESC"

        # Add limit if specified
        if limit:
            query += f" LIMIT {limit}"

        # Execute the query and convert to DataFrame
        df = conn.execute(query).df()

        # Convert timestamps to proper datetime format
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Convert attachments to a list format if needed
        if 'attachments' in df.columns:
            df['attachments'] = df['attachments'].apply(
                lambda x: x.split('|') if isinstance(x, str) and x else []
            )

        # Clean up recipient_email field to remove empty values
        if 'recipient_email' in df.columns:
            df['recipient_email'] = df['recipient_email'].apply(
                lambda x: x.strip(', ') if isinstance(x, str) else x
            )

        return df

    def get_app_dataframe_with_filters(self, mailbox=None, filters=None, limit=None):
        """
        Get a dataframe with specific columns needed for the application,
        with support for additional filters including mailing lists.

        Args:
            mailbox: Optional filter for specific mailbox
            filters: Dictionary containing filter criteria
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with columns compatible with app expectations
        """
        conn = self.connect()

        # Base query with all necessary joins
        query = """
        SELECT
            re.message_id,
            re.timestamp AS date,
            sender.email AS "from",
            -- Aggregate all recipients into a single string
            COALESCE(
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_to ert
                 JOIN entities e ON ert.entity_id = e.id
                 WHERE ert.email_id = re.id), ''
            ) ||
            CASE WHEN
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_to ert
                 JOIN entities e ON ert.entity_id = e.id
                 WHERE ert.email_id = re.id) IS NOT NULL AND
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_cc ercc
                 JOIN entities e ON ercc.entity_id = e.id
                 WHERE ercc.email_id = re.id) IS NOT NULL
            THEN ', ' ELSE '' END ||
            COALESCE(
                (SELECT string_agg(e.email, ', ')
                 FROM email_recipients_cc ercc
                 JOIN entities e ON ercc.entity_id = e.id
                 WHERE ercc.email_id = re.id), ''
            ) AS recipient_email,
            re.subject,
            re.body,
            (SELECT string_agg(a.filename, '|')
             FROM attachments a
             WHERE a.email_id = re.id) AS attachments,
            (SELECT COUNT(*) > 0
             FROM attachments a
             WHERE a.email_id = re.id) AS has_attachments,
            re.direction,
            COALESCE(re.mailbox_name, re.folder) AS mailbox,
            re.mailbox_name,
            ml.email_address AS mailing_list_email
        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        LEFT JOIN
            mailing_lists ml ON re.mailing_list_id = ml.id
        WHERE 1=1
        """

        # Add filters
        filter_conditions = []

        # Mailbox filter
        if mailbox and mailbox != "All Mailboxes":
            filter_conditions.append(f"COALESCE(re.mailbox_name, re.folder) = '{mailbox}'")

        # Additional filters
        if filters:
            # Mailing list filter
            mailing_list_value = filters.get('mailing_list_email')
            if mailing_list_value:
                if mailing_list_value == 'None':
                    filter_conditions.append("ml.email_address IS NULL")
                elif mailing_list_value != 'All':
                    filter_conditions.append(f"ml.email_address = '{mailing_list_value}'")

            # Direction filter
            direction_value = filters.get('direction')
            if direction_value:
                direction_str = str(direction_value)
                normalized_direction = direction_str.strip().casefold()
                # Treat "All"/"Tous" (and similar) as no filter
                if normalized_direction not in {'all', 'tous', 'toutes'}:
                    if normalized_direction in {'envoyé', 'envoyes', 'envoyés', 'envoye', 'sent'}:
                        resolved_direction = 'sent'
                    elif normalized_direction in {'reçu', 'reçus', 'recus', 'recu', 'received'}:
                        resolved_direction = 'received'
                    else:
                        resolved_direction = direction_str  # fall back to raw value
                    filter_conditions.append(f"re.direction = '{resolved_direction}'")

            # Folder filter (additional to mailbox)
            folder_value = filters.get('folder')
            if folder_value and folder_value != 'All':
                filter_conditions.append(f"COALESCE(re.mailbox_name, re.folder) = '{folder_value}'")

        # Add filter conditions to query
        if filter_conditions:
            query += " AND " + " AND ".join(filter_conditions)
        
        # Add ORDER BY to sort by date descending (newest first)
        query += " ORDER BY re.timestamp DESC"

        # Add limit if specified
        if limit:
            query += f" LIMIT {limit}"

        # Execute the query and convert to DataFrame
        df = conn.execute(query).df()

        # Convert timestamps to proper datetime format
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Convert attachments to a list format if needed
        if 'attachments' in df.columns:
            df['attachments'] = df['attachments'].apply(
                lambda x: x.split('|') if isinstance(x, str) and x else []
            )

        # Clean up recipient_email field to remove empty values
        if 'recipient_email' in df.columns:
            df['recipient_email'] = df['recipient_email'].apply(
                lambda x: x.strip(', ') if isinstance(x, str) else x
            )

        return df

    def get_rag_email_dataset(self, limit=None):
        """
        Get a simplified dataset optimized for RAG indexing.
        Returns one row per email with aggregated recipient information.

        Args:
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with columns: email_id, from, to_recipients, cc_recipients,
            bcc_recipients, date, subject, body
        """
        conn = self.connect()

        query = """
        SELECT
            -- Email core data
            re.id AS email_id,
            re.timestamp AS date,
            re.subject,
            re.body,

            -- Sender information
            sender.email AS "from",

            -- Recipients (aggregated)
            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_to ert
            JOIN entities e ON ert.entity_id = e.id
            WHERE ert.email_id = re.id) AS to_recipients,

            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_cc ercc
            JOIN entities e ON ercc.entity_id = e.id
            WHERE ercc.email_id = re.id) AS cc_recipients,

            (SELECT string_agg(e.email, ', ')
            FROM email_recipients_bcc erbcc
            JOIN entities e ON erbcc.entity_id = e.id
            WHERE erbcc.email_id = re.id) AS bcc_recipients

        FROM
            receiver_emails re
        LEFT JOIN
            entities sender ON re.sender_id = sender.id
        ORDER BY
            re.timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        # Execute the query and convert to DataFrame
        df = conn.execute(query).df()

        # Convert timestamps to proper datetime format
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Clean up None values in recipient fields
        recipient_columns = ['to_recipients', 'cc_recipients', 'bcc_recipients']
        for col in recipient_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')

        return df

    def get_receiver_emails(self, limit=None):
        """
        Get a DataFrame with receiver emails.

        Args:
            limit: Optional limit on the number of rows returned

        Returns:
            pandas DataFrame with receiver emails
        """
        conn = self.connect()

        query = """
        SELECT *
        FROM
            receiver_emails
        ORDER BY
            timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        df = conn.execute(query).df()

        return df


if __name__ == "__main__":

    email_analyzer = EmailAnalyzer(db_path="data/Projects/database.duckdb")

    # Get first 1000 emails with comprehensive data
    df = email_analyzer.get_comprehensive_email_dataset(limit=10)
    print(df.shape[0], "emails retrieved")
    print(df.columns)
    print(df.head(1))
