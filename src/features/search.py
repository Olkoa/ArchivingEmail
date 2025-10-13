"""
Elasticsearch integration for the Olkoa project.

This module provides functions for indexing email data in Elasticsearch
and performing advanced searches.
"""

import os
import pandas as pd
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import re

# Default Elasticsearch settings
ES_HOST = os.environ.get('ES_HOST', 'localhost')
ES_PORT = int(os.environ.get('ES_PORT', 9200))
ES_INDEX = os.environ.get('ES_INDEX', 'olkoa-emails')

class ESSearchEngine:
    """Elasticsearch search engine for email data."""
    
    def __init__(
        self, 
        host: str = ES_HOST, 
        port: int = ES_PORT, 
        index_name: str = ES_INDEX,
        use_mock: bool = False
    ):
        """
        Initialize the Elasticsearch search engine.
        
        Args:
            host: Elasticsearch host
            port: Elasticsearch port
            index_name: Name of the Elasticsearch index
            use_mock: Whether to use a mock implementation (for testing without ES)
        """
        self.index_name = index_name
        self.use_mock = use_mock
        
        if not use_mock:
            try:
                self.es = Elasticsearch([f'http://{host}:{port}'])
                self.available = self.es.ping()
                if not self.available:
                    print(f"Warning: Elasticsearch at {host}:{port} is not available.")
            except Exception as e:
                print(f"Error connecting to Elasticsearch: {e}")
                self.available = False
        else:
            self.available = True
            self.mock_data = []
    
    def create_index(self) -> bool:
        """
        Create the Elasticsearch index with appropriate mappings.
        
        Returns:
            True if successful, False otherwise
        """
        if self.use_mock:
            return True
            
        if not self.available:
            return False
        
        # Check if index already exists
        if self.es.indices.exists(index=self.index_name):
            return True
        
        # Define index mappings for email data
        mappings = {
            "mappings": {
                "properties": {
                    "message_id": {"type": "keyword"},
                    "date": {"type": "date"},
                    "from": {"type": "keyword"},
                    "from_name": {"type": "text"},
                    "to": {"type": "keyword"},
                    "to_name": {"type": "text"},
                    "cc": {"type": "keyword"},
                    "subject": {"type": "text", "analyzer": "french"},
                    "body": {"type": "text", "analyzer": "french"},
                    "attachments": {"type": "keyword"},
                    "has_attachments": {"type": "boolean"},
                    "direction": {"type": "keyword"},
                    "mailbox": {"type": "keyword"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "french": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "french_stop", "french_stemmer"]
                        }
                    },
                    "filter": {
                        "french_stop": {
                            "type": "stop",
                            "stopwords": "_french_"
                        },
                        "french_stemmer": {
                            "type": "stemmer",
                            "language": "french"
                        }
                    }
                }
            }
        }
        
        try:
            self.es.indices.create(index=self.index_name, body=mappings)
            return True
        except elasticsearch.exceptions.RequestError:
            print(f"Index {self.index_name} already exists.")
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    def extract_name(self, addr_str: str) -> str:
        """Extract name from an email address string."""
        if not addr_str:
            return ""
        
        # Check if it's in "Name <email>" format
        match = re.search(r'^([^<]+)<[^>]+>$', addr_str.strip())
        if match:
            return match.group(1).strip()
        
        # Otherwise, use the email part before @
        match = re.search(r'([^@]+)@', addr_str)
        if match:
            # Convert email usernames like "john.doe" to "John Doe"
            name = match.group(1).replace('.', ' ').replace('_', ' ')
            return ' '.join(word.capitalize() for word in name.split())
            
        return addr_str
    
    def _prepare_document(self, row: pd.Series) -> Dict[str, Any]:
        """
        Prepare a document for Elasticsearch indexing.
        
        Args:
            row: Pandas Series containing email data
            
        Returns:
            Document dictionary
        """
        # Extract names from email addresses
        from_name = self.extract_name(row.get('from', ''))
        
        # Handle multiple recipients in 'to' field
        to_addresses = row.get('to', '').split(';')
        to_names = [self.extract_name(addr) for addr in to_addresses if addr.strip()]
        
        # Prepare the document
        doc = {
            "message_id": row.get('message_id', ''),
            "date": row.get('date'),
            "from": row.get('from', ''),
            "from_name": from_name,
            "to": row.get('to', ''),
            "to_name": ", ".join(to_names),
            "cc": row.get('cc', ''),
            "subject": row.get('subject', ''),
            "body": row.get('body', ''),
            "attachments": row.get('attachments', ''),
            "has_attachments": row.get('has_attachments', False),
            "direction": row.get('direction', ''),
            "mailbox": row.get('mailbox', '')
        }
        
        return doc
    
    def index_emails(self, df: pd.DataFrame) -> int:
        """
        Index email data in Elasticsearch.
        
        Args:
            df: DataFrame containing email data
            
        Returns:
            Number of documents indexed
        """
        if self.use_mock:
            # Store the DataFrame in memory for mock search
            self.mock_data = df.to_dict('records')
            return len(self.mock_data)
            
        if not self.available:
            return 0
        
        # Ensure index exists
        if not self.create_index():
            return 0
        
        # Prepare documents for bulk indexing
        actions = []
        for _, row in df.iterrows():
            doc = self._prepare_document(row)
            
            action = {
                "_index": self.index_name,
                "_id": doc["message_id"] or f"id_{len(actions)}",
                "_source": doc
            }
            
            actions.append(action)
        
        # Perform bulk indexing
        if actions:
            try:
                success, failed = bulk(self.es, actions, refresh=True)
                return success
            except Exception as e:
                print(f"Error during bulk indexing: {e}")
                return 0
        
        return 0
    
    def _mock_search(
        self, 
        query: str, 
        filters: Dict[str, Any] = None, 
        date_range: Dict[str, datetime] = None,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Perform a mock search for testing without Elasticsearch.
        
        Args:
            query: Search query
            filters: Dictionary of field filters
            date_range: Dictionary with 'start' and 'end' datetime objects
            size: Maximum number of results to return
            
        Returns:
            Dictionary with 'hits' and 'total' fields
        """
        # Simple mock search implementation
        results = []
        query = query.lower()
        
        for doc in self.mock_data:
            # Check if query matches any field
            matches = False
            if query:
                for field in ['subject', 'body', 'from', 'to']:
                    if field in doc and query in str(doc[field]).lower():
                        matches = True
                        break
            else:
                matches = True
            
            # Apply filters
            if matches and filters:
                for field, value in filters.items():
                    if field in doc and doc[field] != value:
                        matches = False
                        break
            
            # Apply date range
            if matches and date_range:
                if 'date' in doc and doc['date']:
                    doc_date = doc['date']
                    if isinstance(doc_date, str):
                        try:
                            doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                        except ValueError:
                            matches = False
                    
                    if matches and date_range.get('start') and doc_date < date_range['start']:
                        matches = False
                    if matches and date_range.get('end') and doc_date > date_range['end']:
                        matches = False
            
            if matches:
                results.append({
                    "_id": doc.get("message_id", ""),
                    "_source": doc
                })
                if len(results) >= size:
                    break
        
        return {
            "hits": {
                "total": {"value": len(results)},
                "hits": results
            }
        }
    
    def search(
        self, 
        query: str, 
        filters: Dict[str, Any] = None, 
        date_range: Dict[str, datetime] = None,
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for emails in Elasticsearch.
        
        Args:
            query: Search query
            filters: Dictionary of field filters
            date_range: Dictionary with 'start' and 'end' datetime objects
            size: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        if self.use_mock:
            return self._mock_search(query, filters, date_range, size)
            
        if not self.available:
            return {"hits": {"total": {"value": 0}, "hits": []}}
        
        # Build Elasticsearch query
        es_query = {
            "query": {
                "bool": {
                    "must": []
                }
            },
            "size": size,
            "sort": [{"date": {"order": "desc"}}]
        }
        
        # Add text search if query is provided
        if query:
            es_query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": ["subject^2", "body", "from_name", "to_name"],
                    "operator": "and",
                }
            })
        
        # Add filters
        if filters:
            for field, value in filters.items():
                if value:
                    if isinstance(value, list):
                        es_query["query"]["bool"]["must"].append({
                            "terms": {field: value}
                        })
                    else:
                        es_query["query"]["bool"]["must"].append({
                            "term": {field: value}
                        })
        
        # Add date range filter
        if date_range:
            date_filter = {"range": {"date": {}}}
            if date_range.get('start'):
                date_filter["range"]["date"]["gte"] = date_range['start'].isoformat()
            if date_range.get('end'):
                date_filter["range"]["date"]["lte"] = date_range['end'].isoformat()
            
            es_query["query"]["bool"]["must"].append(date_filter)
        
        # Execute search
        try:
            results = self.es.search(index=self.index_name, body=es_query)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return {"hits": {"total": {"value": 0}, "hits": []}}
    
    def get_unique_values(self, field: str) -> List[str]:
        """
        Get unique values for a field.
        
        Args:
            field: Field name
            
        Returns:
            List of unique values
        """
        if self.use_mock:
            # Get unique values from mock data
            values = set()
            for doc in self.mock_data:
                if field in doc and doc[field]:
                    if isinstance(doc[field], str) and ';' in doc[field]:
                        for value in doc[field].split(';'):
                            values.add(value.strip())
                    else:
                        values.add(doc[field])
            return sorted(list(values))
            
        if not self.available:
            return []
        
        # Use Elasticsearch aggregation to get unique values
        agg_query = {
            "size": 0,
            "aggs": {
                "unique_values": {
                    "terms": {
                        "field": field,
                        "size": 100  # Limit to 100 unique values
                    }
                }
            }
        }
        
        try:
            results = self.es.search(index=self.index_name, body=agg_query)
            buckets = results['aggregations']['unique_values']['buckets']
            return [bucket['key'] for bucket in buckets]
        except Exception as e:
            print(f"Error retrieving unique values: {e}")
            return []


def format_search_results(results: Dict[str, Any]) -> pd.DataFrame:
    """
    Format Elasticsearch search results as a pandas DataFrame.
    
    Args:
        results: Elasticsearch search results
        
    Returns:
        DataFrame containing formatted results
    """
    # Extract hits
    hits = results.get('hits', {}).get('hits', [])
    
    # Convert to list of dictionaries
    records = []
    for hit in hits:
        source = hit.get('_source', {})
        records.append(source)
    
    # Convert to DataFrame
    if records:
        df = pd.DataFrame(records)
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        return df
    
    # Return empty DataFrame with expected columns
    return pd.DataFrame(columns=[
        "message_id", "date", "from", "from_name", "to", "to_name", 
        "cc", "subject", "body", "attachments", "has_attachments", 
        "direction", "mailbox"
    ])


def search_emails(
    df: pd.DataFrame,
    query: str = "",
    filters: Dict[str, Any] = None,
    date_range: Dict[str, datetime] = None,
    size: int = 100
) -> pd.DataFrame:
    """
    Search emails in the DataFrame using Elasticsearch-like functionality.
    
    Args:
        df: DataFrame containing email data
        query: Search query
        filters: Dictionary of field filters
        date_range: Dictionary with 'start' and 'end' datetime objects
        size: Maximum number of results to return
        
    Returns:
        DataFrame containing search results
    """
    # Try to use Elasticsearch if available
    try:
        es = ESSearchEngine(use_mock=True)  # Start with mock mode
        
        # Index the emails
        es.index_emails(df)
        
        # Perform search
        results = es.search(query, filters, date_range, size)
        
        # Format results
        return format_search_results(results)
    
    except Exception as e:
        print(f"Error using search engine: {e}")
        # Fallback to basic filtering
        return basic_search(df, query, filters, date_range, size)


def basic_search(
    df: pd.DataFrame,
    query: str = "",
    filters: Dict[str, Any] = None,
    date_range: Dict[str, datetime] = None,
    size: int = 100
) -> pd.DataFrame:
    """
    Basic search implementation using pandas filtering.
    
    Args:
        df: DataFrame containing email data
        query: Search query
        filters: Dictionary of field filters
        date_range: Dictionary with 'start' and 'end' datetime objects
        size: Maximum number of results to return
        
    Returns:
        DataFrame containing search results
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Apply text search if query is provided
    if query:
        query = query.lower()
        mask = (
            result_df['subject'].str.lower().str.contains(query, na=False) |
            result_df['body'].str.lower().str.contains(query, na=False) |
            result_df['from'].str.lower().str.contains(query, na=False) |
            result_df['to'].str.lower().str.contains(query, na=False)
        )
        result_df = result_df[mask]
    
    # Apply field filters
    if filters:
        for field, value in filters.items():
            if value and field in result_df.columns:
                if isinstance(value, list):
                    mask = result_df[field].isin(value)
                else:
                    mask = result_df[field] == value
                result_df = result_df[mask]
    
    # Apply date range filter
    if date_range:
        if 'date' in result_df.columns:
            if date_range.get('start'):
                result_df = result_df[result_df['date'] >= date_range['start']]
            if date_range.get('end'):
                result_df = result_df[result_df['date'] <= date_range['end']]
    
    # Sort by date (descending)
    if 'date' in result_df.columns:
        result_df = result_df.sort_values('date', ascending=False)
    
    # Limit results
    if len(result_df) > size:
        result_df = result_df.iloc[:size]
    
    return result_df


if __name__ == "__main__":
    # Test code for search functionality
    import pandas as pd
    from src.data.loading import load_mailboxes
    import os
    
    # Load sample data
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    base_dir = os.path.join(project_root, 'data', 'raw')
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)
    
    # Test search
    results = search_emails(emails_df, query="meeting")
    print(f"Found {len(results)} results for 'meeting'")
    print(results[['date', 'from', 'subject']].head())
