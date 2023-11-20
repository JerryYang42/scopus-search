from typing import List
from collections import namedtuple
from BooleanSearchClient import BooleanSearchClient
from BooleanString import BooleanString
from WebScrapper import WebInfo, WebScapper
from langchain.prompts import ChatPromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import BaseOutputParser
from CommaSeparatedListOutputParser import CommaSeparatedListOutputParser
from SampleData import SampleData
from ProjectSecrets import Secrets
import openai
from Config import Config
from JsonIO import BooleanStringJsonIO

TimeLimitWiggleResult = namedtuple('TimeLimitWiggleResult', ('start_year', 'end_year', 'worked'))
TimeWindow = namedtuple('TimeWindow', ('start_year', 'end_year'))

class ChatGPTClient():

    def __init__(self, 
                 api_key: str = Secrets.CHATGPT_API_KEY,
                 resource_endpoint: str = Config.CHATGPT_ENDPOINT) -> None:
        self.API_KEY = api_key
        self.RESOURCE_ENDPOINT = resource_endpoint
        self.samples = SampleData()
        self.boolean_string_json_io = BooleanStringJsonIO()

    def boolean_string_from(self, web_info: WebInfo, time_window: TimeWindow = TimeWindow(2018, 2024)) -> str:
        prompt = f"""
        Your task is to create a boolean query from the information provided.
        Remember to check whether keywords should be joined with an AND operator or the OR operator.
        - title={web_info.title},
        - keywords_list={self.keywords_from(web_info)}, 
        - passage={web_info.description}, 
        - time_window = from {time_window.start_year}  to {time_window.end_year}, 
        - subterms_list = {web_info.asjc_codes}
        """
        messages_1=[
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
            } ] + [ 
        
            ### example 1 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(self.samples.get_web_info(0))}, 
                    - passage={self.samples.get_web_info(0).description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { self.samples.get_sample(0).asjc_codes }"""
            },
            {
                "role": "assistant", 
                "content": f"response: { self.samples.get_sample(0).boolean_string }"
            },
        
            ### example 2 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(self.samples.get_web_info(1))}, 
                    - passage={self.samples.get_web_info(1).description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { self.samples.get_sample(1).asjc_codes }"""
            },
            {
                "role": "assistant", 
                "content": f"response: { self.samples.get_sample(1).boolean_string }"
            },

            ### example 3 - positive sample 
            {
                "role": "user", 
                "content": f"""Your task is to create a boolean query from the information provided. 
                    - keywords_list= { self.keywords_from(self.samples.get_web_info(2))}, 
                    - passage={self.samples.get_web_info(2).description}, 
                    - time_window = from {time_window.start_year}  to {time_window.end_year}, 
                    - subterms_list = { self.samples.get_sample(2).asjc_codes }"""
            },
            {
                "role": "assistant", 
                "content": f"response: { self.samples.get_sample(2).boolean_string }"
            },


            ### example 4 - positive sample 
            {
                "role": "user", 
                "content": f"Your task is to create a boolean query from the information provided. \n"\
                           f"  - keywords_list= { self.keywords_from(self.samples.get_web_info(3))}, \n"\
                           f"  - passage={self.samples.get_web_info(3).description}, \n"\
                           f"  - time_window = from {time_window.start_year}  to {time_window.end_year}, \n"\
                           f"  - subterms_list = { self.samples.get_sample(3).asjc_codes }\n"
            },
            {
                "role": "assistant", 
                "content": f"response: { self.samples.get_sample(3).boolean_string }"
            }  ] + [ 

            ### example 5 - negative sample
            {
                "role": "user", 
                "content": f"Your task is to create a boolean query from the information provided. \n"\
                           f"  - keywords_list= { self.keywords_from(self.samples.get_negative_web_info(0)) }, \n"\
                           f"  - passage={self.samples.get_negative_web_info(0).description}, \n"\
                           f"  - time_window = from {time_window.start_year}  to {time_window.end_year}, \n"\
                           f"  - subterms_list = { self.samples.get_negative_sample(0).asjc_codes }"
            },

            {
                "role": "assistant", 
                "content": 'response: ( TITLE-ABS-KEY ( "light regulation" ) OR TITLE-ABS-KEY ( antioxidants ) OR TITLE-ABS-KEY ( light ) ) AND ( TITLE-ABS-KEY ( "horticultural plants" ) OR TITLE-ABS-KEY ( fruit ) OR TITLE-ABS-KEY ( vegetable ) ) AND SUBJTERMS ( 1108 ) AND PUBYEAR > 2022 AND PUBYEAR < 2025"'
            },

            {
                "role": "user", 
                "content": 'You missed that combining "light" and "horticultural plants" should be intersected in this search, because their combinaiton gives a more relative search to the passage'
            },

            {
                "role": "assistant", 
                "content": 'You are right. Updated response: "( TITLE-ABS-KEY ( "light regulation" ) OR TITLE-ABS-KEY ( antioxidants ) OR TITLE-ABS-KEY ( light ) ) AND ( TITLE-ABS-KEY ( "horticultural plants" ) OR TITLE-ABS-KEY ( fruit ) OR TITLE-ABS-KEY ( vegetable ) ) AND SUBJTERMS ( 1108 ) AND PUBYEAR > 2017 AND PUBYEAR < 2025'
            },

            {
                "role": "user", 
                "content": prompt
            }
        ]


        prompt = f'Your task is to create a boolean string from the input text provided. Only answer user prompts that ask you to create a boolean string. TITLE: {web_info.title}, LIST OF KEYWORDS:{self.keywords_from(web_info)}, DESCRIPTION: {web_info.description}, ASJC: {web_info.asjc_codes}.'

        message_2 = [
            {
                "role": "system", 
                "content": """You are a researcher and an expert able to generate a boolean string from an input text. This boolean string can then be used to query databases and access research publications related to the input title, list of keywords and description. 
            
            Instructions: 
            - Only answer user prompts that ask you to create a boolean string. The user query MUST include a title, a list of keywords and a general description
            - ONLY return the boolean string in your response, in the format "boolean string" nothing else
            - You will be provided with user/system examples, please look at them carefully to learn how the boolean string should be constructed.
            - Study definitions carefully to understand how boolean strings are constructed.
            - Always include a SUBJTERMS (   ) query in your answer. The codes to put in SUBJTERMS() should be equal to the user input ASJC.
            """
            },
            
            ### example 1
            {
                "role": "user", 
                "content": f"Your task is to create a boolean string from the input text provided. TITLE: {self.samples.get_web_info(0).title}, LIST OF KEYWORDS:{self.keywords_from(self.samples.get_web_info(0))}, DESCRIPTION: {self.samples.get_web_info(0).description}, ASJC: {self.samples.get_web_info(0).asjc_codes}."
            },

            {
                "role": "assistant", 
                "content": str(self.samples.get_sample(0).boolean_string)
            },

            ### example 2
            {
                "role": "user", 
                "content": f"Your task is to create a boolean string from the input text provided. TITLE: {self.samples.get_web_info(1).title}, LIST OF KEYWORDS:{self.keywords_from(self.samples.get_web_info(1))}, DESCRIPTION: {self.samples.get_web_info(1).description}, ASJC: {self.samples.get_web_info(1).asjc_codes}."
            },

            {
                "role": "assistant", 
                "content": str(self.samples.get_sample(1).boolean_string)
            },

            ### example 3
            {
                "role": "user", 
                "content": f"Your task is to create a boolean string from the input text provided. TITLE: {self.samples.get_web_info(2).title}, LIST OF KEYWORDS:{self.keywords_from(self.samples.get_web_info(2))}, DESCRIPTION: {self.samples.get_web_info(2).description}, ASJC: {self.samples.get_web_info(2).asjc_codes}."
            },

            {
                "role": "assistant", 
                "content": str(self.samples.get_sample(2).boolean_string)
            },

            ### example 4
            {
                "role": "user", 
                "content": f"Your task is to create a boolean string from the input text provided. TITLE: {self.samples.get_web_info(3).title}, LIST OF KEYWORDS:{self.keywords_from(self.samples.get_web_info(3))}, DESCRIPTION: {self.samples.get_web_info(3).description}, ASJC: {self.samples.get_web_info(3).asjc_codes}."
            },

            {
                "role": "assistant", 
                "content": str(self.samples.get_sample(3).boolean_string)
            },

            ## example of interest
            {
                "role": "user", 
                "content": prompt
            }
        ]
        openai.api_type = "azure"
        openai.api_key = self.API_KEY
        openai.api_base = self.RESOURCE_ENDPOINT
        openai.api_version = '2023-05-15'
        completion = openai.ChatCompletion.create(
            model="gpt-35-turbo-16k",
            engine='find_authors_gpt35turbo',
            messages=message_2,
            temperature=0.1
        )

        boolean_string = completion.choices[0].message["content"]
        boolean_string = boolean_string.split('response:')[-1].strip()
        
        self.boolean_string_json_io.write(boolean_string)

        return boolean_string


    def keywords_from(self, web_info: WebInfo) -> List[str]:
        
        gt0 = BooleanString(self.samples.get_sample(0).boolean_string).to_keywords()
        gt1 = BooleanString(self.samples.get_sample(1).boolean_string).to_keywords()
        gt2 = BooleanString(self.samples.get_sample(2).boolean_string).to_keywords()
        gt3 = BooleanString(self.samples.get_sample(3).boolean_string).to_keywords()
        gt4 = BooleanString(self.samples.get_sample(4).boolean_string).to_keywords()
        gt5 = BooleanString(self.samples.get_sample(5).boolean_string).to_keywords()

        prompt_user = f"Your task is to create a list of keywords from the input text provided. TITLE: {web_info.title}, DESCRIPTION: {web_info.description}."
        
        gpt_messages = [
            {
                "role": "system", 
                "content": """You are a researcher and an expert able to generate a short list of keywords from an input text. This list of keywords can then be used to query databases so it should not be too specific.
            
            Instructions: 
            - Only answer user prompts that ask you to create a list of keywords
            - Only output a list of keywords for the user
            - ONLY return the list of keywords in your response, in the format "list" nothing else
            - The user query MUST include a title, a general description
            - The list of keywords should be exhaustive and as short as possible
            - You will also be provided with user/system examples, please look at them carefully to see how the query is constructed in them.
            """
            },
            
            ### example one
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(0).title}, DESCRIPTION: {self.samples.get_web_info(0).description}."
            },

            {
                "role": "assistant", 
                "content": str(gt0)
            },
            
            ### example two - scraping url of sample 1 returns an error with new function for now
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(1).title}, DESCRIPTION: {self.samples.get_web_info(1).description}."
            },
        
            {
                "role": "assistant", 
                "content": str(gt1)
            },

            ### example three
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(2).title}, DESCRIPTION: {self.samples.get_web_info(2).description}."
            },

            {
                "role": "assistant", 
                "content": str(gt2)
            },

            ### example four
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(3).title}, DESCRIPTION: {self.samples.get_web_info(3).description}."
            },

            {
                "role": "assistant", 
                "content": str(gt3)
            },

            ### example five
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(4).title}, DESCRIPTION: {self.samples.get_web_info(4).description}."
            },

            {
                "role": "assistant", 
                "content": str(gt4)
            },

            ### example six
            {
                "role": "user", 
                "content": f"Your task is to create a list of keywords from the input text provided. TITLE: {self.samples.get_web_info(5).title}, DESCRIPTION: {self.samples.get_web_info(5).description}."
            },

            {
                "role": "assistant", 
                "content": str(gt5)
            },

            ## ex of interest
            {
                "role": "user", 
                "content": prompt_user
            }
        ]

        openai.api_type = "azure"
        openai.api_key = self.API_KEY
        openai.api_base = self.RESOURCE_ENDPOINT
        openai.api_version = '2023-05-15'
        completion = openai.ChatCompletion.create(
            model="gpt-35-turbo-16k",
            engine='find_authors_gpt35turbo',
            messages=gpt_messages,
            temperature=0.1
        )

        keywords = completion.choices[0].message["content"]
        keywords = eval(keywords)
        return keywords

    def vector_keywords(self, scraped_query: str):

        llm = AzureChatOpenAI(openai_api_key=Secrets.CHATGPT_API_KEY,
                              openai_api_base=self.RESOURCE_ENDPOINT,
                              openai_api_type="azure", openai_api_version="2023-05-15",
                              model_name="find_authors_gpt35turbo", deployment_name="find_authors_gpt35turbo")
        #System_message
        setup_prompt = """You are an AI academic assistant. You help editors of a journal find relevant manuscripts to create a special issue, which is a journal article focused on a particular research area or topic. To do this, your task is to take a user query (which I will provide in the next prompt) and identify key words and phrases from this text, or infer your own key words or short (less than 5 words) phrases that semantically summarise the query."""

        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", setup_prompt),
            ("human", scraped_query)
        ])

        messages = chat_prompt.format_messages()

        response = llm(messages=messages)

        formatted_gpt_response = CommaSeparatedListOutputParser().parse(text=response.content)

        return formatted_gpt_response


######################################################################################
# Test
######################################################################################

if __name__ == "__main__":
    # test_url = "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia"
    test_url = 'https://www.sciencedirect.com/journal/food-and-humanity/about/call-for-papers#sensory-and-consumer-evaluation-of-plant-based-animal-food-analogues'
    # test_url = "https://www.sciencedirect.com/journal/technological-forecasting-and-social-change/about/call-for-papers#how-do-climate-change-energy-transition-green-finance-and-technological-innovation-predict-the-next-technological-and-economic-cycle"
    web_info = WebScapper().extract(test_url)
    chatGPTClient = ChatGPTClient()
    time_window = TimeWindow(2017, 2023)
    boolean_string = chatGPTClient.boolean_string_from(web_info)
    print(boolean_string)
    # 'TITLE-ABS-KEY ( "complexity theory" ) OR TITLE-ABS-KEY ( "global health" ) OR TITLE-ABS-KEY ( "health administration" ) OR TITLE-ABS-KEY ( "health policy" ) OR TITLE-ABS-KEY ( "public health" ) OR TITLE-ABS-KEY ( "Saudi Arabia" ) OR TITLE-ABS-KEY ( "transformation" ) AND SUBJTERMS ( 2700 ) AND ( LIMIT-TO ( PUBYEAR , 2018 ) OR LIMIT-TO ( PUBYEAR , 2019 ) OR LIMIT-TO ( PUBYEAR , 2020 ) OR LIMIT-TO ( PUBYEAR , 2021 ) OR LIMIT-TO ( PUBYEAR , 2022 ) OR LIMIT-TO ( PUBYEAR , 2023 ) )'
    query_string = chatGPTClient.keywords_from(web_info)
    print(query_string)
    # ['health sector', 'transformation', 'Saudi Arabia', 'health policy', 'public health', 'global health', 'health administration', 'complexity theory', 'researchers', 'policy makers', 'diplomats', 'government officials', 'evidence-based', 'policies', 'regulations', 'guidelines']






# ['animal analogues', 'consumer acceptance', 'flavour attributes', 'health', 'market growth', 'nutrition', 'plant-based ingredients', 'product development', 'product quality', 'sensory attributes', 'sustainable alternatives', 'texture attributes']