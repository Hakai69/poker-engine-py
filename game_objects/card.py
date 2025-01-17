from typing import Self

from .color import Color

number_to_str = {
    1: 'A',
    11: 'J',
    12: 'Q',
    13: 'K'
}

class Card:
    '''A card in a deck of cards.'''
    def __init__(self, number: int, color: Color):
        '''Create a new card with the given number and color.'''
        self.number = number
        self.color = color
        
    def __eq__(self, other: Self):
        return isinstance(other, Card) and self.number == other.number and self.color == other.color
    
    def __hash__(self):
        return hash((self.number, self.color))
    
    def __str__(self):
        return f'{number_to_str.get(self.number, self.number)}{self.color}'
    
    def __repr__(self):
        return f'Card({self.number}, {repr(self.color)})'