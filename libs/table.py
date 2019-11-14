from enum import Enum
from libs.game import Game
import threading as thread
from typing import Callable
import time
import bots.game as bgame
from typing import List
from slackapi.client import get_mentioned_string
import uuid

MAX_AWAIT = 15
INITIAL_CHIPS = 500


class Table():
    def __init__(self, game: Game, owner: str):
        self.uid = str(uuid.uuid4())
        self.game = game
        self.owner = owner
        self.players = []
        self.countdown = MAX_AWAIT
        self.wait_on_pos = -1
        self.cur_round = ""
        self.msg_ts = ""

    def join(self, user_id):
        """Join a table, return (pos, nplayer, err)"""
        if user_id in self.players:
            return -1, -1, "already in this table"
        pos = len(self.players)
        self.players.append(user_id)
        self.game.setPlayer(pos, INITIAL_CHIPS)
        self.game.setReady(pos)
        return pos, pos + 1, None

    def start(self, user_id):
        """Start a game, return (hands, err)"""
        if user_id != self.owner:
            return None, "Failed to start, because only the one who open the table can start the game"
        # if len(players) < 2:
        #     return None, "Failed to start, because this game requires at least TWO players"
        self.game.start()
        hands = []
        for pos, player in enumerate(self.players):
            hands.append({
                "id": player,
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
                self.uid, f"timeout: {get_mentioned_string(players[exe_pos])} fold")
            self.countdown = MAX_AWAIT
            return False

        if self.cur_round != round_status:
            public_cards = self.game.pub_cards
            bgame.send_to_channel_by_table_id(
                self.uid, "Enter {} stage: public cards is {}".format(round_status, public_cards))
            self.cur_round = round_status
            self.countdown = MAX_AWAIT
            self.msg_ts, err = bgame.send_to_channel_by_table_id(
                self.uid, f"[{round_status}] wait for {get_mentioned_string(players[exe_pos])} to act (remaining {self.countdown}s)")
            if err is not None:
                raise RuntimeError  # TODO: fix later

        elif exe_pos == self.wait_on_pos:
            self.countdown -= 1
            err = bgame.update_msg_by_table_id(self.uid, self.msg_ts,
                                               f"[{round_status}] wait for {get_mentioned_string(players[exe_pos])} to act (remaining {self.countdown}s)")

        if round_status == "END":
            bgame.send_to_channel_by_table_id(self.uid, "Game Over!")
            return True

        self.wait_on_pos = exe_pos
        return False

    def check(self, user_id) -> str:
        player_pos = self.players.index(user_id)
        if self.game.pcheck(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid check"

    def fold(self, user_id) -> str:
        player_pos = self.players.index(user_id)
        if self.game.pfold(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid fold"

    def bet(self, user_id, chip: int) -> str:
        player_pos = self.players.index(user_id)
        if self.game.praise(player_pos, chip) != 0:
            return f"{get_mentioned_string(user_id)}, invalid bet"

    def call(self, user_id) -> str:
        player_pos = self.players.index(user_id)
        if self.game.pcall(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid call"

    def all_in(self, user_id) -> str:
        player_pos = self.players.index(user_id)
        if self.game.pallin(player_pos) != 0:
            return f"{get_mentioned_string(user_id)}, invalid all in"
