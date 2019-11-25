from __future__ import annotations
from typing import Dict

from .game import Game
import bots.game as bgame
import logging

poker_bots: Dict[int, PokerBot] = {}
INITIAL_CHIPS = 500

logger = logging.getLogger(__name__)


class PokerBot:
    def __init__(self, table_id):
        self.chip = INITIAL_CHIPS
        self.table = table_id

    def react(self, game: Game, pos: int):
        logger.info("React")
        if not game.players[pos].is_playing():
            logger.info("is not playing. return")
            return
        if game.is_check_permitted(pos):
            logger.info("bot %d check", pos)
            if game.pcheck(pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {pos} check fail")
        elif game.players[pos].chip >= game.highest_bet:
            logger.info("bot %d call", pos)
            if game.pcall(pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {pos} call fail")
        else:
            logger.info("bot %d fold", pos)
            if game.pfold(pos):
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {pos} fold fail")
            else:
                bgame.send_to_channel_by_table_id(
                    self.table, f"bot {pos} fold")
