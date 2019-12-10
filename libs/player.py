from enum import Enum


class PlayerStatus(Enum):
    PLAYING = 0
    FOLD = 1
    ALLIN = 2


class PlayerMode(Enum):
    ENTERING = 0
    NORMAL = 1
    LEAVING = 2


class Player:
    def __init__(self, userid: str, username: str, chip: int):
        self.userid = userid
        self.username = username
        self.chip = chip
        self.mode = PlayerMode.ENTERING
        self.init()

    def init(self):
        self.chip_bet = 0
        self.cards = [0] * 2
        self.status = PlayerStatus.PLAYING
        self.timeout_count = 0
        self.rank = None
        self.hand = None

    def get_remaining_chip(self) -> int:
        return self.chip - self.chip_bet

    def is_playing(self) -> bool:
        return self.status == PlayerStatus.PLAYING

    def is_fold(self) -> bool:
        return self.status == PlayerStatus.FOLD

    def is_allin(self) -> bool:
        return self.status == PlayerStatus.ALLIN

    def set_playing(self) -> None:
        self.status = PlayerStatus.PLAYING

    def set_fold(self) -> None:
        self.status = PlayerStatus.FOLD

    def set_allin(self) -> None:
        self.status = PlayerStatus.ALLIN

    def set_rank_and_hand(self, rank, hand):
        self.rank = rank
        self.hand = hand

    def is_leaving(self) -> bool:
        return self.mode == PlayerMode.LEAVING

    def is_normal(self) -> bool:
        return self.mode == PlayerMode.NORMAL

    def set_entering(self) -> None:
        self.mode = PlayerMode.ENTERING

    def set_normal(self) -> None:
        self.mode = PlayerMode.NORMAL

    def set_leaving(self) -> None:
        self.mode = PlayerMode.LEAVING
