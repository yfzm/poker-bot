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
        return table.start(user_id)

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
