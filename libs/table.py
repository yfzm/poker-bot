from enum import Enum
import libs.game as lgame
import threading as thread
from typing import Callable
import time
import bots.game as bgame
from typing import List, Dict
from slackapi.client import get_mentioned_string
import uuid

MAX_AWAIT = 600
INITIAL_CHIPS = 500

class PlayerStatus(Enum):
    PLAYING = 0
    FOLD = 1
    ALLIN = 2
    # OFFLINE = 3

class Player:
    def __init__(self, user: str):
        self.user = user
        self.chip = INITIAL_CHIPS
        self.chipBet = 0
        self.cards = [0] * 2
        self.active = True
        self.status = PlayerStatus.PLAYING
        self.rank = None
        self.hand = None
    
    def is_playing(self) -> bool:
        return self.status == PlayerStatus.PLAYING

    def is_fold(self) -> bool:
        return self.status == PlayerStatus.FOLD

    def is_allin(self) -> bool:
        return self.status == PlayerStatus.ALLIN

    def set_playing(self) -> None:
        self.status = PlayerStatus.PLAYING

    def set_fold(self) -> None:
        self.status = PlayerStatus.FOLD

    def set_allin(self) -> None:
        self.status = PlayerStatus.ALLIN

    def set_rank_and_hand(self, rank, hand):
        self.rank = rank
        self.hand = hand


class Table:
    def __init__(self, owner: str):
        self.uid = str(uuid.uuid4())
        self.game = lgame.Game()
        self.owner = owner
        self.players: List[Player] = []
        self.players_user2pos: Dict[str, int] = dict()
        self.countdown = MAX_AWAIT
        self.exe_pos_local = -1
        self.round_status_local = ""
        self.msg_ts = ""
        self.btn = 0
        self.ante = 20
        self.counter = 0  # number of games

    def join(self, user_id):
        """Join a table, return (pos, nplayer, err)"""
        if user_id in list(map(lambda player: player.user, self.players)):
            return -1, -1, "already in this table"
        pos = len(self.players)
        player = Player(user_id)
        self.players.append(player)
        self.players_user2pos[player.user] = pos
        # self.game.setPlayer(pos, INITIAL_CHIPS)
        # self.game.setReady(pos)
        return pos, pos + 1, None

    def start(self, user_id):
        """Start a game, return (hands, err)"""
        if user_id != self.owner:
            return None, "Failed to start, because only the one who open the table can start the game"
        # if len(players) < 2:
        #     return None, "Failed to start, because this game requires at least TWO players"
        self.game.start(self.players, self.ante, self.btn)
        hands = []
        for pos, player in enumerate(self.players):
            hands.append({
                "id": player.user,
                "hand": self.game.getCardsByPos(pos)
            })
        return hands, None

    def timer_function(self):
        while True:
            starttime = time.time()
            should_stop = self.mainloop()
            if should_stop:
                break
            elapsed_time = time.time() - starttime
            if elapsed_time < 1.0:
                time.sleep(1.0 - elapsed_time)

    def mainloop(self):
        round_status = self.game.get_round_status_name()
        exe_pos = self.game.exe_pos

        if self.countdown == 0:
            # TODO: prefer check over flod
            self.game.pfold(exe_pos)
            bgame.send_to_channel_by_table_id(
                self.uid, f"timeout: {get_mentioned_string(self.players[exe_pos].user)} fold")
            self.countdown = MAX_AWAIT
            return False

        if self.round_status_local != round_status:
            # the game has changed to the next status, while local status is behind
            # so, we should print some message
            public_cards = self.game.pub_cards
            bgame.send_to_channel_by_table_id(
                self.uid, "Enter {} stage: public cards is {}".format(round_status, public_cards))
            self.round_status_local = round_status
            self.countdown = MAX_AWAIT
            self.msg_ts, err = bgame.send_to_channel_by_table_id(
                self.uid, f"[{round_status}] wait for {get_mentioned_string(self.players[exe_pos].user)} to act (remaining {self.countdown}s)")
            if err is not None:
                raise RuntimeError  # TODO: fix later

        elif exe_pos != self.exe_pos_local:
            # the game stage is not changed, but the current active player is changed
            # we also should print some message
            self.countdown = MAX_AWAIT
            self.msg_ts, err = bgame.send_to_channel_by_table_id(
                self.uid, f"[{round_status}] wait for {get_mentioned_string(self.players[exe_pos].user)} to act (remaining {self.countdown}s)")

        else:
            # neither the game stage nor current active player are changed
            # so, we should update the message and decrease the countdown
            self.countdown -= 1
            bgame.update_msg_by_table_id(self.uid, self.msg_ts,
                f"[{round_status}] wait for {get_mentioned_string(self.players[exe_pos].user)} to act (remaining {self.countdown}s)")

        if round_status == "END":
            bgame.send_to_channel_by_table_id(self.uid, "Game Over!")
            self.show_result(self.game.result)
            return True

        self.exe_pos_local = exe_pos
        return False

    def show_result(self, result: lgame.Result):
        for player, chip in result.chip_changes.items():
            r = "win" if chip > 0 else "lose"
            bgame.send_to_channel_by_table_id(self.uid, f"{get_mentioned_string(player.name)} {r} {abs(chip)}\n")

    def check(self, user_id) -> str:
        player_pos = self.players_user2pos[user_id]
        if self.game.pcheck(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid check"

    def fold(self, user_id) -> str:
        player_pos = self.players_user2pos[user_id]
        if self.game.pfold(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid fold"

    def bet(self, user_id, chip: int) -> str:
        player_pos = self.players_user2pos[user_id]
        if self.game.praise(player_pos, chip) != 0:
            return f"{get_mentioned_string(user_id)}, invalid bet"

    def call(self, user_id) -> str:
        player_pos = self.players_user2pos[user_id]
        if self.game.pcall(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid call"

    def all_in(self, user_id) -> str:
        player_pos = self.players_user2pos[user_id]
        if self.game.pallin(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid all in"

    def get_game_info(self) -> str:
        info_str = f"{self.game.game_status.name} {self.game.get_round_status_name()}\n"
        info_str += f"btn: {self.game.btn} {get_mentioned_string(self.players[self.game.btn].user)}\n"
        info_str += f"sb: {self.game.sb} {get_mentioned_string(self.players[self.game.sb].user)}\n"
        info_str += f"bb: {self.game.bb} {get_mentioned_string(self.players[self.game.bb].user)}\n"
        info_str += f"utg: {self.game.utg} {get_mentioned_string(self.players[self.game.utg].user)}\n"
        info_str += f"exe_pos: {self.game.exe_pos} {get_mentioned_string(self.players[self.game.exe_pos].user)}\n"
        info_str += f"pub_card: {self.game.pub_cards}, last_bet {self.game.lastBet}, permitCheck {self.game.permitCheck}\n"
        for player in self.players:
            info_str += f"{get_mentioned_string(player.user)}: total_bet {player.chipBet}, cards {player.cards}, active {player.active}, status {player.status.name}\n"
        return info_str