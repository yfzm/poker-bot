from enum import IntEnum
from functools import wraps
from .card import Card
from .poker_cmp import poker7
import random
from typing import List, Dict
from .player import Player
import threading
import logging
import uuid


class GameStatus(IntEnum):
    WAITING = 1
    RUNNING = 2


class RoundStatus(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END = 4


class ResultType(IntEnum):
    COMPARE = 0
    ALL_FOLD = 1
    ALL_IN = 2


def status(ss):
    def dec(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.lock.acquire()
            ret = -1
            if self.game_status in ss:
                ret = func(self, *args, **kwargs)
            self.lock.release()
            return ret
        return wrapper
    return dec


class Result:
    def __init__(self):
        self.type: ResultType = ResultType.ALL_FOLD
        self.chip_changes: Dict[Player, int] = dict()

    def add_result(self, player: Player, chip: int):
        self.chip_changes[player] = chip

    def win_bet(self, player: Player, chip: int):
        self.chip_changes[player] += chip

    def lose_bet(self, player: Player, chip: int):
        self.chip_changes[player] -= chip

    def execute(self):
        for player, chip in self.chip_changes.items():
            player.chip += chip

    def should_show_hand(self) -> bool:
        return self.type != ResultType.ALL_FOLD


class Action:
    def __init__(self, action: str, chip: int, active=True):
        self.action = action
        self.chip = chip
        self.active = active

    def set_disabled(self):
        self.active = False


class Game(object):
    def __init__(self):
        self.players: List[Player] = []
        self.game_status: GameStatus = GameStatus.WAITING
        self.round_status: RoundStatus = None
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
        self.highest_bet = 0
        self.last_round_bet = 0
        self.last_aggressive = 0
        self.result = Result()
        self.lock = threading.RLock()
        self.actions: Dict[str, Action] = dict()
        self.id = uuid.uuid4()
        self.logger = logging.getLogger(__name__)

    def init_game(self, players: List[Player], ante: int, btn: int):
        self.players = players
        self.actions.clear()
        for player in self.players:
            player.init()
            self.actions[player.userid] = Action("", 0, False)
        self.round_status = RoundStatus.PREFLOP
        self.nplayers = len(self.players)
        self.deck = Deck()
        self.btn = btn
        self.ante = ante
        self.exe_pos = -1
        self.pub_cards = []
        self.highest_bet = 0
        self.last_round_bet = 0
        self.last_aggressive = 0
        self.result = Result()
        self.total_pot = 0

    def get_cards_by_pos(self, pos):
        player = self.players[pos]
        return player.cards

    def get_round_status_name(self):
        if self.round_status:
            return self.round_status.name
        else:
            return ""

    def get_exe_pos(self):
        return self.exe_pos

    @status([GameStatus.WAITING])
    def start(self, players: List[Player], ante: int, btn: int):
        self.init_game(players, ante, btn)

        self.game_status = GameStatus.RUNNING

        # deal all players
        for player in self.players:
            player.cards[0] = self.deck.get_card()
            player.cards[1] = self.deck.get_card()

        # blind
        self.sb = self.find_next_active_player(self.btn)
        self.bb = self.find_next_active_player(self.sb)
        self.utg = self.find_next_active_player(self.bb)

        # a flag for end of one round
        self.exe_pos = self.utg
        self.next_round = self.utg

        self.put_chip(self.sb, self.ante // 2, 'SB')
        self.put_chip(self.bb, self.ante, 'BB')
        self.highest_bet = self.ante

        return 0

    def find_next_active_player(self, pos):
        new_pos = (pos + 1) % self.nplayers
        while not(self.players[new_pos].is_normal() and self.players[new_pos].is_playing()):
            if new_pos == pos:
                return -1
            new_pos = (new_pos + 1) % self.nplayers

        return new_pos if new_pos != pos else -1

    def invoke_next_player(self):
        self.logger.debug("%s: invoke next player", self.id)
        if self.get_active_player_num() == 1:
            self.logger.debug("%s: invoke next player, player_num == 1, go to end", self.id)
            self.end()
            return

        r = self.find_next_active_player(self.exe_pos)
        self.logger.debug("%s: invoke next player, next pos %d", self.id, r)
        if r == -1:
            # all-in case
            self.pub_cards += [self.deck.get_card()
                               for i in range(len(self.pub_cards), 5)]
            self.end()
            return

        self.logger.debug("%s: invoke next player, next round %d", self.id, self.next_round)

        self.exe_pos = r
        if r == self.next_round:
            # enter next phase
            self.round_status = RoundStatus(self.round_status.value + 1)
            self.last_round_bet = self.highest_bet
            if self.round_status == RoundStatus.FLOP:
                self.flop()
            elif self.round_status == RoundStatus.TURN:
                self.turn()
            elif self.round_status == RoundStatus.RIVER:
                self.river()
            elif self.round_status == RoundStatus.END:
                self.end()
            for player in self.players:
                self.actions[player.userid].set_disabled()
            self.exe_pos = self.sb
            self.next_round = self.sb
            self.last_aggressive = self.sb
        # fold or allin at beginning
        if not self.players[self.next_round].is_playing():
            self.next_round = self.find_next_active_player(self.next_round)

    def flop(self):
        self.pub_cards = [self.deck.get_card() for i in range(3)]

    def turn(self):
        self.pub_cards.append(self.deck.get_card())

    def river(self):
        self.pub_cards.append(self.deck.get_card())

    def win_pot(self, winners: List[Player], exclude_players: List[Player]):
        """Calculate how many chips the `winner` wins and set result for all players

        Args:
            winners (List[Player]): the winners, if more than one player, they split the pot.
                Note that the winners are sorted in **descending** order of their bet, which
                is crucial beacause we always want to deal with the main pot first
            exclude_players (List[Player]): players in this list will not lose chips
                to `winner`, because they have a bigger hand
        """
        n_winners = len(winners)
        for player in self.players:
            if player in winners or player in exclude_players:
                continue
            for winner in winners:
                could_win = min(player.chip_bet, winner.chip_bet)
                self.result.win_bet(winner, could_win // n_winners)
                self.result.lose_bet(player, could_win // n_winners)
                player.chip_bet -= could_win

    def end(self):
        # Initialize self.result
        for player in self.players:
            self.result.add_result(player, 0)
        self.result.type = ResultType.ALL_FOLD

        active_players: List[Player] = list(
            filter(lambda p: p.is_normal() and not p.is_fold(), self.players))
        if len(active_players) == 0:
            raise RuntimeError("No active player?")

        # Only when there are more than two active players, comparision is needed
        if len(active_players) >= 2:
            self.result.type = ResultType.ALL_IN
            for p in active_players:
                hand, rank = poker7(
                    list(map(lambda card: str(card), p.cards + self.pub_cards)))
                p.set_rank_and_hand(rank, hand)
                if not p.is_allin():
                    self.result.type = ResultType.COMPARE
            active_players.sort(key=lambda p: p.chip_bet, reverse=False)
            active_players.sort(key=lambda p: p.rank, reverse=True)

        winner_players = []
        exclude_players = []
        last_rank = active_players[0].rank
        for p in active_players:
            if p.rank == last_rank:
                winner_players.append(p)
            else:
                self.win_pot(winner_players, exclude_players)
                exclude_players += winner_players.copy()
                winner_players = [p]
                last_rank = p.rank
        self.win_pot(winner_players, exclude_players)

        self.round_status = RoundStatus.END
        self.game_status = GameStatus.WAITING

    def get_active_player_num(self):
        count = 0
        for player in self.players:
            if player.is_normal() and not player.is_fold():
                count += 1
        return count

    def put_chip(self, pos, num, action):
        player = self.players[pos]
        remaining_chip = player.get_remaining_chip()
        if remaining_chip < num:
            return -1
        if remaining_chip == num:
            player.set_allin()
        player.chip_bet += num
        self.total_pot += num
        return 0

    def is_check_permitted(self, pos):
        return self.players[pos].chip_bet >= self.highest_bet

    @status([GameStatus.RUNNING])
    def pcall(self, pos):
        if pos != self.exe_pos or self.put_chip(pos, self.highest_bet - self.players[pos].chip_bet, 'CALL') < 0:
            return -1
        self.actions[self.players[pos].userid] = Action(
            "call", self.players[pos].chip_bet - self.last_round_bet)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pfold(self, pos):
        if pos != self.exe_pos:
            return -1
        self.players[pos].set_fold()
        self.actions[self.players[pos].userid] = Action("fold", 0)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pcheck(self, pos):
        if pos != self.exe_pos or not self.is_check_permitted(pos):
            return -1
        self.actions[self.players[pos].userid] = Action("check", 0)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def praise(self, pos, num):
        # TODO: check valid raise: the diff is bigger than the last diff
        if pos != self.exe_pos:
            return -1

        self.next_round = self.exe_pos
        self.put_chip(pos, num, 'RAISE')
        self.actions[self.players[pos].userid] = Action(
            "raise", self.players[pos].chip_bet - self.last_round_bet)
        self.highest_bet = self.players[pos].chip_bet
        self.last_aggressive = pos
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pallin(self, pos):
        if pos != self.exe_pos:
            return -1

        # does allin raise the chip?
        if self.players[pos].chip > self.highest_bet:
            self.highest_bet = self.players[pos].chip
            self.next_round = self.exe_pos
            self.last_aggressive = pos
        self.put_chip(pos, self.players[pos].get_remaining_chip(), 'ALLIN')
        self.actions[self.players[pos].userid] = Action(
            "all-in", self.players[pos].chip_bet - self.last_round_bet)
        self.invoke_next_player()
        return 0

    def getJSON(self):
        return 'temp'


class Deck(object):
    def __init__(self):
        self.deck_cards = list(range(0, 52))
        self.shuffle()

    def get_card(self):
        num = self.deck_cards[self.i]
        card = Card(int(num / 13), num % 13 + 1)
        self.i = self.i + 1
        return card

    def shuffle(self):
        random.shuffle(self.deck_cards)
        self.i = 0
