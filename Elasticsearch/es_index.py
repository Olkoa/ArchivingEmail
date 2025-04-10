from elasticsearch import Elasticsearch
import json

def es_index(mail_json):
    # Connect to Elasticsearch
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
    
    # Specify the index name
    index_name = "emails"
    
    # Check if the index exists, create it if not
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
        print(f"Index '{index_name}' created.")
    
    # Load the emails from the JSON file (or use the `emails` list from the previous step)
    with open(mail_json, 'r', encoding='utf-8') as f:
        emails = json.load(f)
    
    # Index each email into Elasticsearch
    for i, email in enumerate(emails):
        response = es.index(index=index_name, id=i+1, document=email)
        print(f"Document indexed with ID: {i+1}")



    #mapping = {
 #   "properties": {
  #      "from": {"type": "keyword"},
   #     "to": {"type": "keyword"},
    #    "subject": {"type": "text"},
     #   "date": {"type": "date"},
      #  "body": {"type": "text"}
   # }
#}

# Create index with mapping
#es.indices.create(index=index_name, body={"mappings": mapping})


    return es,index_name