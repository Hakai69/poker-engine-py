from enum import Enum, auto

class Color(Enum):
    SPADES = auto()
    HEARTS = auto()
    DIAMONDS = auto()
    CLUBS = auto()

if __name__ == '__main__':
    print(Color.SPADES.value)
    print(Color.HEARTS.value)
    print(Color.DIAMONDS.value)
    print(Color.CLUBS.value)