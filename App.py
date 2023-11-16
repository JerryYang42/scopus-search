from typing import List
import pandas as pd

from ChatGPTClient import ChatGPTClient
from BooleanSearchClient import BooleanSearchClient
from VectorSearchClient import VectorSearchClient
from UserInputClient import UserInputClient
from WebScrapper import WebScapper, TtlDescAsjc
from DBClient import DBClient

class App():
    """
    This app is to help finding authors for special issues
    """
    def __init__(self) -> None:
        self.chatGPT = ChatGPTClient()
        self.booleanSearchClient = BooleanSearchClient()
        self.vectorSearchClient = VectorSearchClient()
        self.userInput = UserInputClient()
        self.dbClient = DBClient()

    def start(self, url: str, use: str = "BooleanSearch") -> None:
        """
        :param url: url of landing page for the special issue
        :param use: specify which modle to use, can be "BooleanSearch" or "VectorSearch"
        """
        title_desc_asjcs: TtlDescAsjc = WebScapper().extract(landing_page_url)  # asjc might be read from csv

        if use == "BooleanSearch":
            self._boolean_search(title_desc_asjcs)
        if use == "VectorSearch":
            self.__vector_search(title_desc_asjcs)
        
    def _boolean_search(self, title_desc_asjcs: TtlDescAsjc) -> None:
        # init flags for loops
        _undecided_on_boolean_string: bool = True

        # init boolean string
        (boolean_string, sessionID) = self.chatGPT.boolean_string_from(title_desc_asjcs)

        while _undecided_on_boolean_string:
            # validate boolean string, if invalid, let ChatGPT try a few attempts;    
            if self.booleanSearchClient.is_invalid_input(boolean_string):
                boolean_string = ChatGPTClient.try_correct_boolean_string_from(boolean_string, sessionID, max_attemps=5, coach=booleanSearchClient)
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
                is_happy = (input("Are you happy with this boolean string? \n{boolean_str} (Y/N)").lower().startswith('Y'))
                if is_happy:
                    _undecided_on_boolean_string = False
                else:
                    exit()


        # retrive all authors
        NUM_THREADS = 6
        all_authors: pd.DataFrame = self.booleanSearchClient.retrieve_all_authors(boolean_string, num_threads=NUM_THREADS)

        # evaluation
        # TODO

    def _vector_search(self, title_desc_asjcs: TtlDescAsjc) -> None:
        # TODO

        # init flags for loops
        _undecided_on_boolean_string: bool = True

        # init vector search keywords
        keywords: List[str] = self.chatGPT.keywords_from(title_desc_asjcs)

        while _undecided_on_boolean_string:
            # roughly evaluate the query by the number of results
            n_results = self.vectorSearchClient.num_results(keywords)
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
                is_happy = (input("Are you happy with this keywords? \n{keywords} (Y/N)").lower().startswith('Y'))
                if is_happy:
                    _undecided_on_boolean_string = False
                else:
                    exit()


        # retrive all authors
        NUM_THREADS = 6
        all_authors: pd.DataFrame = self.vectorSearchClient.retrieve_all_authors(boolean_string, num_threads=NUM_THREADS)


######################################################################################
# Test
######################################################################################

landing_page_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
App().start(landing_page_url, use="BooleanSearch")
# App().start(landing_page_url, use="VectorSearch")

