from enum import IntEnum
from functools import wraps
from .card import Card
from .pokerCmp import poker7
import random
from typing import List, Dict
from .player import Player, PlayerStatus


class GameStatus(IntEnum):
    WAITING = 1
    RUNNING = 2


class RoundStatus(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END = 4


def status(ss):
    def dec(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.game_status in ss:
                return func(self, *args, **kwargs)
            # TODO: using exception or error to handle this
            return -1
        return wrapper
    return dec


class Result:
    def __init__(self):
        self.chip_changes: Dict[Player, int] = dict()

    def add_result(self, player: Player, chip: int):
        self.chip_changes[player] = chip

    def win_bet(self, player: Player, chip: int):
        self.chip_changes[player] += chip

    def lose_bet(self, player: Player, chip: int):
        self.chip_changes[player] -= chip


class Game(object):
    def __init__(self):
        self.players: List[Player] = []
        self.game_status: GameStatus = GameStatus.WAITING
        self.roundStatus: RoundStatus = None
        self.nplayers = 0
        self.deck: Deck = None
        self.btn = 0
        self.sb = 0
        self.bb = 0
        self.utg = 0
        self.ante = 0
        self.exe_pos = 0
        self.total_pot = 0
        self.pub_cards = []
        self.lastBet = 0
        self.result = Result()
        self.permitCheck = False

    def init_game(self, players: List[Player], ante: int, btn: int):
        self.players = players
        # self.game_status = GameStatus.WAITFORPLAYERREADY
        self.roundStatus = RoundStatus.PREFLOP
        self.nplayers = len(self.players)
        self.deck = Deck()
        self.btn = btn
        self.ante = ante
        self.exe_pos = -1
        self.pub_cards = []
        self.total_pot = 0

    def getCardsByPos(self, pos):
        player = self.players[pos]
        return player.cards

    def get_round_status_name(self):
        return self.roundStatus.name

    def get_exe_pos(self):
        return self.exe_pos

    @status([GameStatus.WAITING])
    def start(self, players: List[Player], ante: int, btn: int):
        self.init_game(players, ante, btn)
        # for i in range(0, self.max_player):
        #     if (self.players[i].active != self.players[i].ready):
        #         return -1
        # all the players are ready
        self.game_status = GameStatus.RUNNING

        # deal all players
        for player in self.players:
            player.cards[0] = self.deck.getCard()
            player.cards[1] = self.deck.getCard()

        # blind
        # self.btn = self.findNextActivePlayer(self.btn)
        self.sb = self.findNextActivePlayer(self.btn)
        self.bb = self.findNextActivePlayer(self.sb)
        self.utg = self.findNextActivePlayer(self.bb)

        # a flag for end of one round
        self.exe_pos = self.utg
        self.nextRound = self.utg

        self.putChip(self.sb, self.ante / 2, 'SB')
        self.putChip(self.bb, self.ante, 'BB')
        self.lastBet = self.ante
        self.permitCheck = False

        return 0

    def findNextActivePlayer(self, pos):
        pos = (pos + 1) % self.nplayers
        count = 0
        while(self.players[pos].active == False or not self.players[pos].is_playing()):
            pos = (pos + 1) % self.nplayers
            count += 1

            # nobody can do action
            if (count > self.nplayers):
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
            self.permitCheck = True
            # sb first
            self.exe_pos = self.sb
            self.nextRound = self.sb

    def gend(self):
        # continue round until end
        self.permitCheck = True
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

    def win_pot(self, winner: Player, exclude_players: List[Player]):
        """Calculate how many chips the `winner` wins and set result for all players

        Args:
            winner (Player): the winner
            exclude_players (List[Player]): players in this list will not lose chips
                to `winner`, because they have a bigger hand
        """
        total_win = 0
        for player in self.players:
            if player == winner or player in exclude_players:
                continue
            could_win = min(player.chipBet, winner.chipBet)
            total_win += could_win
            self.result.lose_bet(player, could_win)
            player.chipBet -= could_win
        self.result.win_bet(winner, total_win)

    def end(self):
        # Initialize self.result
        for player in self.players:
            self.result.add_result(player, 0)
        
        active_players: List[Player] = list(filter(lambda p: p.active and not p.is_fold(), self.players))
        if len(active_players) == 0:
            raise RuntimeError("No active player?")

        # Only when there are more than two active players, comparision is needed
        if len(active_players) >= 2:
            for p in active_players:
                rank, hand = poker7(map(lambda card: str(card), p.cards + self.pub_cards))
                p.set_rank_and_hand(rank, hand)
            active_players.sort(key=lambda p: p.rank, reverse=True)

        exclude_players = []
        for p in active_players:
            self.win_pot(p, exclude_players)
            exclude_players.append(p)

        # self.roundStatus = RoundStatus.END
        self.game_status = GameStatus.WAITING

    def get_active_player_num(self):
        count = 0
        for player in self.players:
            if player.active and not player.is_fold():
                count += 1
        return count

    def putChip(self, pos, num, action):
        player = self.players[pos]
        if player.chip < num:
            return -1
        # allin
        elif player.chip == num:
            player.set_allin()
            action = 'ALLIN'
        player.chipBet = num
        self.total_pot += num
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
        self.players[pos].set_fold()

        # end of a game
        if self.get_active_player_num() == 1:
            self.end()
            self.roundStatus = RoundStatus.END
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


# class Player(object):
#     def __init__(self, pos):
#         self.chip = 0
#         self.chipBet = 0
#         self.cards = [0] * 2
#         self.active = False  # join a game
#         self.ready = False
#         self.fold = False
#         self.allin = False
#         self.pos = pos

#     def setRank(self, pubCards):
#         def cardToStr(card):
#             return str(card)
#         maxRank = poker7(map(cardToStr, self.cards + pubCards))
#         self.rank = maxRank['rank']
#         self.hand = maxRank['hand']


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
