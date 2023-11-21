import hashlib
import pandas as pd
from typing import List, Tuple

from JsonIO import BooleanStringJsonIO, SiBooleanStringMappingJsonIO, VectorQueryJsonIO, SIVectorQueryMappingJsonIO

def get_boolean_string_query_ids(url: str) -> List[str]:
    json_io = SiBooleanStringMappingJsonIO()
    data = json_io.read()
    entries = data['mappings']
    entry = json_io._get_entry(url, from_entries=entries)
    special_issue_id_not_exists = (len(entry) == 0)
    if special_issue_id_not_exists:
        return []
    entry = entry[0]
    boolean_strings = entry['boolean_strings']
    return boolean_strings

def get_boolean_string_eids(boolean_string: str) -> List[str]:
    json_io = BooleanStringJsonIO()
    eids = json_io.get_eids(boolean_string)
    return eids

def get_vector_string_query_ids(url: str) -> List[str]:
    json_io = SIVectorQueryMappingJsonIO()
    data = json_io.read()
    entries = data['mappings']
    entry = [entry for entry in entries if entry["url"] == url]
    special_issue_id_not_exists = (len(entry) == 0)
    if special_issue_id_not_exists:
        return []
    entry = entry[0]
    query_strings = entry['query_strings']
    return query_strings

def get_vector_string_query_eids(vector_string: str) -> List[str]:
    json_io = VectorQueryJsonIO()
    eids = json_io.get_eids(vector_string)
    return eids

def _to_query_id(boolean_string: str) -> str:
    m = hashlib.md5()
    m.update(boolean_string.encode('utf-8'))
    return str(m.hexdigest())[:12]

def get_boolean_string_result_df(filepath: str):

    # COLUMNS = ['SPECIAL_ISSUE_ID', 'JOURNAL_ACRONYM', 'ASJC_CORE', 'LANDING_PAGE_URL']
    input_df = pd.read_csv(filepath)

    processed_input_df = input_df[['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL']]

    ## 'SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'QUERY_ID'
    siid_qid_map_list = []
    for _, row in processed_input_df.iterrows():
        special_issue_id = row['SPECIAL_ISSUE_ID']
        url = row['LANDING_PAGE_URL']
        boolean_strings = get_boolean_string_query_ids(url)
        siid_qid_map = {
            'SPECIAL_ISSUE_ID': special_issue_id,
            'LANDING_PAGE_URL': url,
            'boolean_strings': boolean_strings
        }
        siid_qid_map_list.append(siid_qid_map)
    siid_qid_map_df = pd.DataFrame(siid_qid_map_list)
    siid_qid_map_df = siid_qid_map_df.dropna()
    ssid_qid_long_mappings = siid_qid_map_df.explode('boolean_strings').rename(columns={'boolean_strings': 'BOOLEAN_STRING'})
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings['QUERY_ID'] = ssid_qid_long_mappings['BOOLEAN_STRING'].apply(lambda s: _to_query_id(s))
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings['eids'] = ssid_qid_long_mappings['BOOLEAN_STRING'].apply(lambda s: get_boolean_string_eids(s))
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings = ssid_qid_long_mappings.explode('eids').rename(columns={'eids': 'EID'})
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings = ssid_qid_long_mappings.reset_index()

    # COLUMNS = ['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'BOOLEAN_STRING', 'QUERY_ID', 'EID']
    return ssid_qid_long_mappings

def get_vector_query_result_df(filepath: str):

    # COLUMNS = ['SPECIAL_ISSUE_ID', 'JOURNAL_ACRONYM', 'ASJC_CORE', 'LANDING_PAGE_URL']
    input_df = pd.read_csv(filepath)

    processed_input_df = input_df[['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL']]

    ## 'SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'QUERY_ID'
    siid_qid_map_list = []
    for _, row in processed_input_df.iterrows():
        special_issue_id = row['SPECIAL_ISSUE_ID']
        url = row['LANDING_PAGE_URL']
        vector_strings = get_vector_string_query_ids(url)
        siid_qid_map = {
            'SPECIAL_ISSUE_ID': special_issue_id,
            'LANDING_PAGE_URL': url,
            'vector_strings': vector_strings
        }
        siid_qid_map_list.append(siid_qid_map)
    siid_qid_map_df = pd.DataFrame(siid_qid_map_list)
    siid_qid_map_df = siid_qid_map_df.dropna()
    ssid_qid_long_mappings = siid_qid_map_df.explode('vector_strings').rename(columns={'vector_strings': 'VECTOR_STRING'})
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings['QUERY_ID'] = ssid_qid_long_mappings['VECTOR_STRING'].apply(lambda s: _to_query_id(s))
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings['eids'] = ssid_qid_long_mappings['VECTOR_STRING'].apply(lambda s: get_vector_string_query_eids(s))
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings = ssid_qid_long_mappings.explode('eids').rename(columns={'eids': 'EID'})
    ssid_qid_long_mappings = ssid_qid_long_mappings.dropna()
    ssid_qid_long_mappings = ssid_qid_long_mappings.reset_index()

    # COLUMNS = ['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'BOOLEAN_STRING', 'QUERY_ID', 'EID']
    return ssid_qid_long_mappings


#####################################################################################
# Test
#####################################################################################

if __name__ == "__main__":
    # input should be a csv file has these columns
    # COLUMNS = ['SPECIAL_ISSUE_ID', 'JOURNAL_ACRONYM', 'ASJC_CORE', 'LANDING_PAGE_URL']
    filepath = "input/eval_input_hackathon_boolean_v2_with_urls.csv"

    
    # output df is a long table with these columns
    # COLUMNS = ['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'BOOLEAN_STRING', 'QUERY_ID', 'EID']

    # result_df = get_boolean_string_result_df(filepath)
    # print(result_df.head(0))

    # Put evaluations below

    result_bool_df = get_boolean_string_result_df(filepath)
    result_bool_df.to_csv('output/boolean_results.csv')

    result_vec_df = get_vector_query_result_df(filepath)
    result_vec_df.to_csv('output/vector_results.csv')




    # # test get_boolean_string_result_df
    # url_1 = 'https://www.sciencedirect.com/journal/scientia-horticulturae/about/forthcoming-special-issues#the-impact-of-pre-harvest-and-post-harvest-light-regulation-on-horticultural-plants'
    # url_2 = 'https://www.sciencedirect.com/journal/crop-protection/about/forthcoming-special-issues#detection-epidemiology-and-management-of-plant-disease-complexes'
    
    # # 0ca3b59e6ba8
    # boolean_str_1 = "TITLE-ABS-KEY ( \"analytical chemistry\" ) AND TITLE-ABS-KEY ( \"sample preparation\" ) OR TITLE-ABS-KEY ( \"extraction technologies\" ) OR TITLE-ABS-KEY ( \"green analytical chemistry\" ) OR TITLE-ABS-KEY ( \"sample clean-up\" ) OR TITLE-ABS-KEY ( \"sustainability\" ) AND SUBJTERMS ( 1602 OR 2304 OR 1303 OR 1607 )" 
    # # 0e103a8a59c5
    # boolean_str_2 = "TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( sustainability ) OR TITLE-ABS-KEY ( transitions ) OR TITLE-ABS-KEY ( bioeconomy ) AND SUBJTERMS ( 3300 )"  
    # # 1ec0299d19d2
    # boolean_str_3 = "TITLE-ABS-KEY ( \"air pollution\" ) AND TITLE-ABS-KEY ( \"control policies\" ) AND TITLE-ABS-KEY ( synergies ) AND SUBJTERMS ( 2305 OR 2311 OR 2308 )"
    # # 2af73a28e6b2
    # boolean_str_4 = "TITLE-ABS-KEY ( \"antimicrobial resistance\" ) OR TITLE-ABS-KEY ( \"antimicrobial resistant organisms\" ) OR TITLE-ABS-KEY ( \"antimicrobial resistance genes\" ) OR TITLE-ABS-KEY ( \"aquatic environment\" ) OR TITLE-ABS-KEY ( \"bacterial species\" ) OR TITLE-ABS-KEY ( \"environmental settings\" ) OR TITLE-ABS-KEY ( \"global health\" ) OR TITLE-ABS-KEY ( \"selective pressures\" ) OR TITLE-ABS-KEY ( \"surface water\" ) OR TITLE-ABS-KEY ( \"groundwater\" ) OR TITLE-ABS-KEY ( \"occurrence\" ) OR TITLE-ABS-KEY ( \"transport\" ) AND SUBJTERMS ( 2739 OR 2725 )"  
    
    # si_boolean_string_mapping_json_io = SiBooleanStringMappingJsonIO()
    # si_boolean_string_mapping_json_io.write(url=url_1,
    #                                         boolean_string=boolean_str_1)
    # si_boolean_string_mapping_json_io.write(url=url_1,
    #                                         boolean_string=boolean_str_2)
    # si_boolean_string_mapping_json_io.write(url=url_1,
    #                                         boolean_string=boolean_str_3)
    # si_boolean_string_mapping_json_io.write(url=url_2,
    #                                         boolean_string=boolean_str_4)

    # result_df = get_boolean_string_result_df(filepath)
    # print(result_df.head(0))


    ## Do evaluation bellow