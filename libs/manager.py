from enum import Enum

class Status(Enum):
    IDLE = 1
    PREPARE = 2
    PLAYING = 3
    END_HAND = 4


class GameManager:
    def __init__(self):
        self.status = Status.IDLE

    def prepare(self):
        if self.status == Status.IDLE:
            self.status = Status.PREPARE
            return True
        return False


gameManager = GameManager()
