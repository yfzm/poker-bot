import time
import threading as thread
import uuid
from typing import List, Dict


import libs.game as lgame
import bots.game as bgame
from slackapi.payload import get_mentioned_string, build_payload, build_info_str
from .poker_bot import PokerBot
from .player import Player

MAX_AWAIT = 600
INITIAL_CHIPS = 500
BOT_NUM = 3


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
        self.timer_thread = thread.Thread(target=self.timer_function)
        self.poker_bots: Dict[int, PokerBot] = {}

    def join(self, user_id):
        """Join a table, return (pos, nplayer, err)"""
        if user_id in list(map(lambda player: player.user, self.players)):
            return -1, -1, "already in this table"
        pos = len(self.players)
        player = Player(user_id)
        self.players.append(player)
        self.players_user2pos[player.user] = pos
        return pos, pos + 1, None

    def start(self, user_id):
        """Start a game, return (hands, err)"""
        if user_id != self.owner:
            return None, "Failed to start, because only the one who open the table can start the game"
        if len(self.players) < 2:
            return None, "Failed to start, because this game requires at least TWO players"
        self.game.start(self.players, self.ante, self.btn)
        hands = []
        for pos, player in enumerate(self.players):
            hands.append({
                "id": player.user,
                "hand": self.game.get_cards_by_pos(pos)
            })
        self.timer_thread.start()
        return hands, None

    def continue_game(self, user_id):
        self.timer_thread.join()
        self.timer_thread = thread.Thread(target=self.timer_function)
        self.btn = (self.btn + 1) % len(self.players)
        return self.start(user_id)

    def add_bot_player(self):
        pos, tot, err = self.join(f"bot_player_{len(self.players)}")
        if tot <= 0 or err is not None:
            return err
        self.poker_bots[pos] = PokerBot(pos, self.uid)
        bgame.send_to_channel_by_table_id(self.uid, f"bot {pos} has joined")
        return None

    def bot_function(self):
        game = self.game
        pos = game.exe_pos
        if pos in self.poker_bots:
            self.poker_bots[pos].react(game)

    def timer_function(self):
        while True:
            starttime = time.time()
            should_stop = self.mainloop()
            self.bot_function()
            if should_stop:
                break
            elapsed_time = time.time() - starttime
            if elapsed_time < 1.0:
                time.sleep(1.0 - elapsed_time)

    def mainloop(self):
        round_status = self.game.get_round_status_name()
        exe_pos = self.game.exe_pos

        def get_payload():
            info_list = []
            pos = self.game.sb
            while True:
                player = self.players[pos]
                if player.active and not player.is_fold():
                    action = self.game.actions[player.user]
                    m_action = action.action if action.active else ""
                    m_chip = action.chip if action.active else 0
                    info_list.append(build_info_str(player.user,
                                                    player.get_remaining_chip(),
                                                    m_action, m_chip, pos == exe_pos, self.countdown))
                if pos == self.game.btn:
                    break
                pos = (pos + 1) % self.game.nplayers
            return build_payload(self.game.pub_cards, self.game.total_pot, self.game.ante,
                                 self.players[self.game.btn].user, info_list)

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
            self.round_status_local = round_status
            self.countdown = MAX_AWAIT
            # if exe_pos == self.exe_pos_local:
            self.msg_ts, err = bgame.send_to_channel_by_table_id(
                self.uid, blocks=get_payload())
            if err is not None:
                raise RuntimeError  # TODO: fix later

        elif exe_pos != self.exe_pos_local:
            # the game stage is not changed, but the current active player is changed
            # we also should print some message
            self.countdown = MAX_AWAIT
            self.msg_ts, err = bgame.send_to_channel_by_table_id(
                self.uid, blocks=get_payload())

        else:
            # neither the game stage nor current active player are changed
            # so, we should update the message and decrease the countdown
            self.countdown -= 1
            bgame.update_msg_by_table_id(
                self.uid, self.msg_ts, blocks=get_payload())

        if round_status == "END":
            bgame.send_to_channel_by_table_id(self.uid, "Game Over!")
            self.game.result.execute()
            self.show_result(self.game.result)
            return True

        self.exe_pos_local = exe_pos
        return False

    def show_result(self, result: lgame.Result):
        for player, chip in result.chip_changes.items():
            r = "win" if chip >= 0 else "lose"
            bgame.send_to_channel_by_table_id(
                self.uid, f"{get_mentioned_string(player.user)} {r} {abs(chip)}, current chip: {player.chip}\n")

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
        info_str += f"next_round: {self.game.next_round} {get_mentioned_string(self.players[self.game.next_round].user)}\n"
        info_str += f"pub_card: {self.game.pub_cards}, highest_bet {self.game.highest_bet}\n"
        for pos, player in enumerate(self.players):
            info_str += f"{get_mentioned_string(player.user)}: chip {player.chip}, \
                        total_bet {player.chipBet}, cards {player.cards}, "
            info_str += f"can_check {self.game.is_check_permitted(pos)}, active {player.active}, status {player.status.name}, "
            info_str += f"rank {player.rank}, hand {player.hand}\n"
        return info_str
