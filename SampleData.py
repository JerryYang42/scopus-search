import pandas as pd
from typing import Dict, Any
from collections import namedtuple

from WebScrapper import WebScapper, WebInfo
from Config import Config


COLUMNS = ['ITEM_GROUP_JOURNAL_REFERENCE', 'ACRONYM', 'BU', 'SPECIAL_ISSUE_TITLE',
       'LANDING_PAGE_URL', 'ONE_LINE_SCOPE_DESCRIPTION', 'ASJC_CORE',
       'KEYWORDS', 'BOOLEAN STRING']

SampleDataRow = namedtuple('SampleDataRow', ['asjc_codes', 'boolean_string'])

class SampleData:

    def __init__(self) -> None:
        self._scrapper = WebScapper()
        self._selected_sample_ids = [
            'JTUMED_SI030181',
            'FOOHUM_SI028840',
            'MICROB_SI029657',
            'JRRAS_IG000014',
            'IJCHP_SI030184',
            'CAG_SI030324'
        ]
        self._selected_negative_sample_ids = [
            'HORTI_IG002597'
        ]
        self._df = pd.read_excel(Config.EXAMPLE_QUERIES_XLSX_FILEPATH)  
        self._samples: Dict[str, SampleDataRow] = {}
        self._web_infos: Dict[str, WebInfo] = {}

    def get_sample(self, i: int) -> SampleDataRow:
        assert i < len(self._selected_sample_ids)
        
        sample_id = self._selected_sample_ids[i]
        if sample_id in self._samples:
            return self._samples[sample_id]
        
        row: pd.DataFrame = self._df[self._df.ITEM_GROUP_JOURNAL_REFERENCE==self._selected_sample_ids[i]]
        sample = row.to_dict('records')[0]
        sampleDataRow = SampleDataRow(asjc_codes=sample['ASJC_CORE'], boolean_string=sample['BOOLEAN STRING'])
        self._samples[sample_id] = sampleDataRow
        return sampleDataRow
    
    def get_negative_sample(self, i: int) -> SampleDataRow:
        assert i < len(self._selected_negative_sample_ids)

        sample_id = self._selected_negative_sample_ids[i]
        if sample_id in self._samples:
            return self._samples[sample_id]
        
        row: pd.DataFrame = self._df[self._df.ITEM_GROUP_JOURNAL_REFERENCE==self._selected_negative_sample_ids[i]]
        sample = row.to_dict('records')[0]
        sampleDataRow = SampleDataRow(asjc_codes=sample['ASJC_CORE'], boolean_string=sample['BOOLEAN STRING'])
        self._samples[sample_id] = sampleDataRow
        return sampleDataRow
    
    def get_web_info(self, i: int) -> WebInfo:
        assert i < len(self._selected_sample_ids)

        sample_id = self._selected_sample_ids[i]
        if sample_id in self._web_infos:
            return self._web_infos[sample_id]
        
        row: pd.DataFrame = self._df[self._df.ITEM_GROUP_JOURNAL_REFERENCE==self._selected_sample_ids[i]].reset_index()
        url: str = row.loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        self._web_infos[sample_id] = web_info
        return web_info
    
    def get_negative_web_info(self, i: int) -> WebInfo:
        assert i < len(self._selected_negative_sample_ids)

        sample_id = self._selected_negative_sample_ids[i]
        if sample_id in self._web_infos:
            return self._web_infos[sample_id]
        
        row: pd.DataFrame = self._df[self._df.ITEM_GROUP_JOURNAL_REFERENCE==self._selected_negative_sample_ids[i]].reset_index()
        url: str = row.loc[0, 'LANDING_PAGE_URL']  # row.iloc[0]['LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        self._web_infos[sample_id] = web_info
        return web_info



##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    samples = SampleData()
    print(samples.get_negative_web_info(0))
