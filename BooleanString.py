from collections import namedtuple
from typing import List
import re
import datetime
import numpy as np
import spacy
from ProjectSecrets import secrets

YearRange = namedtuple('YearRange', ['start', 'end'])

class BooleanString:
    nlp = spacy.load("en_core_web_md")
    this_year = datetime.datetime.now().year
    SUPPORTED_OPERATORS = { 'TITLE-ABS-KEY', 'PUBYEAR', 'SUBJAREA', 'AND', 'OR', 'LANGUAGE','SUBJTERMS', 'EXACTKEYWORD', 'OA', 'SRCTYPE', 'IS', 'DOCTYPE', 'AFFILCOUNTRY' }
    PUNCTUATIONS = { '.', '', '/', '!', '*', '?', ','}
    STOP_WORDS = { 'title','abs','key','pubyear','subjterms','and','or','to','affilcountry','limit','or to' }

    def __init__(self, boolean_string) -> None:
        self.boolean_string = boolean_string

    def to_keywords(self, lemmatization: bool=True) -> List[str]:
        # lowercase
        keyword_list = self.boolean_string.lower()

        # Get a list of words from the boolean string
        if 'title-abs-key' in keyword_list:
            keyword_list = [x.strip() for x in keyword_list.replace('title-abs-key', '').replace('"', '').replace('(', '/').replace(')', '/').replace('affilcountry', '').replace('limit', '').replace('pubyear', '').replace('subjterms', '').replace('-', '').replace('<', '').replace('>', '').replace(',', '').split("/")]

        # remove punctuation or stop words or digits
        keyword_list = [word for word in keyword_list if (
            (word not in BooleanString.PUNCTUATIONS) and 
            (word not in BooleanString.STOP_WORDS) and
            (not word.isdigit()) and
            (not word[:4].isdigit()))]

        if lemmatization:
            keyword_list = [token.lemma_ for token in BooleanString.nlp(" ".join(keyword_list))]
        keywords = list(np.unique(keyword_list))

        return keywords
    
    def to_boolean_query(self) -> str:
        """
        Used to process a valid boolean string to a query to feed to scopus search api
        """
        uppercase_words = set()
        if re.search(r'\bPUBYEAR\b', query):
            query = re.sub(r"PUBYEAR\s*\,\s*([0-9]{4})", r"PUBYEAR IS \1", query)
        else:
            query += f" PUBYEAR > {BooleanString.this_year - 6} AND PUBYEAR < {BooleanString.this_year + 1}"
        query = re.sub(r"SUBJAREA\s*\,\s*(\"[A-Z]{4}\")", r"SUBJAREA (\1)", query)
        query = re.sub(r"LANGUAGE\s*\,\s*\"(.[^\"]*)\"", r"LANGUAGE (\1)", query)
        query = re.sub(r"DOCTYPE\s*\,\s*\"(.[^\"]*)\"", r"DOCTYPE (\1)", query)
        query = re.sub(r"(EXACT[A-Z]+)\s*\,\s*(\".[^\"]*\")", r"\1 (\2)", query)
        query = re.sub(r"([A-Z]+)\s*\,\s*\"(.[^\"]*)\"", r"\1 (\2)", query)
        query = re.sub(r"LIMIT-TO", r"", query)
        query = re.sub(r"(AND\s*|OR\s*)&\s*(AND|OR)", r"\1", query)
        
        matches = re.findall(r'\b([A-Z]+(?:-[A-Z]+)*)\b[^\"]', query)
        uppercase_words.update(matches)
        non_matching_fields = { word for word in uppercase_words if word not in BooleanQuery.SUPPORTED_OPERATORS }

        if len(non_matching_fields) > 0:
            raise RuntimeError(f"has unsupported operaters: {non_matching_fields}")

        return query


######################################################################################
# Test
######################################################################################

# keywords = '(Health Care Reform) OR (Delivery of Health Care) OR (Value-Based Health Care) OR (Telemedicine) OR (Population Health Management) OR (Organizational Efficiency) OR (Organizational Innovation) OR (Health system) OR (health transformation) OR (health services) OR (Professional Practice) OR (health sustainability) OR (Quality Indicators, Health Care)'
test_boolean_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND ( LIMIT-TO ( AFFILCOUNTRY , "Saudi Arabia" ) ) AND ( LIMIT-TO ( PUBYEAR , 2017 ) OR LIMIT-TO ( PUBYEAR , 2018 ) OR LIMIT-TO ( PUBYEAR , 2019 ) OR LIMIT-TO ( PUBYEAR , 2020 ) OR LIMIT-TO ( PUBYEAR , 2021 ) OR LIMIT-TO ( PUBYEAR , 2022 ) OR LIMIT-TO ( PUBYEAR , 2023 ) )'
# print(test_boolean_string)

query_string = BooleanString().to_boolean_query()
print(hash(test_boolean_string))
print()
print(query_string)
print()

keywords: List[str] = BooleanString(test_boolean_string).to_keywords()
print(keywords)  # ['arabia' 'care' 'delivery' 'health' 'innovation' 'management' 'organization' 'policy' 'quality' 'reform' 'saudi' 'service' 'transformation']

