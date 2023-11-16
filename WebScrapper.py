import requests
from collections import namedtuple
from bs4 import BeautifulSoup
import pandas as pd
from typing import Tuple
from dataclasses import dataclass

JournalClassification = namedtuple('JournalClassification', ('top', 'mid', 'low'))

@dataclass
class WebInfo:
    title: str = ''
    description: str = ''
    journal_title: str = ''
    asjc_codes: Tuple[str] = tuple()
    classifications: Tuple[JournalClassification] = tuple()

# resource: https://realpython.com/beautiful-soup-web-scraper-python/

class WebScapper():
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    def __init__(self) -> None:
        self.asjcMapper = AsjcMapper()

    def extract(self, url: str) -> WebInfo:

        response = None
        try:
            # use a header to avoid 403 Client Error: Forbidden for url xxx
            response = requests.get(url, headers=WebScapper.HEADERS)
            # Raise an exception for bad responses
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Error processing URL {url}: {e}")
        
        soup = BeautifulSoup(response.content, 'html.parser')

        journal_title = soup.find('h1', class_='js-title-text').text
        asjc_codes: Tuple[str] = self.asjcMapper.asjcs_from(journal_title=journal_title)
        journal_classifications = self.asjcMapper.classifications_from_asjcs(asjc_codes)

        title_block_id: str = url.split('#')[1]
        title_block = soup.find('h3', {'id': title_block_id})
        title = title_block.text if (title_block is not None) else None
        if title is None:
            try_title_block = soup.find('div', class_='date').find_next_sibling()
            if try_title_block is not None:
                title = try_title_block.text
        if title is None:
            return WebInfo(journal_title=journal_title, 
                           asjc_codes=asjc_codes, 
                           classifications=journal_classifications)

        description = self._extract_description(response, url)
        description = '' if description is None else description
        
        return WebInfo(title=title, 
                       description=description,
                       journal_title=journal_title, 
                       asjc_codes=asjc_codes, 
                       classifications=journal_classifications)
        
        
    def _extract_description(self, response, url: str) -> str:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the relative section by ID
        element_id = url.split('#')[1]
        target_element = soup.find('h3', {'id': element_id})
    
        # Check if the element was found
        if target_element:
            
            # Find the associated <p> element
            associated_paragraph = target_element.find_next('p')
    
            # Check if the <p> element was found
            if associated_paragraph:
    
                ###### 1. get the information under the associated title
                
                # get the text under the title
                para = associated_paragraph.text
    
                # Find the index of "Guest editors:" in the text
                index_guest_editors = para.find("Guest editors:")
                
                # Extract the substring up to the "Guest editors:" section
                desired_extract = para[:index_guest_editors]
    
                ####### 2. get the information under the special issue information, if it exists
                if para.find("Special issue information:"):
                    index_special_start = para.find("Special issue information:")
                    index_special_end = para.find("Manuscript submission information:")
                    si_extract = para[index_special_start:index_special_end].replace('Special issue information:', '')
                
                    desired_extract = desired_extract + ' ' + si_extract
                    
            return(desired_extract)


class AsjcMapper():
    def __init__(self, 
                 path_to_asjc_journal_mapping="ASJC_journals.csv", 
                 path_to_asjc_classification_mapping="ASJC_classification_with_levels.csv") -> None:
        self.asjc_journal_mapping: pd.DataFrame = pd.read_csv(path_to_asjc_journal_mapping)
        self.asjc_classification_mapping: pd.DataFrame = pd.read_csv(path_to_asjc_classification_mapping, delimiter=';')

    def asjcs_from(self, journal_title: str) -> Tuple[str]:
        df = self.asjc_journal_mapping
        asjcs = df.loc[df['JournalTitle'] == journal_title].iloc[0]['ASJCScopus'].split(';')
        return asjcs
    
    def classifications_from_asjcs(self, asjcs: Tuple[str]) -> Tuple[JournalClassification]:
        return tuple([self._classification_from_asjc(asjc) for asjc in asjcs])
        
    def _classification_from_asjc(self, asjc: str) -> JournalClassification:
        # reference: https://github.com/plreyes/Scopus/blob/master/ASJC%20Codes%20with%20levels.csv
        df = self.asjc_classification_mapping
        row = df.loc[df['Code'] == int(asjc)].iloc[0]
        return JournalClassification(top=row['Top'], mid=row['Middle'], low=row['Low'])


##################################################
# TEST
##################################################

# test_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
# info = WebScapper().extract(test_url)
# print(info)
test_url = 'https://www.sciencedirect.com/journal/international-journal-of-clinical-and-health-psychology/about/call-for-papers#sexuality-and-sexual-health'
info = WebScapper().extract(test_url)
print(info)

test_journal_title = "Journal of Taibah University Medical Sciences"
asjcMapper = AsjcMapper()
asjc = asjcMapper.asjcs_from(test_journal_title)
print(asjc)

classifications = asjcMapper.classifications_from_asjcs(('2700', '1201'))
print(classifications)
# print(classifications[0].top)
