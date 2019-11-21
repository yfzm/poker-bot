from enum import Enum


INITIAL_CHIPS = 500


class PlayerStatus(Enum):
    PLAYING = 0
    FOLD = 1
    ALLIN = 2


class Player:
    def __init__(self, user: str):
        self.user = user
        self.chip = INITIAL_CHIPS
        self.init()

    def init(self):
        self.chipBet = 0
        self.cards = [0] * 2
        self.active = True
        self.status = PlayerStatus.PLAYING
        self.rank = None
        self.hand = None

    def get_remaining_chip(self) -> int:
        return self.chip - self.chipBet

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
