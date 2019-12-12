from enum import IntEnum
from functools import wraps
import random
import threading
import logging
import uuid
import time
from itertools import groupby
from typing import List, Dict, Callable, Any

from .poker_cmp import poker7
from .player import Player
from .card import Card


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
            with self.lock:
                if self.game_status in ss:
                    return func(self, *args, **kwargs)
                return -1
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


class RoundAction:
    def __init__(self, round_status: RoundStatus, players: List[Player]):
        self.round_status = round_status
        self.actions: Dict[str, Action] = dict()
        for player in players:
            self.actions[player.userid] = Action("", 0, False)

    def add_action(self, player: Player, action: str, chip: int):
        self.actions[player.userid] = Action(action, chip)


def default_notifier(round_status: RoundStatus, stall: bool):
    pass


class Game:
    def __init__(self, notifier: Callable[[RoundStatus, bool], Any] = default_notifier):
        self.notifier = notifier
        self.players: List[Player] = []
        self.game_status: GameStatus = GameStatus.WAITING
        self.round_status: RoundStatus = None
        self.nplayers = 0
        self.deck: Deck = None
        self.btn = 0
        self.sb = 0
        self.bb = 0
        self.ante = 0
        self.exe_pos = 0
        self.next_round = 0
        self.total_pot = 0
        self.pub_cards = []
        self.highest_bet = 0
        self.mini_raise = 0
        self.last_round_bet = 0
        self.last_aggressive = 0
        self.result = Result()
        self.lock = threading.RLock()
        self.round_actions: List[RoundAction] = []
        self.id = uuid.uuid4()
        self.logger = logging.getLogger(__name__)

    def init_game(self, players: List[Player], ante: int, btn: int):
        self.players = players
        for player in self.players:
            player.init()
        self.round_actions = [RoundAction(i, self.players) for i in RoundStatus]
        self.round_status = RoundStatus.PREFLOP
        self.nplayers = len(self.players)
        self.deck = Deck()
        self.btn = btn
        self.ante = ante
        self.exe_pos = -1
        self.pub_cards = []
        self.highest_bet = 0
        self.mini_raise = 0
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

    def is_running(self):
        return self.game_status == GameStatus.RUNNING

    def force_end(self):
        self.notifier = default_notifier
        self.game_status = GameStatus.WAITING
        self.round_status = RoundStatus.END

    @status([GameStatus.WAITING])
    def start(self, players: List[Player], ante: int, btn: int):
        self.init_game(players, ante, btn)

        self.game_status = GameStatus.RUNNING

        # deal all players
        for player in self.players:
            player.cards[0] = self.deck.get_card()
            player.cards[1] = self.deck.get_card()

        # blind
        if self.nplayers == 2:
            self.sb = self.btn
        else:
            self.sb = self.find_next_active_player(self.btn)
        self.bb = self.find_next_active_player(self.sb)

        # a flag for end of one round
        self.exe_pos = self.bb
        self.next_round = self.exe_pos
        self.invoke_next_player()
        self.next_round = self.exe_pos
        self.last_aggressive = self.exe_pos

        self.put_chip(self.sb, self.ante // 2)
        self.put_chip(self.bb, self.ante)
        self.highest_bet = self.ante
        self.mini_raise = self.ante * 2

        return 0

    def find_next_active_player(self, pos):
        new_pos = (pos + 1) % self.nplayers
        while new_pos != pos:
            if self.players[new_pos].is_normal() and self.players[new_pos].is_playing():
                return new_pos
            new_pos = (new_pos + 1) % self.nplayers
        return -1

    def invoke_next_player(self):
        self.logger.debug("%s: invoke next player", self.id)
        if self.get_active_player_num() == 1:
            self.notifier(self.round_status, True)
            self.logger.debug("%s: invoke next player, player_num == 1, go to end", self.id)
            self.end()
            return

        r = self.find_next_active_player(self.exe_pos)
        self.logger.debug("%s: invoke next player, next pos %d", self.id, r)
        if r == -1:
            # all-in case
            self.pub_cards += [self.deck.get_card()
                               for _ in range(len(self.pub_cards), 5)]
            self.notifier(self.round_status, True)
            self.end()
            return

        self.logger.debug("%s: invoke next player, next round %d", self.id, self.next_round)

        if r == self.next_round:
            # enter next phase
            self.notifier(self.round_status, True)
            # FIXME: This is not elegant, but I cannot find another way to do it!
            time.sleep(1)

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
                return
            self.exe_pos = self.btn
            self.next_round = self.exe_pos
            self.invoke_next_player()
            self.last_aggressive = self.exe_pos
            self.next_round = self.exe_pos
            self.mini_raise = self.ante
        else:
            self.exe_pos = r
            self.notifier(self.round_status, False)

        # fold or allin at beginning
        if not self.players[self.next_round].is_playing():
            self.next_round = self.find_next_active_player(self.next_round)

    def flop(self):
        self.pub_cards = [self.deck.get_card() for _ in range(3)]

    def turn(self):
        self.pub_cards.append(self.deck.get_card())

    def river(self):
        self.pub_cards.append(self.deck.get_card())

    def win_pot(self, winners: List[Player], exclude_players: List[Player]):
        """Calculate how many chips the `winner` wins and set result for all players

        Args:
            winners (List[Player]): the winners, if more than one player, they split the pot.
                Note that the winners are sorted in **descending** order of their bet, which
                is crucial because we always want to deal with the main pot first
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
                hand, rank = poker7([str(i) for i in p.cards + self.pub_cards])
                p.set_rank_and_hand(rank, hand)
                if not p.is_allin():
                    self.result.type = ResultType.COMPARE
            active_players.sort(key=lambda p: p.chip_bet, reverse=False)
            active_players.sort(key=lambda p: p.rank, reverse=True)

        grouped_active_players = [list(g) for _, g in groupby(active_players, lambda x: x.rank)]

        exclude_players = []
        for winner_players in grouped_active_players:
            self.win_pot(winner_players, exclude_players)
            exclude_players.extend(winner_players)

        self.round_status = RoundStatus.END
        self.game_status = GameStatus.WAITING

    def get_active_player_num(self):
        count = 0
        for player in self.players:
            if player.is_normal() and not player.is_fold():
                count += 1
        return count

    def put_chip(self, pos, num):
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
        if pos != self.exe_pos or self.put_chip(pos, self.highest_bet - self.players[pos].chip_bet) < 0:
            return -1
        self.round_actions[self.round_status.value].add_action(
            self.players[pos], "call", self.players[pos].chip_bet - self.last_round_bet)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pfold(self, pos):
        if pos != self.exe_pos:
            return -1
        self.players[pos].set_fold()
        self.round_actions[self.round_status.value].add_action(self.players[pos], "fold", 0)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pcheck(self, pos):
        if pos != self.exe_pos or not self.is_check_permitted(pos):
            return -1
        self.round_actions[self.round_status.value].add_action(self.players[pos], "check", 0)
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def praise(self, pos, num):
        if pos != self.exe_pos:
            return -1
        cur_round_bet = self.players[pos].chip_bet - self.last_round_bet + num
        if cur_round_bet < self.mini_raise:
            return -1
        if self.put_chip(pos, num):
            return -1
        self.next_round = self.exe_pos
        self.round_actions[self.round_status.value].add_action(self.players[pos], "raise", cur_round_bet)
        diff_raise = self.players[pos].chip_bet - self.highest_bet
        self.highest_bet = self.players[pos].chip_bet
        self.mini_raise += diff_raise
        self.last_aggressive = pos
        self.invoke_next_player()
        return 0

    @status([GameStatus.RUNNING])
    def pallin(self, pos):
        if pos != self.exe_pos:
            return -1

        # does allin raise the chip?
        if self.players[pos].chip > self.highest_bet:
            diff_raise = self.players[pos].chip - self.highest_bet
            self.highest_bet = self.players[pos].chip
            self.mini_raise += diff_raise
            self.next_round = self.exe_pos
            self.last_aggressive = pos
        self.put_chip(pos, self.players[pos].get_remaining_chip())
        self.round_actions[self.round_status.value].add_action(
            self.players[pos], "all-in", self.players[pos].chip_bet - self.last_round_bet)
        self.invoke_next_player()
        return 0


class Deck(object):
    def __init__(self):
        self.deck_cards = random.sample(range(52), 52)

    def get_card(self):
        num = self.deck_cards.pop()
        return Card(num // 13, num % 13 + 1)
