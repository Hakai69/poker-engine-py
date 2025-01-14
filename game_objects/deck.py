import random

from .color import Color
from .card import Card

class Deck(list):
    default_deck = [Card(number, color) for number in range(1, 14) for color in Color]
    def __init__(self):
        super().__init__([*Deck.default_deck])
        random.shuffle(self)
        
    def deal(self) -> Card:
        '''Remove and return a card from the deck.'''
        if not self:
            raise IndexError('Cannot deal from an empty deck.')
        return self.pop()