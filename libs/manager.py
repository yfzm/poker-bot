from __future__ import annotations
from enum import Enum
from libs.game import Game
import threading as thread
from typing import Dict
import time
import bots.game as bgame
from typing import Dict
from slackapi.client import get_mentioned_string
from .table import Table

MAX_PLAYER = 9


class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


poker_bots: Dict[int, PokerBot] = {}


class PokerBot:
    def __init__(self, pos, chip, table):
        self.chip = chip
        self.pos = pos
        self.table = table

    def react(self, game: Game):
        if game.permitCheck:
            if game.pcheck(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check")
        elif self.chip >= game.lastBet and game.lastBet > 2:
            if game.pcall(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call")
        elif self.chip >= game.lastBet:
            if game.praise(self.pos, 2 if game.lastBet == 0 else 2 * game.lastBet):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} raise fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} raise {game.lastBet}")
        else:
            if game.pfold(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold")


class GameManager:
    def __init__(self):
        self.tables: Dict[str, Table] = dict()

    def init_status(self):
        pass

    # TODO: need to protect through lock
    def open(self, user_id):
        table = Table(user_id)
        self.tables[table.uid] = table
        return table.uid

    def join(self, table_id, user_id):
        """Join a table, return (pos, nplayer, err)"""
        table = self.tables[table_id]
        return table.join(user_id)

    # def set_ob(self, func) -> None:
    #     self.game.setOb(func)

    def start(self, table_id, user_id):
        """Start a game, return (hands, err)"""
        table = self.tables[table_id]
        # if len(players) < 2:
        #     return None, "Failed to start, because this game requires at least TWO players"
        self.add_bot_player(table_id, user_id)
        # FIXME: only for test
        thread.Thread(target=self.bot_function, args=[table_id]).start()
        return table.start(user_id)

    def continue_game(self, table_id, user_id):
        table = self.tables[table_id]
        return table.continue_game(user_id)

    def add_bot_player(self, table_id, user_id):
        for i in range(len(self.tables[table_id].players), 4):
            pos, tot, err = self.join(table_id, f"bot_player_{i}")
            assert tot > 0 and err is None
            poker_bots[i] = PokerBot(pos, 500, table_id)  # TODO: magic number
            print(f"add bot {pos}")

    def bot_function(self, table_id):
        table = self.tables[table_id]
        game = table.game
        while True:
            pos = game.exe_pos
            if pos in poker_bots:
                poker_bots[pos].react(game)
            time.sleep(1)

    def check(self, table_id, user_id) -> str:
        """Check, return err"""
        table = self.tables[table_id]
        return table.check(user_id)

    def fold(self, table_id, user_id) -> str:
        table = self.tables[table_id]
        return table.fold(user_id)

    def bet(self, table_id, user_id, chip: int) -> str:
        table = self.tables[table_id]
        return table.bet(user_id, chip)

    def call(self, table_id, user_id) -> str:
        table = self.tables[table_id]
        return table.call(user_id)

    def all_in(self, table_id, user_id) -> str:
        table = self.tables[table_id]
        return table.all_in(user_id)

    # def start_timer(self, table_id) -> None:
    #     table = self.tables[table_id]
    #     table.timer_function()

    def get_game_info(self, table_id) -> str:
        table = self.tables[table_id]
        return table.get_game_info()


gameManager = GameManager()

if __name__ == "__main__":
    pass
    # some fields of `user`
    # 'color'
    # 'deleted'
    # 'id'
    # 'is_admin'
    # 'is_app_user'
    # 'is_bot'
    # 'name'
