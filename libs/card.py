class Card(object):
    _COLOR = 'shcd'
    _NUM2CHAR = 'EA23456789TJQK'

    def __init__(self, color, num):
        if color < 0 or color > 3 or num < 1 or num > 13:
            raise ValueError
        self.color = color
        self.num = num

    def __repr__(self):
        return f'{Card._NUM2CHAR[self.num]}{Card._COLOR[self.color]}'

    def __str__(self):
        return f'{Card._NUM2CHAR[self.num]}{Card._COLOR[self.color]}'
