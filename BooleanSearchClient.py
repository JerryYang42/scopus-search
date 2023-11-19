from BooleanString import BooleanString
from collections import namedtuple
from typing import Any, List, Dict, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import re
from DBClient import DBClient, QuerySource, QueryStatus
from ProjectSecrets import Secrets

TimeLimitWiggleResult = namedtuple('TimeLimitWiggleResult', ('start_year', 'end_year', 'worked'))

class BooleanSearchClient:
    ENDPOINT = 'https://api.elsevier.com/content/search/scopus'

    def __init__(self, api_key: str, inst_token: str) -> None:
        self.api_key = api_key  # Scopus API Key
        self.inst_token = inst_token  # institutional token

    def num_results(self, query: str) -> int:
        query = BooleanString(query).to_boolean_query()
        url = f'{BooleanSearchClient.ENDPOINT}?query={query}&apiKey={self.api_key}&insttoken={self.inst_token}&sort=citedby-count'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                if 'search-results' in data:
                    total_results = int(data['search-results'].get('opensearch:totalResults'))
                    return total_results
                else:
                    raise ValueError("No 'search-results' in response: \n{data}")
        except Exception as e:
            raise RuntimeError("error requesting {URL}\nquery: {query}\n")
    
    def is_invalid_input(self, query: str) -> bool:
        query = BooleanString(query).to_boolean_query()
        url = f'{BooleanSearchClient.ENDPOINT}?query={query}&apiKey={self.api_key}&insttoken={self.inst_token}'
        response = None
        try:
            response = requests.get(url)
        except Exception as e:
            raise RuntimeError("error requesting {URL}\nquery: {query}\n")
        if response.status_code == 400:
            return True
        return False

    def retrieve_top_entries(self, query: str, n_top_entries: int, dbClient: DBClient) -> pd.DataFrame:
        if n_top_entries <= 0:
            raise ValueError(f"n_top_entries must be above 0, received {n_top_entries}")
        
        url_from = lambda query: f'{BooleanSearchClient.ENDPOINT}?query={BooleanString(query).to_boolean_query()}&apiKey={self.api_key}&insttoken={self.inst_token}&cursor=*&view=complete&sort=citedby-count'
        entries =  self._retrieve_entries_from_url(url_from(query), n_top_entries)
        # TODO: move to App
        # success = dbClient.update_query_status(query, QueryStatus.accepted)
        qid = dbClient.get_accepted_qid(query)
        dbClient.add_entries(qid, entries)
	
    def try_limit_to_recent(self, query: str) -> TimeLimitWiggleResult:
        # TODO: use query
        return TimeLimitWiggleResult(start_year=2013, end_year=2023, worked=True)
    
    def try_loosen_time_limit(self, query: str) -> TimeLimitWiggleResult:
        # TODO: use query
        return TimeLimitWiggleResult(start_year=2013, end_year=2023, worked=True)
    
    def _retrieve_entries_from_url(self, url: str, n_top_entries: int) -> List[Dict[Any, Any]]:

        response = None
        try:
            response = requests.get(url)
            response.raise_for_status
        except Exception as e:
            raise RuntimeError(f"Error sending request.\nurl: {url}")
        
        # error handling
        if response.status_code != 200:
            raise RuntimeError(f"response.status_code not 200: {response.status_code}\nurl: {url}")
        response_data = response.json()
        if 'service-error' in response_data:
            status_code = response_data['service-error'].get('status:statusCode')
            status_text = response_data['service-error'].get('status:statusText')
            raise RuntimeError(f"returned service error with status code{status_code}\nstatus text{status_text}\nurl: {url}")
        if 'search-results' not in response_data:
            raise RuntimeError("There is no 'search-results' in response data for url: \n{url}")
        
        total_results = int(response_data['search-results'].get('opensearch:totalResults'))
        n_top_entries = min(total_results, n_top_entries)

        collected_top_entries = []
        _processed_urls = set()

        _n_entries_to_go = n_top_entries - len(collected_top_entries)
        _entries = self._entries_from_response_data(response_data)[:_n_entries_to_go]  # won't cause OutOfRangeError, a=[1,2]; a[:10]; returns [1,2]
        collected_top_entries.extend(_entries)
        _n_entries_to_go = n_top_entries - len(collected_top_entries)
        next_page_url = self._next_page_url_from(response_data)
        _processed_urls.add(self._current_page_url_from(response_data))
        
        _has_next_page = (next_page_url is not None)
        while (_has_next_page) and (_n_entries_to_go > 0):
            current_page_url = next_page_url

            if current_page_url in _processed_urls:  
                print("Next URL already processed. Exiting loop.")
                break

            response = requests.get(current_page_url)
            response_data = response.json()

            _n_entries_to_go = n_top_entries - len(collected_top_entries)
            _entries = self._entries_from_response_data(response_data)[:_n_entries_to_go]
            collected_top_entries.extend(_entries)
            _n_entries_to_go = n_top_entries - len(collected_top_entries)
            if _n_entries_to_go == 0:
                print("Reached iteration limit. Exiting loop.")
                break
            _processed_urls.add(current_page_url)
            
            next_page_url = self._next_page_url_from(response_data)
            _has_next_page = (next_page_url is not None)
            
        return collected_top_entries
        
    
    def _next_page_url_from(self, response_data: Dict[Any, Any]) -> str|None: 
        return self._target_page_url_from(response_data, 'next')
    
    def _current_page_url_from(self, response_data: Dict[Any, Any]) -> str|None:
        return self._target_page_url_from(response_data, 'self')
    
    def _target_page_url_from(self, response_data: Dict[Any, Any], target_page_tag: str) -> str|None:
        page_urls = response_data['search-results'].get('link', [])
        target_page_url = None
        for page_url in page_urls:
            if page_url.get('@ref') == target_page_tag:
                target_page_url = page_url.get('@href')
                return target_page_url
        return target_page_url
    
    def _entries_from_response_data(self, response_data: str) -> List[Any]:
        return response_data['search-results'].get('entry', [])

    def _calculate_range(self, start, end):
        start_numeric = re.sub(r'\D', '', start)
        end_numeric = re.sub(r'\D', '', end)
        if start_numeric and end_numeric:
            start_int = int(start_numeric)
            end_int = int(end_numeric)
            return end_int - start_int + 1
        else:
            return None

    def retrieve_entries_for_queries(self):
        pass
        # TODO: multi-threading
        # with ThreadPoolExecutor(max_workers=num_threads) as executor:
        #     get_url = lambda query: f'{BooleanSearchClient.ENDPOINT}?query={query}&apiKey={self.api_key}&insttoken={self.inst_token}&cursor=*&view=complete&sort=citedby-count'
        #     futures = [ executor.submit(self._process_query(get_url(query), id_value)) for query, id_value in zip(queries, ids) ]
        #     processed_queries = []
        #     for future in futures:
        #         result = future.result()
        #         if result:
        #             processed_queries.append(result)


##################################################
# TEST
##################################################

if __name__ == "__main__":
    # test_boolean_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND ( LIMIT-TO ( AFFILCOUNTRY , "Saudi Arabia" ) ) AND ( LIMIT-TO ( PUBYEAR , 2017 ) OR LIMIT-TO ( PUBYEAR , 2018 ) OR LIMIT-TO ( PUBYEAR , 2019 ) OR LIMIT-TO ( PUBYEAR , 2020 ) OR LIMIT-TO ( PUBYEAR , 2021 ) OR LIMIT-TO ( PUBYEAR , 2022 ) OR LIMIT-TO ( PUBYEAR , 2023 ) )'
    # query_string = BooleanString(test_boolean_string).to_boolean_query()
    # query_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND (  ( AFFILCOUNTRY (Saudi Arabia) ) ) AND (  ( PUBYEAR IS 2017 ) OR  ( PUBYEAR IS 2018 ) OR  ( PUBYEAR IS 2019 ) OR  ( PUBYEAR IS 2020 ) OR  ( PUBYEAR IS 2021 ) OR  ( PUBYEAR IS 2022 ) OR  ( PUBYEAR IS 2023 ) )'
    client = BooleanSearchClient(secrets.BOOLEAN_SEARCH_API_KEY, secrets.BOOLEAN_SEARCH_INST_TOKEN)
    # num_results = client.num_results(query_string)
    # print(num_results)
    # client.retrieve_all_authors(query_string)
    # is_invalid = client.is_invalid_input(query_string)
    # assert not is_invalid 

    # 
    # dbClient = DBClient()
    # dbClient.add_boolean_string(test_boolean_string, QuerySource.chatGPT, QueryStatus.rejected)
    # dbClient.update_query_status(test_boolean_string, QueryStatus.accepted)
    # client.retrieve_entries(test_boolean_string, n_top_entries=20, dbClient=dbClient)
    # df_authors = dbClient.read_authors(test_boolean_string)
    # print(df_authors)

    # 
    # boolean_string = '''TITLE-ABS-KEY ( "plant-based" ) AND TITLE-ABS-KEY ( "animal analogues" ) AND TITLE-ABS-KEY ( "consumer acceptance" ) AND TITLE-ABS-KEY ( "flavour attributes" ) AND TITLE-ABS-KEY ( "health" ) AND TITLE-ABS-KEY ( "market growth" ) AND TITLE-ABS-KEY ( "nutrition" ) AND TITLE-ABS-KEY ( "plant-based ingredients" ) AND TITLE-ABS-KEY ( "product development" ) AND TITLE-ABS-KEY ( "product quality" ) AND TITLE-ABS-KEY ( "sensory attributes" ) AND TITLE-ABS-KEY ( "sustainable alternatives" ) AND TITLE-ABS-KEY ( "texture attributes" ) AND SUBJTERMS ( 1106 ) AND PUBYEAR > 2017 AND PUBYEAR < 2025'''
    # boolean_string = '''TITLE-ABS-KEY ( "plant-based" AND "animal analogues" ) AND TITLE-ABS-KEY ( "consumer acceptance" OR "flavour attributes" OR "product development" OR "product quality" OR "sensory attributes" OR "texture attributes" ) AND SUBJTERMS ( 1106 ) AND PUBYEAR > 2017 AND PUBYEAR < 2025'''
    boolean_string = '''( TITLE-ABS-KEY ( "plant-based" ) OR TITLE-ABS-KEY ( "animal analogues" ) OR TITLE-ABS-KEY ( "consumer acceptance" ) OR TITLE-ABS-KEY ( "flavour attributes" ) OR TITLE-ABS-KEY ( "health" ) OR TITLE-ABS-KEY ( "market growth" ) OR TITLE-ABS-KEY ( "nutrition" ) OR TITLE-ABS-KEY ( "product development" ) OR TITLE-ABS-KEY ( "product quality" ) OR TITLE-ABS-KEY ( "sensory attributes" ) OR TITLE-ABS-KEY ( "sustainable alternatives" ) OR TITLE-ABS-KEY ( "texture attributes" ) ) AND SUBJTERMS ( 1106 )'''
    n_results = client.num_results(boolean_string)
    print(n_results)

