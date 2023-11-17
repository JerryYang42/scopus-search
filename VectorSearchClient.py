import json
import requests
from typing import Tuple, List

class VectorSearchClient():

    ENDPOINT = "https://shared-search-service-api.cert.scopussearch.net/sharedsearch/document/result"

    REQUEST_HEADERS = {"Content-Type": "application/json",
                   "x-els-product" : "embeddings",
                   "x-els-dataset" : "embeddings"}

    def retrieve_top_entries(self, query_string: str) -> requests.Response:
        # request_data json
        PAYLOAD = '{"query":{"semanticQueryString":"response"},"resultSet":{"skip":0,"amount":500},' \
                              '"sortBy":[{"fieldName":"relevance","order":"desc"}],' \
                              '"returnFields": ["relevance","eid","authors","authid","abs","pubyr"]}'
        request_data = json.loads(PAYLOAD)
        request_data["query"]["semanticQueryString"] = query_string

        response = None
        try:
            response = requests.post(VectorSearchClient.ENDPOINT, 
                                     json=request_data, 
                                     headers=VectorSearchClient.REQUEST_HEADERS)
        except Exception as e:
            raise RuntimeError("error requesting {URL}\nquery: {query}\n")
        
        # error handling
        response.raise_for_status()
        
        response_json = response.json()
        self._extract_response(response_json)
        

    def num_of_results(self, response_json: requests.Response) -> int:
        if response.status_code == 200:
            data = response.json()

            if 'hits' in data:
                total_results = len(data['hits'])
                return total_results
            else:
                raise ValueError("No 'hits' in response: \n{data}")

    def _extract_response(self, response_json) -> Tuple[List[str]]:
        hits = response_json["hits"]

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

        return auid_list, manuscript_abstracts, eid_list

    def try_limit_to_recent(self):
        pass

    def try_loosen_time_limit(self):
        pass


######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    vectorSearch = VectorSearchClient()

