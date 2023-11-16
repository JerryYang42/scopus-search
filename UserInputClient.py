from typing import List
from collections import namedtuple
from dataclasses import dataclass

@dataclass
class UserResponse:
    """Class for keeping track of an item in inventory."""
    accepted: bool


class UserInputClient():
    
    def are_you_happy_with(self, boolean_string: str) -> UserResponse:
        _input = input(f"Are you happy with this boolean string? (Y/N)\n\n{boolean_string}\n\n")
        accepted = _input.lower().startswith('y')
        return UserResponse(accepted)


##############################################################
# TEST
##############################################################

response = UserInputClient().are_you_happy_with("this boolean string")
print(response)
