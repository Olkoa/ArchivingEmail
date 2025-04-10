from elasticsearch import Elasticsearch
from IPython.display import display

# Connect to Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Function to search Elasticsearch based on the query entered
def search_elasticsearch(query):
    # Define the search query
    search_query = {
        "query": {
            "match": {
                "body": query  # Search the 'body' field of the emails
            }
        }
    }

    # Execute the search
    search_response = es.search(index="emails", body=search_query)

    # Display the search results
    print(f"Search results for '{query}':")
    for hit in search_response['hits']['hits']:
        print(f"Subject: {hit['_source']['subject']}")
        print(f"From: {hit['_source']['from']}")
        print(f"Date: {hit['_source']['date']}")
        print(f"To: {hit['_source']['to']}")
        print(f"Body: {hit['_source']['body'][:200]}...")  # Show first 200 characters of body
        print("-" * 80)


# Function to search Elasticsearch based on the query entered
def search_elasticsearch_multi(query):
    # Define the search query with multi_match to search across multiple fields
    search_query = {
        "query": {
            "multi_match": {
                "query": query,  # The search term entered
                "fields": ["subject", "from", "body", "to", "date"],  # Fields to search across
                "fuzziness": "AUTO"  # Automatically calculate fuzziness based on the length of the word
            }
        }
    }

    # Execute the search
    search_response = es.search(index="emails", body=search_query)

    # Display the search results
    print(f"Search results for '{query}':")
    for hit in search_response['hits']['hits']:
        print(f"Subject: {hit['_source']['subject']}")
        print(f"From: {hit['_source']['from']}")
        print(f"Date: {hit['_source']['date']}")
        print(f"To: {hit['_source']['to']}")
        print(f"Body: {hit['_source']['body'][:200]}...")  # Show first 200 characters of body
        print("-" * 80)
