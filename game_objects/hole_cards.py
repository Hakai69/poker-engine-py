from typing import Collection

from .card import Card
from .color import Color

class HoleCards(frozenset):
    '''Your hole cards in a game of Texas Hold'em, also known as pocket hands or
    private cards.'''
    def __init__(self, cards: Collection[Card]):
        if len(cards) != 2:
            raise ValueError(f'Hole cards must amount to 2 cards not {len(cards)}')
        super().__new__(frozenset, cards)

    def __str__(self) -> str:
        return 'Hole cards: ' + ' & '.join(map(str, self))

    def __repr__(self) -> str:
        return f'HoleCards({str(list(self))})'
    
    def color_count(self, color: Color) -> int:
        '''Return the number of cards in the hand with the given color.'''
        return sum(card.color == color for card in self)
    
    