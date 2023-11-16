from typing import List
from collections import namedtuple
from BooleanSearchClient import BooleanSearchClient
from WebScrapper import WebInfo
from ProjectSecrets import secrets

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


    def try_narrow_down_topic(self, boolean_string):
        pass

    def try_more_generic_topic(self, boolean_string):
        pass

######################################################################################
# Test
######################################################################################

chatGPTClient = ChatGPTClient()