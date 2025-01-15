from enum import Enum, auto

class Color(Enum):
    SPADES = auto()
    HEARTS = auto()
    DIAMONDS = auto()
    CLUBS = auto()
    
    def __str__(self):
        return Color._color_to_emoticon[self]
    
    def __repr__(self):
        return super().__repr__()
    
Color._color_to_emoticon = {
    Color.SPADES: '♠️',
    Color.HEARTS: '♥️',
    Color.DIAMONDS: '♦️',
    Color.CLUBS: '♣️',
}

if __name__ == '__main__':
    print(repr(Color.SPADES), str(Color.SPADES), Color.SPADES.value, sep='\t')
    print(repr(Color.HEARTS), str(Color.HEARTS), Color.HEARTS.value, sep='\t')
    print(repr(Color.DIAMONDS), str(Color.DIAMONDS), Color.DIAMONDS.value, sep='\t')
    print(repr(Color.CLUBS), str(Color.CLUBS), Color.CLUBS.value, sep='\t')