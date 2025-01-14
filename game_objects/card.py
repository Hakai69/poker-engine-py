from typing import Self

from .color import Color

class Card:
    '''A card in a deck of cards.'''
    def __init__(self, number: int, color: Color):
        '''Create a new card with the given number and color.'''
        self.number = number
        self.color = color
        
    def __eq__(self, other: Self):
        return self.number == other.number and self.color == other.color
    
    def __hash__(self):
        return hash((self.number, self.color))
    
    def __str__(self):
        return f'{self.number} of {self.color.name.lower()}'
    
    def __repr__(self):
        return f'Card({self.number}, Color.{self.color.name})'