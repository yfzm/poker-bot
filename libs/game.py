from enum import IntEnum
from functools import wraps
from .card import Card
from .pokerCmp import poker7
import random

status_names = ["PREFLOP", "FLOP", "TURN", "RIVER", "END"]


class GameStatus(IntEnum):
    WAITFORPLAYERREADY = 1
    RUNNING = 2
    CONTINUING = 3


class RoundStatus(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END = 4


def status(ss):
    def dec(func):
        def wrapper(self, *args, **kwargs):
            if self.game_status in ss:
                return func(self, *args, **kwargs)
            # TODO: using exception or error to handle this
            return -1
        return wrapper
    return dec


class Game(object):
    def __init__(self):
        self.max_player = 0
        self.players = []
        self.game_status: GameStatus = None
        self.players_num = 0
        self.deck: Deck = None
        self.btn = 0
        self.ante = 0
        self.exe_pos = 0
        self.pub_cards = []

    @staticmethod
    def build(max_player):
        g = Game()
        assert max_player > 1
        g.max_player = max_player
        g.players = [Player(i) for i in range(max_player)]
        g.game_status = GameStatus.WAITFORPLAYERREADY
        g.players_num = 0
        g.deck = Deck()
        g.btn = -1
        g.ante = 20
        g.exe_pos = -1
        g.pub_cards = []
        return g

    def getCardsByPos(self, pos):
        player = self.players[pos]
        return player.cards

    def get_round_status_name(self):
        return status_names[int(self.roundStatus)]

    def get_exe_pos(self):
        return self.exe_pos

    @status([GameStatus.WAITFORPLAYERREADY])
    def setPlayer(self, pos, chip):
        player = self.players[pos]
        # is occupied ?
        if player.active:
            return -1

        player.active = True
        player.chip = chip
        self.players_num = self.players_num + 1
        return 0

    @status([GameStatus.WAITFORPLAYERREADY])
    def setReady(self, pos):
        player = self.players[pos]

        if player.active:
            player.ready = True
            return 0
        return -1

    @status([GameStatus.WAITFORPLAYERREADY, GameStatus.CONTINUING])
    def start(self):
        for i in range(0, self.max_player):
            if (self.players[i].active != self.players[i].ready):
                return -1
        # all the players are ready
        self.game_status = GameStatus.RUNNING
        self.roundStatus = RoundStatus.PREFLOP

        # deal all players
        for player in self.players:
            player.cards[0] = self.deck.getCard()
            player.cards[1] = self.deck.getCard()

        # blind
        self.btn = self.findNextActivePlayer(self.btn)
        self.sb = self.findNextActivePlayer(self.btn)
        self.bb = self.findNextActivePlayer(self.sb)
        self.utg = self.findNextActivePlayer(self.bb)

        # a flag for end of one round
        self.exe_pos = self.utg
        self.nextRound = self.bb

        self.putChip(self.sb, self.ante / 2, 'SB')
        self.putChip(self.bb, self.ante, 'BB')
        self.lastBet = self.ante
        self.permitCheck = False

        return 0

    def findNextActivePlayer(self, pos):
        pos += 1
        count = 0
        while(self.players[pos].active == False or self.players[pos].fold or self.players[pos].allin):
            pos = (pos + 1) % self.max_player
            count += 1

            # nobody can do action
            if (count > self.max_player):
                return -1
        return pos

    def invokeNextPlayer(self):
        r = self.findNextActivePlayer(self.exe_pos)
        if r == -1:
            self.gend()
        else:
            self.exe_pos = r

        # touch the bound
        if self.roundStatus != RoundStatus.END and self.exe_pos == self.nextRound:
            if self.roundStatus == RoundStatus.PREFLOP:
                self.flop()
            elif self.roundStatus == RoundStatus.FLOP:
                self.turn()
            elif self.roundStatus == RoundStatus.TURN:
                self.river()
            elif self.roundStatus == RoundStatus.RIVER:
                self.end()
            self.roundStatus = RoundStatus(self.roundStatus.value + 1)
            self.lastBet = 0
            # sb first
            self.exe_pos = self.sb

    def gend(self):
        # continue round until end
        self.roundStatus
        if self.roundStatus.value < RoundStatus.FLOP.value:
            self.flop()
        if self.roundStatus.value < RoundStatus.TURN.value:
            self.turn()
        if self.roundStatus.value < RoundStatus.RIVER.value:
            self.river()
        if self.roundStatus.value < RoundStatus.END.value:
            self.end()

    def flop(self):
        self.pub_cards = [self.deck.getCard() for i in range(3)]

    def turn(self):
        self.pub_cards.append(self.deck.getCard())

    def river(self):
        self.pub_cards.append(self.deck.getCard())

    def end(self):
        players = []
        for p in self.players:
            if p.active:
                p.chip = p.chip - p.chipBet
                if p.fold == False:
                    p.setRank(self.pub_cards)
                    players.append(p)

        def take_rank(p):
            return p.rank
        players.sort(key=take_rank, reverse=True)
        self.roundStatus = RoundStatus.END
        self.game_status = GameStatus.CONTINUING

    def get_active_player_num(self):
        count = 0
        for player in self.players:
            if player.active and player.fold == False:
                count += 1
        return count

    def putChip(self, pos, num, action):
        player = self.players[pos]
        if player.chip < num:
            return -1
        # allin
        elif player.chip == num:
            player.allin = True
            action = 'ALLIN'
        player.chipBet = num
        return 0

    @status([GameStatus.RUNNING])
    def pbet(self, pos, num):
        if (pos != self.exe_pos or num < self.ante or self.lastBet != 0):
            return -1

        self.putChip(pos, num, 'BET')
        self.lastBet = num
        self.permitCheck = True
        self.invokeNextPlayer()
        return 0

    @status([GameStatus.RUNNING])
    def pcall(self, pos):
        if pos != self.exe_pos or self.putChip(pos, self.lastBet, 'CALL') < 0:
            return -1
        self.invokeNextPlayer()
        return 0

    @status([GameStatus.RUNNING])
    def pfold(self, pos):
        if (pos != self.exe_pos):
            return -1
        self.players[pos].fold = True

        # end of a game
        if self.get_active_player_num() == 1:
            self.end()
        else:
            self.invokeNextPlayer()
        return 0

    @status([GameStatus.RUNNING])
    def pcheck(self, pos):
        if (pos != self.exe_pos or self.permitCheck == False):
            return -1
        self.invokeNextPlayer()
        return 0

    @status([GameStatus.RUNNING])
    def praise(self, pos, num):
        if (pos != self.exe_pos or num < self.lastBet * 2):
            return -1

        self.nextRound = self.exe_pos
        self.lastBet = num
        self.permitCheck = False
        self.putChip(pos, num, 'RAISE')
        self.invokeNextPlayer()
        return 0

    @status([GameStatus.RUNNING])
    def pallin(self, pos):
        if (pos != self.exe_pos):
            return -1

        # does allin raise the chip?
        if self.lastBet < self.players[pos].chip:
            self.nextRound = self.exe_pos
            self.lastBet = self.players[pos].chip
        self.permitCheck = False
        self.putChip(pos, self.players[pos].chip, 'ALLIN')
        self.invokeNextPlayer()
        return 0

    def getJSON(self):
        return 'temp'


class Player(object):
    def __init__(self, pos):
        self.chip = 0
        self.chipBet = 0
        self.cards = [0] * 2
        self.active = False  # join a game
        self.ready = False
        self.fold = False
        self.allin = False
        self.pos = pos

    def setRank(self, pubCards):
        def cardToStr(card):
            return str(card)
        maxRank = poker7(map(cardToStr, self.cards + pubCards))
        self.rank = maxRank['rank']
        self.hand = maxRank['hand']


class Deck(object):
    def __init__(self):
        self.deckCards = list(range(0, 52))
        self.shuffle()

    def getCard(self):
        num = self.deckCards[self.i]
        card = Card(int(num / 13), num % 13 + 1)
        self.i = self.i + 1
        return card

    def shuffle(self):
        random.shuffle(self.deckCards)
        self.i = 0
