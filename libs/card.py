from enum import Enum
class Color(Enum):
    SPADE = 0
    HEART = 1
    CLUB = 2
    DIAMOD = 3

class Card(object):
    def __init__(self, color, num):
        if color == 0:
            self.color = 's'
        elif color == 1:
            self.color = 'h'
        elif color == 2:
            self.color = 'c'
        elif color == 3:
            self.color = 'd'
        
        if num == 1:
            self.num = 'A'
        elif num == 10:
            self.num = 'T'
        elif num == 11:
            self.num = 'J'
        elif num == 12:
            self.num = 'Q'
        elif num == 13:
            self.num = 'K'
        else:
            self.num = num

    def __repr__(self):
        return '{}{}'.format(self.num, self.color)
    def __str__(self):
        return '{}{}'.format(self.num, self.color)


