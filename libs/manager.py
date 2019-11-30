from __future__ import annotations
from enum import Enum
from typing import Dict
from .table import Table
from .storage import Storage
import logging

MAX_PLAYER = 9


class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


class GameManager:
    def __init__(self):
        print("gamemanager")
        self.logger = logging.getLogger(__name__)
        self.tables: Dict[str, Table] = dict()
        self.storage = Storage('PokerGame.dat')

    def init_status(self):
        pass

    # TODO: need to protect through lock
    def open(self, user_id: str):
        table = Table(user_id, self.storage)
        self.tables[table.uid] = table
        return table.uid

    def join(self, table_id, user_id, username):
        """Join a table, return (pos, total_chip, table_chip, err)"""
        table = self.tables[table_id]
        return table.join(user_id, username)

    def leave(self, table_id, user_id):
        """Leave a table, return (nplayer, err)"""
        table = self.tables[table_id]
        return table.leave(user_id)

    def start(self, table_id, user_id):
        """Start a game, return (hands, err)"""
        table = self.tables[table_id]
        return table.start(user_id)

    def continue_game(self, table_id, user_id):
        table = self.tables[table_id]
        return table.continue_game(user_id)

    def add_bot(self, table_id):
        table = self.tables[table_id]
        return table.add_bot_player()

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

    def get_game_info(self, table_id) -> str:
        table = self.tables[table_id]
        return table.get_game_info()

    def login(self, user_id) -> str:
        self.storage.create_user(user_id, 500)
        return None

    def gain_chip(self, user_id) -> str:
        err = self.storage.change_user_chip(user_id, 500)
        return err

    def show_chip(self, user_id) -> (int, str):
        chips, err = self.storage.fetch_user_chip(user_id)
        if err is not None:
            return 0, err
        return chips, None


gameManager = GameManager()

if __name__ == "__main__":
    pass
