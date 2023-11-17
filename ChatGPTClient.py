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

TimeLimitWiggleResult = namedtuple('TimeLimitWiggleResult', ('start_year', 'end_year', 'worked'))

class ChatGPTClient():

    def __init__(self, 
                 api_key: str, 
                 endpoint: str) -> None:
        self.API_KEY = api_key
        self.RESOURCE_ENDPOINT = endpoint

    def boolean_string_from(self, webInfo: WebInfo) -> str:

        prompt = f"""
        title: {webInfo.title}
        description: {webInfo.description}
        asjc_codes: {webInfo.asjc_codes}
        classifications: {webInfo.classifications}
        """

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


    def keywords_from(self, title_desc_asjcs: TtlDescAsjc) -> List[str]:
        # TODO: integrate
        # https://elsevier-dev.cloud.databricks.com/?o=8907390598234411#notebook/931469551481155 
        # The last section
        # “Few shot”, The good function is get_messages4
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

chatGPTClient = ChatGPTClient()
