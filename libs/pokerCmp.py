from itertools import combinations, permutations

def card_ranks(cards):
    ranks = ['0123456789TJQKA'.index(r) for r,x in cards]
    ranks.sort(reverse=True)
    if ranks == [14, 5, 4, 3, 2]:
        ranks = [5, 4, 3, 2, 1]
    return ranks

def straight(ranks):
    return (max(ranks) - min(ranks)) == 4 and len(set(ranks)) == 5

def flush(cards):
    hand_flush = [s for r, s in cards]
    return len(set(hand_flush)) == 1

def kind(n, ranks):
    for r in ranks:
        if (ranks.count(r) == n):
            return r
    return None

def two_pair(ranks):
    pair = kind(2, ranks)
    lowpair = kind(2, list(reversed(ranks)))
    if pair and lowpair != pair:
        return list(map(int, (pair, lowpair)))
    else:
        return None

def hand_rank(hand):
    ranks = card_ranks(hand) 
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)

def poker7(cards):
    hands = combinations(cards, 5)
    hand = max(hands, key=hand_rank)
    return {'hand': hand, 'rank': hand_rank(hand)}

if __name__ == '__main__':
    cards = "2s 3d 4s 5s As 9s Ts".split()
    print(poker7(cards))
    sf = "6c 7c 8c 9c Tc".split()
    temp = hand_rank(sf)
    hands = [sf]
    res = poker(hands)