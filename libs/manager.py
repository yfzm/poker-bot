from enum import Enum

class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


class GameManager:
    def __init__(self):
        self.status = Status.IDLE
        self.players = []

    def init_status(self):
        self.players = []

    def prepare(self):
        if self.status == Status.IDLE:
            self.init_status()
            self.status = Status.PREPARE
            return True
        return False

    def join(self, user):
        if self.status != Status.PREPARE:
            return False, None
        if user["name"] in self.players:
            return False, None
        self.players.append(user["name"])
        return True, len(self.players)

    # interface: maybe in the future self.players contains more fields
    def get_all_players():
        return self.players


gameManager = GameManager()

# some fields of `user`
# 'color'
# 'deleted'
# 'id'
# 'is_admin'
# 'is_app_user'
# 'is_bot'
# 'name'
