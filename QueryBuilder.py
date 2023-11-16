from collections import namedtuple
import re
import datetime

YearRange = namedtuple('YearRange', ['start', 'end'])

class QueryBuilder():

    SUPPORTED_OPERATORS = { 'TITLE-ABS-KEY', 'PUBYEAR', 'SUBJAREA', 'AND', 'OR', 'LANGUAGE','SUBJTERMS', 'EXACTKEYWORD', 'OA', 'SRCTYPE', 'IS', 'DOCTYPE', 'AFFILCOUNTRY' }
    
    def __init__(self):
        self.query: str = ""
    #     self.keywords = []
    #     self.year_range: YearRange = None
    #     self.limited_locations = []  # if empty, no limit on affliated countries
    
    def boolean_string(self, query: str) -> 'QueryBuilder':
        this_year = datetime.datetime.now().year
        uppercase_words = set()
        if re.search(r'\bPUBYEAR\b', query):
            query = re.sub(r"PUBYEAR\s*\,\s*([0-9]{4})", r"PUBYEAR IS \1", query)
        else:
            query += f" PUBYEAR > {this_year - 6} AND PUBYEAR < {this_year + 1}"
        query = re.sub(r"SUBJAREA\s*\,\s*(\"[A-Z]{4}\")", r"SUBJAREA (\1)", query)
        query = re.sub(r"LANGUAGE\s*\,\s*\"(.[^\"]*)\"", r"LANGUAGE (\1)", query)
        query = re.sub(r"DOCTYPE\s*\,\s*\"(.[^\"]*)\"", r"DOCTYPE (\1)", query)
        query = re.sub(r"(EXACT[A-Z]+)\s*\,\s*(\".[^\"]*\")", r"\1 (\2)", query)
        query = re.sub(r"([A-Z]+)\s*\,\s*\"(.[^\"]*)\"", r"\1 (\2)", query)
        query = re.sub(r"LIMIT-TO", r"", query)
        query = re.sub(r"(AND\s*|OR\s*)&\s*(AND|OR)", r"\1", query)
        
        matches = re.findall(r'\b([A-Z]+(?:-[A-Z]+)*)\b[^\"]', query)
        uppercase_words.update(matches)
        non_matching_fields = { word for word in uppercase_words if word not in QueryBuilder.SUPPORTED_OPERATORS }

        if len(non_matching_fields) > 0:
            raise RuntimeError(f"has unsupported operaters: {non_matching_fields}")

        self.query = query
        
        return self
    
    # def title_abs_key(self, keyword: str) -> 'QueryBuilder':
    #     self.keywords.append(keyword)
    #     return self
    
    # def time_limit(self, range: YearRange) -> 'QueryBuilder':
    #     self.year_range = range
    #     return self
    
    # def location_limit(self, country: str | Iterable[str]) -> 'QueryBuilder':
    #     if isinstance(country, Iterable):
    #         self.limited_locations.extend(country)
    #     else:
    #         self.limited_locations.append(country)
    #     return self
    
    # def asjc_codes(self, asjcs: Iterable[str]) -> 'QueryBuilder':
    #     self.asjcs = asjcs
    #     return self

    def get_query_str(self) -> str:
        return self.query

if __name__ == "__main__":
    keywords = '(Health Care Reform) OR (Delivery of Health Care) OR (Value-Based Health Care) OR (Telemedicine) OR (Population Health Management) OR (Organizational Efficiency) OR (Organizational Innovation) OR (Health system) OR (health transformation) OR (health services) OR (Professional Practice) OR (health sustainability) OR (Quality Indicators, Health Care)'
    test_boolean_string = '( TITLE-ABS-KEY ( "health care" ) AND TITLE-ABS-KEY ( reform ) OR TITLE-ABS-KEY ( delivery ) OR TITLE-ABS-KEY ( management ) OR TITLE-ABS-KEY ( policy ) OR TITLE-ABS-KEY ( organization ) OR TITLE-ABS-KEY ( innovation ) OR TITLE-ABS-KEY ( transformation ) OR TITLE-ABS-KEY ( services ) OR TITLE-ABS-KEY ( quality ) ) AND SUBJTERMS ( 2700 OR 2713 OR 2718 OR 2719 OR 2739 OR 2904 OR 2905 OR 2911 OR 3500 OR 3600 ) AND ( LIMIT-TO ( AFFILCOUNTRY , "Saudi Arabia" ) ) AND ( LIMIT-TO ( PUBYEAR , 2017 ) OR LIMIT-TO ( PUBYEAR , 2018 ) OR LIMIT-TO ( PUBYEAR , 2019 ) OR LIMIT-TO ( PUBYEAR , 2020 ) OR LIMIT-TO ( PUBYEAR , 2021 ) OR LIMIT-TO ( PUBYEAR , 2022 ) OR LIMIT-TO ( PUBYEAR , 2023 ) )'

    query_string = QueryBuilder().boolean_string(test_boolean_string).get_query_str()
    # print(test_boolean_string)
    print(hash(test_boolean_string))
    print()
    print(query_string)
    print()

