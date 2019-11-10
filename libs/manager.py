from enum import Enum
from libs.game import Game
import threading as thread
from typing import Callable
import time
import bots.game as bgame

class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


MAX_PLAYER = 9
MAX_AWAIT = 15
INITIAL_CHIPS = 500

class GameManager:
    def __init__(self):
        self.tables = []
        self.player_id2pos = {}

    def init_status(self):
        pass

    # TODO: need to protect through lock
    def open(self, user_id):
        self.tables.append({
            "game": Game(MAX_PLAYER),
            "owner": user_id,
            "players": [],
            "countdown": MAX_AWAIT,
            "wait_on_pos": -1,
            "cur_round": ""
        })

        return len(self.tables) - 1


    def join(self, table_id, user_id):
        """
        Join a table, return (pos, nplayer, err)
        """
        assert table_id < len(self.tables)
        table = self.tables[table_id]
        game = table["game"]
        players = table["players"]
        if user_id in players:
            return -1, -1, "already in this table"
        pos = len(players)
        players.append(user_id)
        game.setPlayer(pos, INITIAL_CHIPS)
        game.setReady(pos)
        return pos, pos + 1, None
    
    
    # def set_ob(self, func) -> None:
    #     self.game.setOb(func)


    def start(self, table_id, user_id):
        """
        Start a game, return (hands, err)
        """
        table = self.tables[table_id]
        if user_id != table["owner"]:
            return None, "Failed to start, because only the one who open the table can start the game"
        game = table["game"]
        players = table["players"]
        # if len(players) < 2:
        #     return None, "Failed to start, because this game requires at least TWO players"
        game.start()
        hands = []
        for pos, player in enumerate(players):
            hands.append({
                "id": player,
                "hand": game.getCardsByPos(pos)
            })
        return hands, None

    def timer_function(self, table_id):
        while True:
            starttime = time.time()
            should_stop = self.mainloop(table_id)
            if should_stop:
                break
            eclipse_time = time.time() - starttime
            print(eclipse_time)
            if eclipse_time < 1.0:
                time.sleep(1.0 - eclipse_time)

    def mainloop(self, table_id):
        table = self.tables[table_id]
        game = table["game"]
        players = table["players"]
        countdown = table["countdown"]
        round_status = game.get_round_status_name()
        exe_pos = game.exePos

        # if round_status == "END":
        #     return True

        if countdown == 0:
            # TODO: prefer check over flod
            game.pfold(exe_pos)
            bgame.send_to_channel_by_table_id(table_id, "timeout: {} fold".format(bgame.get_user_name_by_id(players[exe_pos])))
            table["countdown"] = MAX_AWAIT
            return False

        if table["cur_round"] != round_status:
            public_cards = game.pubCards
            bgame.send_to_channel_by_table_id(table_id, "Enter {} stage: public cards is {}".format(round_status, public_cards))
            table["cur_round"] = round_status

        if exe_pos == table["wait_on_pos"]:
            # TODO: find a way to update message
            if countdown % 5 == 0:
                bgame.send_to_channel_by_table_id(table_id, 
                    "[{}] wait for {} to act (remaining {}s)".format(round_status, 
                        bgame.get_user_name_by_id(players[exe_pos]), countdown))
            table["countdown"] = countdown - 1
        
        table["wait_on_pos"] = exe_pos
        return False


    # # TODO: need to protect through lock
    # def begin(self, func: Callable[[str], None]):
    #     self.game.start()
    #     func("now start")

    # def get_pos(self, user: str) -> int:
    #     return self.players.index(user)

    # def raise_(self, user:str, chip: int) -> bool:
    #     return self.game.praise(self.get_pos(user), chip) == 0

    # def check(self, user: str) -> bool:
    #     return self.game.pcheck(self.get_pos(user)) == 0

    # def fold(self, user: str) -> bool:
    #     return self.game.pfold(self.get_pos(user)) == 0

    # def bet(self, user: str, chip: int) -> bool:
    #     return self.game.pbet(self.get_pos(user), chip)

    # def call(self, user: str) -> bool:
    #     return self.game.pcall(self.get_pos(user))

    # def all_in(self, user: str) -> bool:
    #     return self.game.pallin(self.get_pos(user))


    # interface: maybe in the future self.players contains more fields
    def get_all_players(self):
        return self.players


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
