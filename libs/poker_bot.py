from __future__ import annotations
from typing import Dict

from .game import Game
import bots.game as bgame

poker_bots: Dict[int, PokerBot] = {}
INITIAL_CHIPS = 500


class PokerBot:
    def __init__(self, pos, table_id):
        self.chip = INITIAL_CHIPS
        self.pos = pos
        self.table = table_id

    def react(self, game: Game):
        if not game.players[self.pos].is_playing():
            return
        if game.is_check_permitted(self.pos):
            if game.pcheck(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check")
        elif game.players[self.pos].chip >= game.highest_bet:
            if game.pcall(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call")
        else:
            if game.pfold(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold")
