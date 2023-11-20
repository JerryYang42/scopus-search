import json
import requests
from typing import Tuple, List
import pandas as pd
from datetime import datetime

from JsonIO import VectorQueryJsonIO

class VectorSearchClient():

    ENDPOINT = "https://shared-search-service-api.cert.scopussearch.net/sharedsearch/document/result"

    REQUEST_HEADERS = {"Content-Type": "application/json",
                   "x-els-product" : "embeddings",
                   "x-els-dataset" : "embeddings"}

    def __init__(self) -> None:
        self.json_io = VectorQueryJsonIO()

    def num_results(self, query_string: str) -> int:
        MAX_SUPPORTED_AMOUNT = 500
        payload = {
            "query": { 
                "semanticQueryString": query_string 
            },
            "resultSet": {
                "skip": 0,
                "amount": MAX_SUPPORTED_AMOUNT 
            }, 
            "sortBy": [{
                "fieldName": "relevance", 
                "order": "desc"
            }],
            "returnFields": [  # returnFields = 'abstract', 'author', 'authorSort', 'controlledTerms', 'database', 'date', 'dedupkey', 'dmask', 'doi', 'eid', 'eidocid', 'loadNumber', 'parentId', 'pcited', 'publicationYear', 'publisherNameSort', 'serialTitle', 'subHeading', 'tdocid', 'title'
                "relevance",
                "eid",
                "authors",
                "authid",
                "abs", 
                "pubyr"]}

        response = None
        try:
            response = requests.post(VectorSearchClient.ENDPOINT, 
                                     json=payload, 
                                     headers=VectorSearchClient.REQUEST_HEADERS)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{payload}\n")
        
        # error handling
        if response is None:
            raise RuntimeError(f"error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{payload}\n")
        
        response_json = response.json()
        n_results = len(response_json["hits"])
        return n_results

    def retrieve_top_entries(self, query_string: str, n_top_entries: int) -> None:
        MAX_SUPPORTED_AMOUNT = 500
        n_top_entries = min(n_top_entries, MAX_SUPPORTED_AMOUNT)
        payload = {
            "query": { 
                "semanticQueryString": query_string 
            },
            "resultSet": {
                "skip": 0,
                "amount": n_top_entries 
            }, 
            "sortBy": [{
                "fieldName": "relevance", 
                "order": "desc"
            }],
            "returnFields": [  # returnFields = 'abstract', 'author', 'authorSort', 'controlledTerms', 'database', 'date', 'dedupkey', 'dmask', 'doi', 'eid', 'eidocid', 'loadNumber', 'parentId', 'pcited', 'publicationYear', 'publisherNameSort', 'serialTitle', 'subHeading', 'tdocid', 'title'
                "relevance",
                "eid",
                "authors",
                "authid",
                "abs", 
                "pubyr"]}

        response = None
        try:
            response = requests.post(VectorSearchClient.ENDPOINT, 
                                     json=payload, 
                                     headers=VectorSearchClient.REQUEST_HEADERS)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{payload}\n")
        
        # error handling
        if response is None:
            raise RuntimeError(f"error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{payload}\n")
        
        response_json = response.json()
        entries = response_json["hits"]
        self.json_io.write(query_string, entries)


##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    vectorSearchClient = VectorSearchClient()
    test_query = "cancer treatment"
    vectorSearchClient.retrieve_top_entries(test_query, 20)
    json_io = VectorQueryJsonIO()
    data = json_io.read(test_query)
    print(data)
    eids = json_io.get_eids(test_query)
    auids = json_io.get_auids(test_query)
    abstracts = json_io.get_abstracts(test_query)
    print(eids)
    print(auids)
    print(abstracts)
