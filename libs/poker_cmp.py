from itertools import combinations


def _card_ranks(cards):
    ranks = ['0123456789TJQKA'.index(r) for r, x in cards]
    ranks.sort(reverse=True)
    if ranks == [14, 5, 4, 3, 2]:
        ranks = [5, 4, 3, 2, 1]
    return ranks


def _straight(ranks):
    return (max(ranks) - min(ranks)) == 4 and len(set(ranks)) == 5


def _flush(cards):
    hand_flush = [s for r, s in cards]
    return len(set(hand_flush)) == 1


def _kind(n, ranks):
    for r in ranks:
        if ranks.count(r) == n:
            return r
    return None


def _two_pair(ranks):
    pair = _kind(2, ranks)
    low_pair = _kind(2, list(reversed(ranks)))
    if pair and low_pair != pair:
        return list(map(int, (pair, low_pair)))
    else:
        return None


def _hand_rank(hand):
    ranks = _card_ranks(hand)
    if _straight(ranks) and _flush(hand):
        return 8, max(ranks)
    elif _kind(4, ranks):
        return 7, _kind(4, ranks), _kind(1, ranks)
    elif _kind(3, ranks) and _kind(2, ranks):
        return 6, _kind(3, ranks), _kind(2, ranks)
    elif _flush(hand):
        return 5, ranks
    elif _straight(ranks):
        return 4, max(ranks)
    elif _kind(3, ranks):
        return 3, _kind(3, ranks), ranks
    elif _two_pair(ranks):
        return 2, _two_pair(ranks), ranks
    elif _kind(2, ranks):
        return 1, _kind(2, ranks), ranks
    else:
        return 0, ranks


def poker7(cards):
    hands = combinations(cards, 5)
    hand = max(hands, key=_hand_rank)
    return hand, _hand_rank(hand)


if __name__ == '__main__':
    cards = "2s 3d 4s 5s As 9s Ts".split()
    print(poker7(cards))
    sf = "6c 7c 8c 9c Tc".split()
    temp = _hand_rank(sf)
    hands = [sf]
    res = poker7(hands)
