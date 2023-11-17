from typing import List
from collections import namedtuple
from BooleanSearchClient import BooleanSearchClient
from WebScrapper import WebInfo
from ProjectSecrets import secrets
from langchain.prompts import ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import BaseOutputParser
from CommaSeparatedListOutputParser import CommaSeparatedListOutputParser
from SampleData import SampleData
from pprint import pprint

TimeLimitWiggleResult = namedtuple('TimeLimitWiggleResult', ('start_year', 'end_year', 'worked'))
TimeWindow = namedtuple('TimeWindow', ('start_year', 'end_year'))

class ChatGPTClient():

    def __init__(self, 
                 api_key: str, 
                 endpoint: str) -> None:
        self.API_KEY = api_key
        self.RESOURCE_ENDPOINT = endpoint

    def boolean_string_from(self, webInfo: WebInfo, time_window: TimeWindow = TimeWindow(2018, 2024)) -> str:
        prompt = f"""
        Your task is to create a boolean query from the information provided.
        Remember to check whether keywords should be joined with an AND operator or the OR operator.
        - title={webInfo.title},
        - keywords_list={self.keywords_from(webInfo)}, 
        - passage={webInfo.description}, 
        - time_window = from {time_window.start_year}  to {time_window.end_year}, 
        - subterms_list = {webInfo.asjc_codes}
        """

        messages=[
            {
                "role": "system", 
                "content": """You are a query expert. The user is an analyst who is trying to find documents relating to a passage. You will generate a boolean search query for the user, based off of the keywords, passage and other information that will be supplied by the user.
                    Instructions: 
                    - Generate BOOLEAN query for the user and return it to them
                    - Only answer user prompts that ask you to create a boolean query
                    - Only output boolean strings for the user
                    - ONLY return the query in your response, in the format "response: query" nothing else
                    - The user query MUST include key_words and a passage 
                        - 'time_window' and 'chained_keywords' are optional
                    - The boolean string MUST follow the format (note '*' means a section is compulsory):
                        - [KEYWORD_SECTION]* AND [SUBTERM SECTION]* AND [LIMIT_YEAR_SECTION]
                    - please see the definitions below to understand how the query sections should be constructed
                    - You will also be provided with user/system examples, please look at the carefully to see how the query is constructed in them.

                    Definitions:
                    - KEYWORD_SECTION: This part of the query contains keywords from the 'keywords_list'. Keywords can be chained with the OR & AND operators 
                        - Use AND when two keywords should be intersected during the search (get the context from the "passage" input), and use OR when it can be a union. For instance, return "TITLE-ABS-KEY ( "image processing" ) AND TITLE-ABS-KEY ( biology )" when we want results featuring image processing applied to biology, and return TITLE-ABS-KEY ( "image processing" ) OR TITLE-ABS-KEY ( biology ) if we want all results featuring image processing together with all results featuring biology
                    - If there is more than one word in the keyword entry then use quotations when structuring it (e.g. if item_1 = "hello world" this translates to: TITLE-ABS-KEY ("hello world"))
                    - If there is only one word in the keyword entry then do not use quotations when structuring it (e.g. if item_1 = "agriculture" this translates to: TITLE-ABS-KEY (agriculture))
                    - [SUBTERM_SECTION] - structure the terms given in the subterms_list , e.g.: SUBJTERMS ( term1 OR term_2 OR term_3)
                    - if 'time_window' is populated we will need to apply a time filter to ensure the query e.g.: AND PUBYEAR > year_min AND PUBYEAR < year_max. 
                    - If there is only one value in time_window then the syntax is as follows e.g. AND PUBYEAR = year_value
                    """
            },
        
            ### example 1 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(SampleData.sample_1_web_info())}, 
                    - passage={SampleData.sample_1_web_info().description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { [s.strip() for s in SampleData.sample_1().loc[0,'ASJC_CORE'].split(';')] }"""
            },
            {
                "role": "assistant", 
                "content": f"response: {SampleData.sample_1().loc[0,'BOOLEAN STRING']}"
            },
        
            ### example 2 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(SampleData.sample_2_web_info())}, 
                    - passage={SampleData.sample_2_web_info().description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { [s.strip() for s in SampleData.sample_2().loc[0,'ASJC_CORE'].split(';')] }"""
            },
            {
                "role": "assistant", 
                "content": f"response: {SampleData.sample_2().loc[0,'BOOLEAN STRING']}"
            },

            ### example 3 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(SampleData.sample_3_web_info())}, 
                    - passage={SampleData.sample_3_web_info().description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { [s.strip() for s in SampleData.sample_3().loc[0,'ASJC_CORE'].split(';')] }"""
            },
            {
                "role": "assistant", 
                "content": f"response: {SampleData.sample_3().loc[0,'BOOLEAN STRING']}"
            },


            ### example 4 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(SampleData.sample_4_web_info())}, 
                    - passage={SampleData.sample_4_web_info().description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { [s.strip() for s in SampleData.sample_4().loc[0,'ASJC_CORE'].split(';')] }"""
            },
            {
                "role": "assistant", 
                "content": f"response: {SampleData.sample_4().loc[0,'BOOLEAN STRING']}"
            },

            ### example 5 - negative sample
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                - keywords_list={  self.keywords_from(SampleData.negative_sample_web_info()) }, 
                - passage={SampleData.negative_sample_web_info().description}, 
                - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                - subterms_list = { [s.strip() for s in SampleData.negative_sample().loc[0,'ASJC_CORE'].split(';')] }
                """
            },

            {
                "role": "assistant", 
                "content": '''response: ( TITLE-ABS-KEY ( "light regulation" ) OR TITLE-ABS-KEY ( antioxidants ) OR TITLE-ABS-KEY ( light ) ) AND ( TITLE-ABS-KEY ( "horticultural plants" ) OR TITLE-ABS-KEY ( fruit ) OR TITLE-ABS-KEY ( vegetable ) ) AND SUBJTERMS ( 1108 ) AND PUBYEAR > 2022 AND PUBYEAR < 2025"'''
            },

            {
                "role": "user", 
                "content": '''You missed that combining 'light' and 'horticultural plants' should be intersected in this search, because their combinaiton gives a more relative search to the passage'''
            },

            {
                "role": "assistant", 
                "content": '''you are right. Updated response: "( TITLE-ABS-KEY ( "light regulation" ) OR TITLE-ABS-KEY ( antioxidants ) OR TITLE-ABS-KEY ( light ) ) AND ( TITLE-ABS-KEY ( "horticultural plants" ) OR TITLE-ABS-KEY ( fruit ) OR TITLE-ABS-KEY ( vegetable ) ) AND SUBJTERMS ( 1108 ) AND PUBYEAR > 2017 AND PUBYEAR < 2025'''
            },

            {
                "role": "user", 
                "content": prompt
            }
        ]

    def correct_boolean_string_from(self, wrong_boolean_string: str, 
                                    sessionID: str, 
                                    coach: BooleanSearchClient, 
                                    max_attemps=5) -> str | None:
        attempt = 0
        boolean_string = wrong_boolean_string

        while (coach.is_invalid_input(boolean_string) and 
            attempt < max_attemps):

            boolean_string = ChatGPTClient.try_correct_boolean_string_from(boolean_string, sessionID, max_attemps=5, coach=coach)
            attempt += 1

        if (attempt < max_attemps):
            return boolean_string
        
        return None if coach.is_invalid_input(boolean_string) else boolean_string


    def keywords_from(self, webInfo: WebInfo) -> List[str]:
        # TODO: integrate
        # https://elsevier-dev.cloud.databricks.com/?o=8907390598234411#notebook/931469551481155 
        # The last section
        # “Few shot”, The good function is get_messages4
        
        # TODO
        pass

    def vector_keywords(self, scraped_query: str):
        llm = AzureChatOpenAI(openai_api_key="5e2adb634b1645a893e0db84a742df6e",
                              openai_api_base="https://els-openai-hackathon-5.openai.azure.com/",
                              openai_api_type="azure", openai_api_version="2023-05-15",
                              model_name="find_authors_gpt35turbo", deployment_name="find_authors_gpt35turbo")
        #System_message
        setup_prompt = """You are an AI academic assistant. You help editors of a journal find relevant manuscripts to 
        create a special issue, which is a journal article focused on a particular research area or topic. To do this,
        your task is to take a user query (which I will provide in the next prompt) and identify key words and phrases 
        from this text, or infer your own key words or short (less than 5 words) phrases that semantically summarise 
        the query."""

        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", setup_prompt),
            ("human", scraped_query),
        ])

        messages = chat_prompt.format_messages()

        response = llm(messages=messages)

        formatted_gpt_response = CommaSeparatedListOutputParser().parse(text=response.content)

        return formatted_gpt_response

    def try_narrow_down_topic(self, boolean_string):
        pass

    def try_more_generic_topic(self, boolean_string):
        pass

######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    # chatGPTClient = ChatGPTClient()
    time_window = TimeWindow(2018, 2024)
    a = {
            "role": "user", 
            "content": f"""Your task is to create a boolean query from the information provided. 
                - keywords_list= , 
                - passage={SampleData.sample_1_web_info().description}, 
                - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                - subterms_list = { [s.strip() for s in SampleData.sample_1().loc[0,'ASJC_CORE'].split(';')] }"""
        }
    pprint(a)
    