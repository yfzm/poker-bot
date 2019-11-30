import unittest
from libs.game import Game, GameStatus, RoundStatus
from libs.player import Player


INITIAL_CHIPS = 500


class TestGameKernel(unittest.TestCase):

    def setUp(self):
        self.g = Game()
        self.p1 = Player("u1", "player1", INITIAL_CHIPS)
        self.p2 = Player("u2", "player2", INITIAL_CHIPS)
        self.p3 = Player("u3", "player3", INITIAL_CHIPS)
        self.players = list(filter(lambda p: not p.is_leaving(), [self.p1, self.p2, self.p3]))
        for player in self.players:
            player.set_normal()
        self.g.start(self.players, 20, 1)

    def test_fold(self):
        game = self.g
        self.assertEqual(game.exe_pos, 1)
        self.assertEqual(game.pfold(1), 0)
        self.assertEqual(game.get_active_player_num(), 2)
        self.assertEqual(game.exe_pos, 2)

        self.assertEqual(game.pcall(2), 0)
        self.assertEqual(game.pcheck(0), 0)
        self.assertEqual(game.exe_pos, 2)
        self.assertEqual(game.pfold(2), 0)
        self.assertEqual(game.round_status, RoundStatus.END)
        self.assertEqual(game.game_status, GameStatus.WAITING)

    def test_all_in(self):
        pass

    def test_show_hand1(self):
        pass

    def test_wrong_pos_take_action(self):
        game = self.g
        self.assertEqual(game.exe_pos, 1)
        self.assertEqual(game.pfold(0), -1)
        self.assertEqual(game.pfold(2), -1)
        self.assertEqual(game.pfold(3), -1)
        self.assertEqual(game.pfold(-1), -1)
        self.assertEqual(game.pfold(1), 0)
        self.assertEqual(game.exe_pos, 2)
