import pandas as pd

from WebScrapper import WebScapper, WebInfo



COLUMNS = ['ITEM_GROUP_JOURNAL_REFERENCE', 'ACRONYM', 'BU', 'SPECIAL_ISSUE_TITLE',
       'LANDING_PAGE_URL', 'ONE_LINE_SCOPE_DESCRIPTION', 'ASJC_CORE',
       'KEYWORDS', 'BOOLEAN STRING']


class SampleData:
    df = pd.read_excel('examples_for_hackathon.xlsx')  

    @staticmethod
    def sample_1() -> pd.DataFrame: 
        return SampleData.df[SampleData.df.ITEM_GROUP_JOURNAL_REFERENCE=='JTUMED_SI030181'].reset_index()
    @staticmethod
    def sample_1_web_info() -> WebInfo:
        url: str = SampleData.sample_1().loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        return web_info
        
    @staticmethod
    def sample_2() -> pd.DataFrame: 
        return SampleData.df[SampleData.df.ITEM_GROUP_JOURNAL_REFERENCE=='FOOHUM_SI028840'].reset_index()
    @staticmethod
    def sample_2_web_info() -> WebInfo:
        url: str = SampleData.sample_2().loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        return web_info
    
    @staticmethod
    def sample_3() -> pd.DataFrame: 
        return SampleData.df[SampleData.df.ITEM_GROUP_JOURNAL_REFERENCE=='MICROB_SI029657'].reset_index()
    @staticmethod
    def sample_3_web_info() -> WebInfo:
        url: str = SampleData.sample_3().loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        return web_info
    
    @staticmethod
    def sample_4() -> pd.DataFrame: 
        return SampleData.df[SampleData.df.ITEM_GROUP_JOURNAL_REFERENCE=='JRRAS_IG000014'].reset_index()
    @staticmethod
    def sample_4_web_info() -> WebInfo:
        url: str = SampleData.sample_4().loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        return web_info
    
    @staticmethod
    def negative_sample() -> pd.DataFrame: 
        return SampleData.df[SampleData.df.ITEM_GROUP_JOURNAL_REFERENCE=='HORTI_IG002597'].reset_index()

    @staticmethod
    def negative_sample_web_info() -> WebInfo:
        url: str = SampleData.negative_sample().loc[0, 'LANDING_PAGE_URL']
        web_info = WebScapper().extract(url)
        return web_info