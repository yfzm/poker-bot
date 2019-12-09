import unittest
from libs.poker_cmp import poker7

TEST_CASE = [
    # TODO: to be filled
    ("2s 3d 4s 5s As 9s Ts", "4s 5s As 9s Ts"),
    ("8s Ks Qs Js As 9s Ts", "Ts Js Qs Ks As"),
    ("As 3d 5h 7d 2d Qs Kd", "5h 7d Qs Kd As"),
    ("9s 5d Ts Th 4d Td 3d", "9s 5d Ts Th Td"),
    ("2d Qh Ah 7s 2c Qc 8c", "2d Qh Ah 2c Qc"),
]


class TestPokerCmp(unittest.TestCase):
    def assertUnorderedListEqual(self, l1, l2, msg=None):
        return self.assertSetEqual(set(l1), set(l2), msg)

    def test_poker7(self):
        for i in TEST_CASE:
            h, r = poker7(i[0].split())
            self.assertSetEqual(set(h), set(i[1].split()), i)
