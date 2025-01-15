import random

from .color import Color
from .card import Card

class Deck(list):
    default_deck = [Card(number, color) for number in range(1, 14) for color in Color]
    def __init__(self, *, existing_cards:list[Card] = None):
        if existing_cards is None:
            super().__init__([*Deck.default_deck])
            random.shuffle(self)
        else:
            existing_cards = set(existing_cards)
            super().__init__([card for card in Deck.default_deck if card not in existing_cards])
            random.shuffle(self)
        
    def deal(self) -> Card:
        '''Remove and return a card from the deck.'''
        if not self:
            raise IndexError('Cannot deal from an empty deck.')
        return self.pop()