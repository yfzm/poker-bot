from enum import Enum


class Color(Enum):
    SPADE = 0
    HEART = 1
    CLUB = 2
    DIAMOD = 3

    @classmethod
    def has(cls, ele) -> bool:
        return ele in cls._value2member_map_


class Card(object):
    _NUM2CHAR = ['Error', 'A'] + \
        [i for i in range(1, 10)] + ['T''J', 'Q', 'K']

    def __init__(self, color, num):
        if not Color.has(color) or num < 1 or num > 13:
            raise ValueError
        self.color = Color(color)
        self.num = num

    def __repr__(self):
        return f'{Card._NUM2CHAR[self.num]}{self.color.value}'

    def __str__(self):
        return f'{Card._NUM2CHAR[self.num]}{self.color.value}'
