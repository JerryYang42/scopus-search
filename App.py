from typing import List
import pandas as pd
from dataclasses import dataclass

from ChatGPTClient import ChatGPTClient
from BooleanSearchClient import BooleanSearchClient
from VectorSearchClient import VectorSearchClient
from UserInputClient import UserInputClient, UserResponse
from WebScrapper import WebScapper, WebInfo
from DBClient import DBClient, QuerySource, QueryStatus
from ProjectSecrets import secrets
from Config import Config

class App():
    """
    This app is to help finding authors for special issues
    """
    def __init__(self) -> None:
        self.chatGPT = ChatGPTClient(secrets.CHATGPT_API_KEY, Config.CHATGPT_ENDPOINT)
        self.booleanSearchClient = BooleanSearchClient(secrets.BOOLEAN_SEARCH_API_KEY, secrets.BOOLEAN_SEARCH_INST_TOKEN)
        self.vectorSearchClient = VectorSearchClient()
        self.userInput = UserInputClient()
        self.dbClient = DBClient()

    def start(self, landing_page_url: str, use: str = "BooleanSearch") -> None:
        """
        :param url: url of landing page for the special issue
        :param use: specify which modle to use, can be "BooleanSearch" or "VectorSearch"
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
        (boolean_string, sessionID) = self.chatGPT.boolean_string_from(webInfo)

        # SKIPPABLE: try improve
        if use_try_improve:
            result: ImproveResult = self._try_improve_boolean_string(boolean_string)
            boolean_string = result.boolean_string
        
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

        # SKIPPABLE: try improve
        if use_try_improve:
            result: ImproveResult = self._try_improve_keywords(keywords)

        # retrive all authors
        all_authors: pd.DataFrame = self.vectorSearchClient.retrieve_top_entries(keywords)

    def _try_improve_keywords(self, keywords: str) -> 'ImproveResult':
        # init flags for loops
        _undecided_on_boolean_string: bool = True

        while _undecided_on_boolean_string:
            # roughly evaluate the query by the number of results
            n_results = self.vectorSearchClient.num_results_from(keywords)
            # if relevancy is cheap to calculate, maybe we can do it here?
            if n_results > 20_000:
                # TODO: refine logic
                self.vectorSearchClient.try_limit_to_recent()
                # TODO: add human intervention?
                # if search has done its best, let ChatGPT come up with new keywords
                keywords = self.chatGPT.try_narrow_down_topic(keywords)
            elif n_results < 5_000:
                # TODO: refine logic
                self.vectorSearchClient.try_loosen_time_limit()
                # TODO: add human intervention?
                # if search has done its best, let ChatGPT come up with new keywords
                keywords = self.chatGPT.try_more_generic_topic(keywords)
            else:
                # TODO: display selected keywords and its metrics
                response: UserResponse = (input("Are you happy with this keywords? \n{keywords} (Y/N)").lower().startswith('Y'))
                if response.accepted:
                    _undecided_on_boolean_string = False; continue
                else:
                    exit()

    def _try_improve_boolean_string(self, boolean_string: str) -> 'ImproveResult':
        """
        let chat-GPT and search engine to improve the boolean string
        """
        _undecided_on_boolean_string = True
        while _undecided_on_boolean_string:
            # validate boolean string, if invalid, let ChatGPT try a few attempts;    
            if self.booleanSearchClient.is_invalid_input(boolean_string):
                boolean_string = ChatGPTClient.try_correct_boolean_string_from(boolean_string, sessionID, max_attemps=5, coach=self.booleanSearchClient)
                self.dbClient.add_boolean_string(boolean_string, QuerySource.chatGPT)
            # if ChatGPT cannot fix, exit process
            if boolean_string is None:  
                raise RuntimeError("ChatGPT cannot give a valid boolean string. exit process")

            # roughly evaluate the query by the number of results
            n_results = self.booleanSearchClient.num_results(boolean_string)
            if n_results > 20_000:
                # TODO: refine logic
                result = self.booleanSearchClient.try_limit_to_recent(boolean_string)
                if result.worked:  # boolean search had a solution
                    continue
                # TODO: add human intervention?
                # if search has done its best, let ChatGPT come up with new boolean string
                boolean_string = self.chatGPT.try_narrow_down_topic(boolean_string)
            elif n_results < 5_000:
                # TODO: refine logic
                result = self.booleanSearchClient.try_loosen_time_limit(boolean_string)
                if result.worked:  # boolean search had a solution
                    continue
                # TODO: add human intervention?
                # if search has done its best, let ChatGPT come up with new boolean string
                boolean_string = self.chatGPT.try_more_generic_topic(boolean_string)
            else:
                # display selected boolean string and its metrics

                # What's a good boolean string?
                # - decent number of results
                # - decent number of authors
                # - don't miss out essential papers
                #    - top 10 (citations, publishYear)
                # - covers decent range of year
                response: UserResponse = UserInputClient.are_you_happy_with(boolean_string)
                if response.accepted:
                    _undecided_on_boolean_string = False
                else:  # user rejected
                    exit()


@dataclass
class ImproveResult:
    boolean_string: str
    should_try: bool

######################################################################################
# Test
######################################################################################

landing_page_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
App().start(landing_page_url, use="BooleanSearch")
# App().start(landing_page_url, use="VectorSearch")

