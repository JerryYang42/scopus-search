import hashlib
import pandas as pd
from typing import List, Tuple

from JsonIO import BooleanStringJsonIO, SiBooleanStringMappingJsonIO, SIVectorQueryMappingJsonIO

def get_boolean_string_query_ids(special_issue_id) -> Tuple[List, List]:
    # # test data
    # boolean_str_1 = "TITLE-ABS-KEY ( \"analytical chemistry\" ) AND TITLE-ABS-KEY ( \"sample preparation\" ) OR TITLE-ABS-KEY ( \"extraction technologies\" ) OR TITLE-ABS-KEY ( \"green analytical chemistry\" ) OR TITLE-ABS-KEY ( \"sample clean-up\" ) OR TITLE-ABS-KEY ( \"sustainability\" ) AND SUBJTERMS ( 1602 OR 2304 OR 1303 OR 1607 )"
    # boolean_str_2 = "TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( sustainability ) OR TITLE-ABS-KEY ( transitions ) OR TITLE-ABS-KEY ( bioeconomy ) AND SUBJTERMS ( 3300 )"
    # { ("0ca3b59e6ba8", boolean_str_1),
    #   ("0e103a8a59c5", boolean_str_2) }

    json_io = SiBooleanStringMappingJsonIO()
    data = json_io.read()
    entries = data['mappings']
    entry = json_io._get_entry(special_issue_id, from_entries=entries)
    special_issue_id_not_exists = (len(entry) == 0)
    if special_issue_id_not_exists:
        return []
    entry = entry[0]
    boolean_string_items = entry['boolean_strings']
    boolean_strings = [boolean_string_item['boolean_string'] for boolean_string_item in boolean_string_items]
    return boolean_strings
    

def get_boolean_string_eids(boolean_string: str) -> List[str]:
    json_io = BooleanStringJsonIO()
    eids = json_io.get_eids(boolean_string)
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
        boolean_strings = get_boolean_string_query_ids(special_issue_id)
        
        siid_qid_map_list.append({
            'SPECIAL_ISSUE_ID': special_issue_id,
            'LANDING_PAGE_URL': url,
            'boolean_strings': boolean_strings
        })
    siid_qid_map_df = pd.DataFrame(siid_qid_map_list)
    ssid_qid_long_mappings = siid_qid_map_df.explode('boolean_strings').rename(columns={'boolean_strings': 'BOOLEAN_STRING'})
    ssid_qid_long_mappings['QUERY_ID'] = ssid_qid_long_mappings['BOOLEAN_STRING'].apply(lambda s: _to_query_id(s))
    ssid_qid_long_mappings['eids'] = ssid_qid_long_mappings['BOOLEAN_STRING'].apply(lambda s: get_boolean_string_eids(s))
    ssid_qid_long_mappings = ssid_qid_long_mappings.explode('eids').rename(columns={'eids': 'EID'})
    # COLUMNS = ['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'BOOLEAN_STRING', 'QUERY_ID', 'EID']



#####################################################################################
# Test
#####################################################################################

if __name__ == "__main__":
    # input should be a csv file has these columns
    # COLUMNS = ['SPECIAL_ISSUE_ID', 'JOURNAL_ACRONYM', 'ASJC_CORE', 'LANDING_PAGE_URL']
    filepath = "input/eval_input_hackathon_boolean_v2_with_urls.csv"
    
    # output df is a long table with these columns
    # COLUMNS = ['SPECIAL_ISSUE_ID', 'LANDING_PAGE_URL', 'BOOLEAN_STRING', 'QUERY_ID', 'EID']
    result_df = get_boolean_string_result_df(filepath)


    ## Do evaluation bellow