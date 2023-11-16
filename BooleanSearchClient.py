from BooleanString import BooleanString
from collections import namedtuple
import requests
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
import re
import os
from DBClient import DBClient

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

    def retrieve_all_authors(self, query: str, num_threads = 6) -> pd.DataFrame:
        query = BooleanString(query).to_boolean_query()
        url = f'{BooleanSearchClient.ENDPOINT}?query={query}&apiKey={self.api_key}&insttoken={self.inst_token}&cursor=*&view=complete&sort=citedby-count'

        # retrive all authors
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            get_url = lambda query: f'{BooleanSearchClient.ENDPOINT}?query={query}&apiKey={self.api_key}&insttoken={self.inst_token}&cursor=*&view=complete&sort=citedby-count'
            futures = [ executor.submit(self._process_query(get_url(query), id_value)) for query, id_value in zip(queries, ids) ]
            processed_queries = []
            for future in futures:
                result = future.result()
                if result:
                    processed_queries.append(result)
            return pd.DataFrame()
	
    def try_limit_to_recent(self, query: str) -> TimeLimitWiggleResult:
        # TODO: use query
        return TimeLimitWiggleResult(start_year=2013, end_year=2023, worked=True)
    
    def try_loosen_time_limit(self, query: str) -> TimeLimitWiggleResult:
        # TODO: use query
        return TimeLimitWiggleResult(start_year=2013, end_year=2023, worked=True)
    
    def _process_query(self, url: str, filename: str, max_docs=200) -> pd.DataFrame | None:
        if max_docs <= 0:
            print(f"max_docs must be above 0, received {max_docs}")
            return

        response = None
        try:
            response = requests.get(url)
        except Exception as e:
            raise RuntimeError(f"error sending request.\nurl: {url}")
        
        # error handling
        if response.status_code != 200:
            print(f"response.status_code not 200: {response.status_code}") 
            return
        
        data = response.json()

        if 'service-error' in data:
            status_code = data['service-error'].get('status:statusCode')
            statusText = data['service-error'].get('status:statusText')
            print ("query_status:", status_code)
            print ("error_text:", statusText)
            return

        if 'search-results' not in data:
            print("There is no 'search-results' in response data")
            return 

        dfs = []
        entry_data = []
        processed_urls = set()

        entries = data['search-results'].get('entry', [])
        entry_data.extend(entries)
        links = data['search-results'].get('link', [])
        next_link = None
        for link in links:
            if link.get('@ref') == 'next':
                next_link = link.get('@href')
                break
        processed_urls.add(next_link)

        url_count = 0
        items_per_page = int(data['search-results']["opensearch:itemsPerPage"])
        MAX_PAGES = int(np.ceil(max_docs / items_per_page))
        while next_link and url_count < MAX_PAGES:
            response = requests.get(next_link)
            data = response.json()
            entries = data['search-results'].get('entry', [])
            entry_data.extend(entries)
            links = data['search-results'].get('link', [])
            next_link = None
            for link in links:
                if link.get('@ref') == 'next':
                    next_link = link.get('@href')
                    break
            if next_link in processed_urls:
                print("Next URL already processed. Exiting loop.")
                break
            url_count += 1
            if url_count == MAX_PAGES:
                print("Reached iteration limit. Exiting loop.")
                break
            processed_urls.add(next_link)
            
        df = pd.DataFrame(entry_data)
        for entry in entry_data:
            lst = entry.get('author', [])
            author_names = [f"{author['surname']}, {author['given-name']}" for author in lst]
            ids = [author.get('authid') for author in lst]
            if len(author_names) == len(ids):
                combined_names = [f"{author['given-name']} {author['surname']} ({author['authid']})" for author in lst]
                df_row = pd.DataFrame({'Authors': ['; '.join(author_names)],
                                        'Author full names': ['; '.join(combined_names)],
                                        'Author(s) ID': ['; '.join(ids)]
                                        })
                dfs.append(df_row)
        df_concatenated = pd.concat(dfs, ignore_index=True)
        #print(df_concatenated)
        df_selected = df[['dc:title', 'prism:volume','prism:issueIdentifier','article-number', 'citedby-count', 'prism:doi', 'subtypeDescription', 'eid', 'prism:pageRange', 'prism:coverDate', 'prism:publicationName', 'dc:description', 'freetoreadLabel', 'link']].rename(columns={
            'dc:title': 'Title', 
            'prism:volume': 'Volume', 
            'prism:issueIdentifier': 'Issue', 
            'article-number':'Art. No.', 
            'citedby-count':'Cited by', 
            'prism:doi':'DOI',
            'subtypeDescription':'Document Type', 
            'prism:publicationName':'Source title', 
            'dc:description':'Abstract', 
            'freetoreadLabel':'OpenAccess', 
            'eid':'EID', 
            'link':'Link'})
        #df_selected[['Page start', 'Page end']] = df_selected['prism:pageRange'].str.split('-', expand=True)
        df_selected['Page start'] = df_selected['prism:pageRange'].apply(lambda x: x if x is None or '-' not in x else x.split('-')[0])
        df_selected['Page end'] = df_selected['prism:pageRange'].apply(lambda x: x.split('-')[1] if (x is not None and '-' in x)  else None )
        df_selected['prism:coverDate'] = pd.to_datetime(df_selected['prism:coverDate'])
        df_selected['Page count'] = df_selected.apply(lambda row: self._calculate_range(row['Page start'], row['Page end']) if (row['Page start'] is not None and row['Page end'] is not None) else None, axis=1)
        df_selected['Year'] = df_selected['prism:coverDate'].dt.year
        df_selected['OpenAccess'] = df_selected['OpenAccess'].apply(lambda x: [item['$'].replace('$', '') for item in x['value']] if isinstance(x, dict) and 'value' in x and isinstance(x['value'], list) else None)
        df_selected['Link'] = df_selected['Link'].apply(lambda x: [item['@href'] for item in x if isinstance(item, dict) and item.get('@ref') == 'scopus'] if isinstance(x, list) else None)
        df_selected['Link'] = df_selected['Link'].str[0].str.replace(r"\[\'|\'\]", "", regex=True)
        #print (df_selected['link'])
        df_combined = pd.concat([df_concatenated, df_selected], axis=1)    
        #display (df_combined)
        df_combined = df_combined[["Authors","Author full names","Author(s) ID","Title","Year","Source title","Volume","Issue","Art. No.","Page start","Page end","Page count","Cited by","DOI","Link","Abstract","Document Type","OpenAccess","EID"]]        
        file_name = os.path.join(f"output/{filename}.csv")
        df_combined.to_csv(file_name, index=False)

    def _calculate_range(self, start, end):
        start_numeric = re.sub(r'\D', '', start)
        end_numeric = re.sub(r'\D', '', end)
        if start_numeric and end_numeric:
            start_int = int(start_numeric)
            end_int = int(end_numeric)
            return end_int - start_int + 1
        else:
            return None



	



test_boolean_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND ( LIMIT-TO ( AFFILCOUNTRY , "Saudi Arabia" ) ) AND ( LIMIT-TO ( PUBYEAR , 2017 ) OR LIMIT-TO ( PUBYEAR , 2018 ) OR LIMIT-TO ( PUBYEAR , 2019 ) OR LIMIT-TO ( PUBYEAR , 2020 ) OR LIMIT-TO ( PUBYEAR , 2021 ) OR LIMIT-TO ( PUBYEAR , 2022 ) OR LIMIT-TO ( PUBYEAR , 2023 ) )'
query_string = BooleanString(test_boolean_string).from_boolean_string()
query_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND (  ( AFFILCOUNTRY (Saudi Arabia) ) ) AND (  ( PUBYEAR IS 2017 ) OR  ( PUBYEAR IS 2018 ) OR  ( PUBYEAR IS 2019 ) OR  ( PUBYEAR IS 2020 ) OR  ( PUBYEAR IS 2021 ) OR  ( PUBYEAR IS 2022 ) OR  ( PUBYEAR IS 2023 ) )'
client = BooleanSearchClient()
# num_results = client.num_results(query_string)
# print(num_results)
# client.retrieve_all_authors(query_string)
is_invalid = client.is_invalid_input(query_string)
print(is_invalid)
