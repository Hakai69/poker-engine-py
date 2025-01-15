from enum import Flag, auto

from typing import Self

class ActionType(Flag):
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    RAISE = auto()
    MUCK = auto()
    SHOW = auto()
    
    def __str__(self):
        return self.name.lower()
    
class Action:

    def __init__(self, type: ActionType, value: int | None = None):
        self.type = type
        self.value = value
        
    def __eq__(self, other: Self):
        return self.type == other.type and self.value == other.value
        
    def __hash__(self):
        return hash((self.type, self.value))
    
    @staticmethod
    def from_string(raw_action: str) -> Self:
        elements = raw_action.split(' ')
        if len(elements) == 1:
            return Action(ActionType.from_string(elements[0]), None)
        return Action(ActionType.from_string(elements[0]), int(elements[1]))