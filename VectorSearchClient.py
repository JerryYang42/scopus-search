import json
import requests

class VectorSearchClient():

    ENDPOINT = "https://shared-search-service-api.cert.scopussearch.net/sharedsearch/document/result"

    REQUEST_HEADERS = {"Content-Type": "application/json",
                   "x-els-product" : "embeddings",
                   "x-els-dataset" : "embeddings"}

    def __init__(self, api_key: str, inst_token: str) -> None:
        self.api_key = api_key  # Scopus API Key
        self.inst_token = inst_token  # institutional token

    def get_api_response(self, query_string: str) -> requests.Response:
        try:
            request_payload = '{"query":{"semanticQueryString":"response"},"resultSet":{"skip":0,"amount":500},' \
                              '"sortBy":[{"fieldName":"relevance","order":"desc"}],' \
                              '"returnFields": ["relevance","eid","authors","authid","abs","pubyr"]}'

            data = json.loads(request_payload)
            data["query"]["semanticQueryString"] = f"{query_string}"

            request_payload_json = data

            return requests.post(VectorSearchClient.ENDPOINT, json=request_payload_json, headers=VectorSearchClient.REQUEST_HEADERS)
        except Exception as e:
            raise RuntimeError("error requesting {URL}\nquery: {query}\n")

    def num_of_results(self, response: requests.Response) -> int:
        if response.status_code == 200:
            data = response.json()

            if 'hits' in data:
                total_results = len(data['hits'])
                return total_results
            else:
                raise ValueError("No 'hits' in response: \n{data}")

    def extract_response(self, api_response: requests.Response):
        response_json = api_response.json()
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