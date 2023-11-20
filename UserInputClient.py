from typing import List
from collections import namedtuple
from dataclasses import dataclass
from DBClient import SearchEngine

from WebScrapper import WebInfo

@dataclass
class UserResponse:
    """Class for keeping track of an item in inventory."""
    accepted: bool


class UserInputClient():
    
    def are_you_happy_with(self, query: str, n_result: int, use:SearchEngine) -> UserResponse:
        query_name = "boolean string" if use == SearchEngine.BooleanSearch else "query string"
        question = f"{query}\nThere are {n_result} results.\nAre you happy with this {query_name}? (Y/N) "
        _input = input(question)
        accepted = _input.lower().startswith('y')
        return UserResponse(accepted)

##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    response = UserInputClient().are_you_happy_with("this boolean string", n_result=200, use=SearchEngine.BooleanSearch)
    print(response)
