import json
import requests
from typing import Tuple, List
import pandas as pd
from datetime import datetime

class VectorSearchClient():

    ENDPOINT = "https://shared-search-service-api.cert.scopussearch.net/sharedsearch/document/result"

    REQUEST_HEADERS = {"Content-Type": "application/json",
                   "x-els-product" : "embeddings",
                   "x-els-dataset" : "embeddings"}

    def retrieve_top_entries(self, query_string: str, n_top_entries: int) -> None:
        # request_data json
        PAYLOAD = '{"query":{"semanticQueryString":"response"},"resultSet":{"skip":0,"amount":500},' \
                              '"sortBy":[{"fieldName":"relevance","order":"desc"}],' \
                              '"returnFields": ["relevance","eid","authors","authid","abs","pubyr"]}'
        request_json = json.loads(PAYLOAD)
        request_json['query']["semanticQueryString"] = query_string
        # request_json['resultSet']["amount"] = n_top_entries
        # returnFields = 'abstract', 'author', 'authorSort', 'controlledTerms', 'database', 'date', 'dedupkey', 'dmask', 'doi', 'eid', 'eidocid', 'loadNumber', 'parentId', 'pcited', 'publicationYear', 'publisherNameSort', 'serialTitle', 'subHeading', 'tdocid', 'title'
        # if n_top_entries < 0:
        #     raise ValueError(f"invalid n_top_entries: {n_top_entries} ")
        # payload = {
        #     "query": { 
        #         "semanticQueryString": query_string },
        #     "resultSet":{
        #         "skip": 0,
        #         "amount": n_top_entries }, 
        #     "sortBy":[ 
        #         {"fieldName": "relevance", "order": "desc"} ],
        #     "returnFields": [
        #         "relevance",
        #         "eid",
        #         "authors",
        #         "authid",
        #         "abs", 
        #         "pubyr","title"]}
        # request_json = json.dumps(payload)

        response = None
        try:
            response = requests.post(VectorSearchClient.ENDPOINT, 
                                     json=request_json, 
                                     headers=VectorSearchClient.REQUEST_HEADERS)
        except Exception as e:
            raise RuntimeError("error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{request_json}\n")
        
        # error handling
        if response is None:
            raise RuntimeError("error requesting {VectorSearchClient.ENDPOINT}\nrequest: \n{request_json}\n")
        response.raise_for_status()
        
        response_json = response.json()
        self._extract_response(response_json)

    def _extract_response(self, response_json) -> Tuple[List[str]]:

        hits = response_json["hits"]
        # COLUMNS = ['relevance', 'eid', 'authors', 'abs', 'pubyr']

        # COLUMNS = ['authid']
        

        auid_list = []
        manuscript_abstracts = []
        eid_list = []

        for hit in hits:
            manuscript_abstracts.append(hit["abs"])
            eid_list.append(hit["eid"])
            if hit.get("authors"):
                hit_author = hit["authors"]
                for auid in hit_author:
                    actual_auid = auid["authid"]
                    auid_list.append(actual_auid)
            else:
                continue

        entries = {'auid_list': auid_list, 'manustript_abstracts': manuscript_abstracts, 'eid_list': eid_list}
        entries_json = json.dumps(entries)
        filename = f'vector_search_output/{datetime.now().strftime("%Y-%m-%d-H-%M-%S")}'
        # Writing to sample.json
        with open(f"{filename}.json", "w") as outfile:
            outfile.write(entries_json)


    def try_limit_to_recent(self):
        pass

    def try_loosen_time_limit(self):
        pass



##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    vectorSearchClient = VectorSearchClient()
    vectorSearchClient.retrieve_top_entries("cancer treatment", 20)
