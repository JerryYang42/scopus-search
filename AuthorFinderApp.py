from typing import List
import pandas as pd
from dataclasses import dataclass

from ChatGPTClient import ChatGPTClient, TimeWindow
from BooleanSearchClient import BooleanSearchClient
from VectorSearchClient import VectorSearchClient
from UserInputClient import UserInputClient, UserResponse
from WebScrapper import WebScapper, WebInfo
from DBClient import DBClient, QuerySource, QueryStatus, SearchEngine
from ProjectSecrets import Secrets
from Config import Config

class AuthorFinderApp():
    """
    This app is to help finding authors for special issues
    """
    def __init__(self) -> None:
        self.chatGPT = ChatGPTClient(Secrets.CHATGPT_API_KEY, 
                                     Config.CHATGPT_ENDPOINT)
        self.booleanSearchClient = BooleanSearchClient(Secrets.BOOLEAN_SEARCH_API_KEY, 
                                                       Secrets.BOOLEAN_SEARCH_INST_TOKEN)
        self.vectorSearchClient = VectorSearchClient()
        self.dbClient = DBClient(Config.DB_FILENAME)

    def start(self, landing_page_url: str, use: SearchEngine = SearchEngine.BooleanSearch) -> None:
        """
        :param url: url of landing page for the special issue
        :param use: specify which search engine to use
        """
        webInfo: WebInfo = WebScapper().extract(landing_page_url)  # asjc might be read from csv

        if use == "BooleanSearch":
            self._boolean_search(webInfo)
        if use == "VectorSearch":
            self._vector_search(webInfo)
        
    def _boolean_search(self, webInfo: WebInfo, use_try_improve=False) -> None:
        """
        :param webInfo: info scrapped from landing page and other knowledge from csv
        :param use_try_improve: if False, only make one-shot; 
                                if True, let BooleanSearch and ChatGPT try a few attempts
        """
        # init boolean string
        boolean_string = self.chatGPT.boolean_string_from(webInfo)
        
        # validate boolean string. If invalid, exit
        if self.booleanSearchClient.is_invalid_input(boolean_string):
            raise RuntimeError("ChatGPT cannot give a valid boolean string. exit process")

        # retrive all authors
        all_authors: pd.DataFrame = self.booleanSearchClient.retrieve_top_entries(boolean_string,
                                                                              n_top_entries=50,
                                                                              dbClient=self.dbClient)

    def _vector_search(self, webInfo: WebInfo, use_try_improve=False) -> None:
        """
        :param webInfo: info scrapped from landing page and other knowledge from csv
        :param use_try_improve: if False, only make one-shot; 
                                if True, let VectorSesearch and ChatGPT try a few attempts
        """
        # init vector search keywords
        keywords: List[str] = self.chatGPT.keywords_from(webInfo)

        # retrive all authors
        all_authors: pd.DataFrame = self.vectorSearchClient.retrieve_top_entries(keywords)


@dataclass
class ImproveResult:
    boolean_string: str
    should_try: bool

######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    landing_page_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
    AuthorFinderApp().start(landing_page_url, use="BooleanSearch")
    AuthorFinderApp().start(landing_page_url, use="VectorSearch")

    # test_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
    # web_info = WebScapper().extract(test_url)
    # chatGPTClient = ChatGPTClient()
    # time_window = TimeWindow(2017, 2023)
    # boolean_string = chatGPTClient.boolean_string_from(web_info)
    # booleanSearchClient = BooleanSearchClient(secrets.BOOLEAN_SEARCH_API_KEY, secrets.BOOLEAN_SEARCH_INST_TOKEN)
    # is_invalid = booleanSearchClient.is_invalid_input(boolean_string)
    # assert not is_invalid 
    # dbClient = DBClient()
    # booleanSearchClient.retrieve_top_entries(boolean_string, 20, dbClient)
    
