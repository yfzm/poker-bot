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
            # print("not playing")
            return
        if game.permitCheck:
            if game.pcheck(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} check")
        elif self.chip >= game.highest_bet:
            if game.pcall(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} call")
        # elif self.chip >= game.lastBet:
        #     if game.praise(self.pos, 2 if game.lastBet == 0 else 2 * game.lastBet):
        #         bgame.send_to_channel_by_table_id(
        #             self.table, f"bot {self.pos} raise fail")
        #     else:
        #         bgame.send_to_channel_by_table_id(
        #             self.table, f"bot {self.pos} raise {game.lastBet}")
        else:
            if game.pfold(self.pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {self.pos} fold")
