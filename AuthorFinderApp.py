from typing import List

from ChatGPTClient import ChatGPTClient, TimeWindow
from BooleanSearchClient import BooleanSearchClient
from JsonIO import BooleanStringJsonIO, SiBooleanStringMappingJsonIO, VectorQueryJsonIO
from VectorSearchClient import VectorSearchClient
from UserInputClient import UserInputClient, UserResponse
from WebScrapper import WebScapper, WebInfo
from DBClient import DBClient, SearchEngine
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
        self.scrapper = WebScapper()
        self.userInput = UserInputClient()
        self.boolean_string_json_io = BooleanStringJsonIO()
        self.siid_boolean_string_mapping_json_io = SiBooleanStringMappingJsonIO()
        self.vector_query_json_io = VectorQueryJsonIO()
        self.quiet = False

    def start(self, landing_page_url: str, 
              use: SearchEngine = SearchEngine.BooleanSearch, 
              ask_before_retrieval: bool = False, 
              n_top_entries: int = 20_000,
              quiet: bool = False) -> None:
        """
        :param url: url of landing page for the special issue. Required.
        :param use: specify which search engine to use. Default Boolean Search
        :param ask_before_retrieval: specify if the user is happy to proceed with
          the generated query. Default False
          If true, user will be prompted a question and expected an input to proceed;
          If false, it will use the generated query to fetch top n results. 
        :param top_n_results: number of top results user what to retrieve. Default 500
        """
        self.quiet = quiet
        if not self.quiet: 
            print(f"Finding author for url: {landing_page_url}")
        web_info: WebInfo = self.scrapper.extract(landing_page_url)

        if use == "BooleanSearch":
            self._boolean_search(web_info, landing_page_url, ask_before_retrieval, n_top_entries)
        if use == "VectorSearch":
            self._vector_search(web_info, landing_page_url, ask_before_retrieval, n_top_entries, landing_page_url=landing_page_url)
        
    def _boolean_search(self, web_info: WebInfo, 
                        landing_page_url: str,
                        ask_before_retrieval: bool = False, 
                        n_top_entries: int = 20_000,
                        ) -> None:
        """
        :param web_info: info scrapped from landing page and other knowledge from csv
        :param ask_before_retrieval: specify if the user is happy to proceed with
          the generated query. Default False
          If true, user will be prompted a question and expected an input to proceed;
          If false, it will use the generated query to fetch top n results. 
        :param top_n_results: number of top results user what to retrieve. Default 500
        """
        # init boolean string
        boolean_string = self.chatGPT.boolean_string_from(web_info)
        self.siid_boolean_string_mapping_json_io.write(landing_page_url, boolean_string)
        if not self.quiet: 
            print("ChatGPT conceived a boolean string for you ...")
        
        # validate boolean string. If invalid, exit
        if self.booleanSearchClient.is_invalid_input(boolean_string):
            if not self.quiet: 
                print("ChatGPT cannot give a valid boolean string. exit process")
            raise RuntimeError(f"the generated Boolean string is invalid:\n{boolean_string}")
        
        # if user what to decide if we want to proceed with the query and store all the result
        user_response: UserResponse = UserResponse(accepted=False)
        if ask_before_retrieval:
            n_result = self.booleanSearchClient.num_results(boolean_string)
            user_response = self.userInput.are_you_happy_with(boolean_string, n_result, use=SearchEngine.BooleanSearch)
        if (ask_before_retrieval) and (not user_response.accepted):
            if not self.quiet: 
                print("You are not happy with the boolean. exit process")
            raise RuntimeError()
        if not ask_before_retrieval:
            if not self.quiet: 
                print(f"Boolean string: \n{boolean_string}")

        # retrieve entries
        if not self.quiet: 
            print("Retrieving results for you ...")
        self.booleanSearchClient.retrieve_top_entries(boolean_string,
                                                      n_top_entries=n_top_entries,
                                                      dbClient=self.dbClient)
        
        # display result
        filename = self.boolean_string_json_io._filename_from(boolean_string)
        if not self.quiet: 
            print(f"Saved to {Config.BOOLEAN_STRING_OUTPUT_FOLDER}/{filename}.")
        n_results = self.boolean_string_json_io.get_total_results(boolean_string)
        n_authors = len(self.boolean_string_json_io.get_auids(boolean_string))
        if not self.quiet: 
            print(f"Got {n_results} results, {n_authors} authors.")


    def _vector_search(self, web_info: WebInfo, 
                       landing_page_url: str,
                       ask_before_retrieval: bool = False, 
                       n_top_entries=20_000) -> None:
        """
        :param web_info: info scrapped from landing page and other knowledge from csv
        """
        # init vector search keywords
        query_keywords: List[str] = self.chatGPT.keywords_from(web_info)
        query_string = ", ".join(query_keywords)
        if not self.quiet: 
            print("ChatGPT conceived a query string for you ...")

        # if user what to decide if we want to proceed with the query and store all the result
        user_response: UserResponse = UserResponse(accepted=False)
        if ask_before_retrieval:
            n_result = self.vectorSearchClient.num_results(query_string)
            user_response = self.userInput.are_you_happy_with(query_string, n_result, use=SearchEngine.VectorSearch)
        if (ask_before_retrieval) and (not user_response.accepted):
            if not self.quiet: 
                print("You are not happy with the query string. exit process")
            raise RuntimeError()
        if not ask_before_retrieval:
            if not self.quiet: 
                print(f"Query string: \n{query_string}")

        # retrieve entries
        if not self.quiet: 
            print("Retrieving results for you ...")
        self.vectorSearchClient.retrieve_top_entries(query_string, n_top_entries=n_top_entries)
        
        # display result
        filename = self.vector_query_json_io._filename_from(query_string)
        n_results = self.vector_query_json_io.get_total_results(query_string)
        n_authors = len(self.vector_query_json_io.get_auids(query_string))
        if not self.quiet: 
            print(f"Got {n_results} results, {n_authors} authors. Saved to {Config.VECTOR_QUERY_OUTPUT_FOLDER}/{filename}.")


######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    # landing_page_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
    # AuthorFinderApp().start(landing_page_url, use="BooleanSearch")
    # AuthorFinderApp().start(landing_page_url, use="VectorSearch")

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
    
    urls = ['https://www.sciencedirect.com/journal/international-journal-of-clinical-and-health-psychology/about/call-for-papers#sexuality-and-sexual-health', 'https://www.sciencedirect.com/journal/food-and-humanity/about/call-for-papers#sensory-and-consumer-evaluation-of-plant-based-animal-food-analogues', 'https://www.sciencedirect.com/journal/applied-energy/about/call-for-papers#thermoacoustics-combustion-and-energy-conversion-systems', 'https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia']
    app = AuthorFinderApp()
    for url in urls:
        app.start(landing_page_url=url, 
                    use=SearchEngine.BooleanSearch, 
                    n_top_entries=20, 
                    ask_before_retrieval=False,
                    quiet=False)
