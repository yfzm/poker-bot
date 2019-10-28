from enum import Enum
from libs.game import Game
import threading as thread
from typing import Callable

class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


MAX_PLAYER = 6
MAX_AWAIT = 30

class GameManager:
    def __init__(self):
        self.status = Status.IDLE
        self.players = []
        self.game = None
        self.timer = None

    def init_status(self,func: Callable[[str], None]):
        self.players = []
        self.game = Game(MAX_PLAYER)
        self.timer = thread.Timer(MAX_AWAIT,function= self.begin, args=[func])

    # TODO: need to protect through lock
    def prepare(self, func: Callable[[str], None]):
        if self.status == Status.IDLE:
            self.init_status(func)
            self.status = Status.PREPARE
            self.timer.start()
            return True
        return False

    def join(self, user):
        if self.status != Status.PREPARE:
            return False, None
        if user["name"] in self.players:
            return False, None
        self.game.setPlayer(len(self.players), 500)
        self.players.append(user["name"])
        return True, len(self.players)
    
    def set_ob(self, func) -> None:
        self.game.setOb(func)

    # TODO: need to protect through lock
    def begin(self, func: Callable[[str], None]):
        self.game.start()
        func()

    def get_pos(self, user: str) -> int:
        return self.players.index(user)

    def raise_(self, user:str, chip: int) -> bool:
        return self.game.praise(self.get_pos(user), chip) == 0

    def check(self, user: str) -> bool:
        return self.game.pcheck(self.get_pos(user)) == 0

    def fold(self, user: str) -> bool:
        return self.game.pfold(self.get_pos(user)) == 0

    def bet(self, user: str, chip: int) -> bool:
        return self.game.pbet(self.get_pos(user), chip)

    def call(self, user: str) -> bool:
        return self.game.pcall(self.get_pos(user))

    def all_in(self, user: str) -> bool:
        return self.game.pallin(self.get_pos(user))


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
