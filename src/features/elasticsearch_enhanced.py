"""
Enhanced Elasticsearch integration for the Okloa project.

This module extends the existing Elasticsearch functionality with more advanced
search capabilities, including different search modes and configurable fuzziness.
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

# Import original search functionality
from .search import ESSearchEngine, format_search_results, basic_search

# Default Elasticsearch settings
ES_HOST = os.environ.get('ES_HOST', 'localhost')
ES_PORT = int(os.environ.get('ES_PORT', 9200))
ES_INDEX = os.environ.get('ES_INDEX', 'okloa-emails')

class EnhancedESSearchEngine(ESSearchEngine):
    """Enhanced Elasticsearch search engine for email data."""
    
    def search(
        self, 
        query: str,
        search_mode: str = "all", 
        fields: List[str] = None,
        filters: Dict[str, Any] = None, 
        date_range: Dict[str, datetime] = None,
        fuzziness: Union[str, int] = 'AUTO',
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Enhanced search for emails with different modes and fuzziness.
        
        Args:
            query: Search query
            search_mode: Search mode ('all', 'content_and_title', 'title_only', 'content_only', 'advanced')
            fields: List of fields to search in (used only when search_mode is 'advanced')
            filters: Dictionary of field filters
            date_range: Dictionary with 'start' and 'end' datetime objects
            fuzziness: Fuzziness level ('AUTO', 0, 1, 2)
            size: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        if self.use_mock:
            return self._mock_search_enhanced(query, search_mode, fields, filters, date_range, fuzziness, size)
            
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
        
        # Add text search based on search mode
        if query:
            search_fields = self._get_search_fields(search_mode, fields)
            
            if len(search_fields) > 1:
                es_query["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": search_fields,
                        "operator": "and",
                        "fuzziness": fuzziness
                    }
                })
            elif len(search_fields) == 1:
                es_query["query"]["bool"]["must"].append({
                    "match": {
                        search_fields[0]: {
                            "query": query,
                            "operator": "and",
                            "fuzziness": fuzziness
                        }
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
    
    def _get_search_fields(self, search_mode: str, fields: List[str] = None) -> List[str]:
        """
        Get the fields to search based on the search mode.
        
        Args:
            search_mode: Search mode ('all', 'content_and_title', 'title_only', 'content_only', 'advanced')
            fields: List of fields to search in (used only when search_mode is 'advanced')
            
        Returns:
            List of fields to search in
        """
        if search_mode == "all":
            return ["subject^2", "body", "from_name", "to_name", "from", "to"]
        elif search_mode == "content_and_title":
            return ["subject^2", "body"]
        elif search_mode == "title_only":
            return ["subject"]
        elif search_mode == "content_only":
            return ["body"]
        elif search_mode == "advanced" and fields:
            # Weight subject more heavily if it's included
            if "subject" in fields:
                fields = [f + "^2" if f == "subject" else f for f in fields]
            return fields
        else:
            # Default to all fields
            return ["subject^2", "body", "from_name", "to_name", "from", "to"]
    
    def _mock_search_enhanced(
        self, 
        query: str,
        search_mode: str = "all",
        fields: List[str] = None,
        filters: Dict[str, Any] = None, 
        date_range: Dict[str, datetime] = None,
        fuzziness: Union[str, int] = 'AUTO',
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Perform an enhanced mock search for testing without Elasticsearch.
        
        Args:
            query: Search query
            search_mode: Search mode ('all', 'content_and_title', 'title_only', 'content_only', 'advanced')
            fields: List of fields to search in (used only when search_mode is 'advanced')
            filters: Dictionary of field filters
            date_range: Dictionary with 'start' and 'end' datetime objects
            fuzziness: Fuzziness level ('AUTO', 0, 1, 2)
            size: Maximum number of results to return
            
        Returns:
            Dictionary with 'hits' and 'total' fields
        """
        # Get the fields to search based on search mode
        search_fields = self._get_search_fields(search_mode, fields)
        
        # Extract the field names without boosting (e.g., "subject^2" -> "subject")
        clean_fields = [field.split('^')[0] for field in search_fields]
        
        # Simple mock search implementation
        results = []
        query = query.lower()
        
        for doc in self.mock_data:
            # Check if query matches any of the specified fields
            matches = False
            if query:
                for field in clean_fields:
                    if field in doc and doc[field] and query in str(doc[field]).lower():
                        matches = True
                        break
            else:
                matches = True
            
            # Apply filters
            if matches and filters:
                for field, value in filters.items():
                    if field in doc:
                        if isinstance(value, list):
                            if doc[field] not in value:
                                matches = False
                                break
                        elif doc[field] != value:
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
                    "_source": doc,
                    "_score": 1.0  # Default score for mock results
                })
                if len(results) >= size:
                    break
        
        return {
            "hits": {
                "total": {"value": len(results)},
                "hits": results
            }
        }


def enhanced_search_emails(
    df: pd.DataFrame,
    query: str = "",
    search_mode: str = "all",
    fields: List[str] = None,
    filters: Dict[str, Any] = None,
    date_range: Dict[str, datetime] = None,
    fuzziness: Union[str, int] = 'AUTO',
    size: int = 100
) -> pd.DataFrame:
    """
    Enhanced search for emails in the DataFrame using Elasticsearch-like functionality.
    
    Args:
        df: DataFrame containing email data
        query: Search query
        search_mode: Search mode ('all', 'content_and_title', 'title_only', 'content_only', 'advanced')
        fields: List of fields to search in (used only when search_mode is 'advanced')
        filters: Dictionary of field filters
        date_range: Dictionary with 'start' and 'end' datetime objects
        fuzziness: Fuzziness level ('AUTO', 0, 1, 2)
        size: Maximum number of results to return
        
    Returns:
        DataFrame containing search results
    """
    # Try to use Elasticsearch if available
    try:
        es = EnhancedESSearchEngine(use_mock=True)  # Start with mock mode
        
        # Index the emails
        es.index_emails(df)
        
        # Perform search
        results = es.search(query, search_mode, fields, filters, date_range, fuzziness, size)
        
        # Format results
        result_df = format_search_results(results)
        
        # Add score column if not present
        if not result_df.empty and '_score' not in result_df.columns:
            result_df['_score'] = 1.0
        
        return result_df
    
    except Exception as e:
        print(f"Error using enhanced search engine: {e}")
        # Fallback to basic filtering
        return basic_search(df, query, filters, date_range, size)


if __name__ == "__main__":
    # Test code for enhanced search functionality
    import pandas as pd
    from src.data.loading import load_mailboxes
    import os
    
    # Load sample data
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    base_dir = os.path.join(project_root, 'data', 'raw')
    emails_df = load_mailboxes(["mailbox_1", "mailbox_2", "mailbox_3"], base_dir=base_dir)
    
    # Test all-fields search
    print("\nAll Fields Search:")
    results = enhanced_search_emails(emails_df, query="réunion", search_mode="all", fuzziness="AUTO")
    print(f"Found {len(results)} results for 'réunion' in all fields")
    if not results.empty:
        print(results[['date', 'from', 'subject']].head())
    
    # Test content and title search
    print("\nContent and Title Search:")
    results = enhanced_search_emails(emails_df, query="rapport", search_mode="content_and_title", fuzziness=1)
    print(f"Found {len(results)} results for 'rapport' in content and title")
    if not results.empty:
        print(results[['date', 'from', 'subject']].head())
    
    # Test title-only search
    print("\nTitle Only Search:")
    results = enhanced_search_emails(emails_df, query="budget", search_mode="title_only", fuzziness="AUTO")
    print(f"Found {len(results)} results for 'budget' in title only")
    if not results.empty:
        print(results[['date', 'from', 'subject']].head())
    
    # Test content-only search
    print("\nContent Only Search:")
    results = enhanced_search_emails(emails_df, query="archives", search_mode="content_only", fuzziness="AUTO")
    print(f"Found {len(results)} results for 'archives' in content only")
    if not results.empty:
        print(results[['date', 'from', 'subject']].head())
    
    # Test advanced search
    print("\nAdvanced Search:")
    results = enhanced_search_emails(
        emails_df,
        query="problem",
        search_mode="advanced",
        fields=["subject", "body"],
        filters={"direction": "received"},
        fuzziness="AUTO"
    )
    print(f"Found {len(results)} results for advanced search")
    if not results.empty:
        print(results[['date', 'from', 'subject']].head())
