from __future__ import annotations
from enum import Enum
from libs.game import Game
import threading as thread
from typing import Dict
import time
import bots.game as bgame
from typing import List
from slackapi.client import get_mentioned_string


class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


class Table():
    def __init__(self, game: Game, owner: str):
        self.game = game
        self.owner = owner
        self.players = []
        self.countdown = MAX_AWAIT
        self.wait_on_pos = -1
        self.cur_round = ""
        self.msg_ts = ""


MAX_PLAYER = 9
MAX_AWAIT = 15
INITIAL_CHIPS = 500

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
        self.tables: List[Table] = []

    def init_status(self):
        pass

    # TODO: need to protect through lock
    def open(self, user_id):
        self.tables.append(Table(Game.build(MAX_PLAYER), user_id))

        return len(self.tables) - 1

    def join(self, table_id, user_id):
        """Join a table, return (pos, nplayer, err)"""
        assert table_id < len(self.tables)
        table = self.tables[table_id]
        game = table.game
        players = table.players
        if user_id in players:
            return -1, -1, "already in this table"
        pos = len(players)
        players.append(user_id)
        game.setPlayer(pos, INITIAL_CHIPS)
        game.setReady(pos)
        bgame.send_to_channel_by_table_id(table_id, f"{user_id} has joined game")
        return pos, pos + 1, None

    # def set_ob(self, func) -> None:
    #     self.game.setOb(func)

    def start(self, table_id, user_id):
        """Start a game, return (hands, err)"""
        table = self.tables[table_id]
        if user_id != table.owner:
            return None, "Failed to start, because only the one who open the table can start the game"
        game = table.game
        players = table.players
        # if len(players) < 2:
        #     return None, "Failed to start, because this game requires at least TWO players"
        self.add_bot_player(table_id, user_id)
        game.start()
        hands = []
        for pos, player in enumerate(players):
            hands.append({
                "id": player,
                "hand": game.getCardsByPos(pos)
            })
        # FIXME: only for test
        thread.Thread(target=self.bot_function, args=[table_id]).start()
        return hands, None

    def add_bot_player(self, table_id, user_id):
        for i in range(len(self.tables[table_id].players), 4):
            pos, tot, err = self.join(table_id, f"bot_player_{i}")
            assert tot > 0
            poker_bots[i] = PokerBot(pos, INITIAL_CHIPS, table_id)
            print(f"add bot {pos}")

    def bot_function(self, table_id):
        table = self.tables[table_id]
        game = table.game
        while True:
            pos = game.exe_pos
            if pos in poker_bots:
                poker_bots[pos].react(game)
            time.sleep(1)

    def timer_function(self, table_id):
        while True:
            starttime = time.time()
            should_stop = self.mainloop(table_id)
            if should_stop:
                break
            eclipse_time = time.time() - starttime
            if eclipse_time < 1.0:
                time.sleep(1.0 - eclipse_time)

    def mainloop(self, table_id):
        table = self.tables[table_id]
        game = table.game
        players = table.players
        # countdown = table.countdown
        round_status = game.get_round_status_name()
        exe_pos = game.exe_pos

        # if round_status == "END":
        #     return True

        if table.countdown == 0:
            # TODO: prefer check over flod
            game.pfold(exe_pos)
            bgame.send_to_channel_by_table_id(
                table_id, f"timeout: {get_mentioned_string(players[exe_pos])} fold")
            table.countdown = MAX_AWAIT
            return False

        if table.cur_round != round_status:
            public_cards = game.pub_cards
            bgame.send_to_channel_by_table_id(
                table_id, "Enter {} stage: public cards is {}".format(round_status, public_cards))
            table.cur_round = round_status
            table.countdown = MAX_AWAIT
            table.msg_ts, err = bgame.send_to_channel_by_table_id(
                table_id, f"[{round_status}] wait for {get_mentioned_string(players[exe_pos])} to act (remaining {table.countdown}s)")
            if err is not None:
                raise RuntimeError  # TODO: fix later

        elif exe_pos == table.wait_on_pos:
            table.countdown -= 1
            err = bgame.update_msg_by_table_id(table_id, table.msg_ts,
                                               f"[{round_status}] wait for {get_mentioned_string(players[exe_pos])} to act (remaining {table.countdown}s)")

        if round_status == "END":
            bgame.send_to_channel_by_table_id(table_id, "Game Over!")
            return True

        table.wait_on_pos = exe_pos
        return False

    # TODO: need to protect through lock

    def check(self, table_id, user_id) -> bool:
        game = self.tables[table_id].game
        player_pos = self.tables[table_id].players.index(user_id)
        return game.pcheck(player_pos) == 0

    def fold(self, table_id, user_id) -> bool:
        game = self.tables[table_id].game
        player_pos = self.tables[table_id].players.index(user_id)
        return game.pfold(player_pos) == 0

    def bet(self, table_id, user_id, chip: int) -> bool:
        game = self.tables[table_id].game
        player_pos = self.tables[table_id].players.index(user_id)
        return game.praise(player_pos, chip) == 0

    def call(self, table_id, user_id) -> bool:
        game = self.tables[table_id].game
        player_pos = self.tables[table_id].players.index(user_id)
        return game.pcall(player_pos) == 0

    def all_in(self, table_id, user_id) -> bool:
        game = self.tables[table_id].game
        player_pos = self.tables[table_id].players.index(user_id)
        return game.pallin(player_pos) == 0


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
