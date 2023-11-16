import requests
from collections import namedtuple
from bs4 import BeautifulSoup
import pandas as pd
from typing import List

JournalClassification = namedtuple('JournalClassification', ('top', 'mid', 'low'))

# title: str
# description: str
# asjcs: List[JournalClassification]
TtlDescAsjc = namedtuple('TtlAbsAsjc', ('title', 'description', 'asjcs'))

# resource: https://realpython.com/beautiful-soup-web-scraper-python/

class WebScapper():
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    def __init__(self) -> None:
        self.asjcMapper = AsjcMapper()

    def extract(self, url: str) -> str:

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
        asjc_codes = self.asjcMapper.asjcs_from(journal_title=journal_title)
        journal_classifications = self.asjcMapper.classifications_from_asjcs(asjc_codes)
        title = soup.find('div', class_='date').find_next_sibling().text
        description = soup.find_all('p', string="Special issue information:")[0].find_next_sibling().text

        return TtlDescAsjc(title, description, asjcs=journal_classifications)


class AsjcMapper():
    def __init__(self, 
                 path_to_asjc_journal_mapping="ASJC_journals.csv", 
                 path_to_asjc_classification_mapping="ASJC_classification_with_levels.csv") -> None:
        self.asjc_journal_mapping: pd.DataFrame = pd.read_csv(path_to_asjc_journal_mapping)
        self.asjc_classification_mapping: pd.DataFrame = pd.read_csv(path_to_asjc_classification_mapping, delimiter=';')

    def asjcs_from(self, journal_title: str) -> List[str]:
        df = self.asjc_journal_mapping
        asjcs = df.loc[df['JournalTitle'] == journal_title].iloc[0]['ASJCScopus'].split(';')
        return asjcs
    
    def classifications_from_asjcs(self, asjcs: List[str]) -> List[JournalClassification]:
        return [self._classification_from_asjc(asjc) for asjc in asjcs]
        
    def _classification_from_asjc(self, asjc: str) -> JournalClassification:
        # reference: https://github.com/plreyes/Scopus/blob/master/ASJC%20Codes%20with%20levels.csv
        df = self.asjc_classification_mapping
        row = df.loc[df['Code'] == int(asjc)].iloc[0]
        return JournalClassification(top=row['Top'], mid=row['Middle'], low=row['Low'])



# test_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
# info = WebScapper().extract(test_url)
# print(info)

test_journal_title = "Journal of Taibah University Medical Sciences"
asjcMapper = AsjcMapper()
asjc = asjcMapper.asjcs_from(test_journal_title)
print(asjc)

classifications = asjcMapper.classifications_from_asjcs(['2700', '1201'])
print(classifications)
print(classifications[0].top)
