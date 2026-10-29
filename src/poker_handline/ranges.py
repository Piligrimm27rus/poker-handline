from collections.abc import Collection
from itertools import combinations

from poker_handline.cards import Card, deck, parse_card

_RANKS = {char: value for value, char in enumerate("23456789TJQKA", start=2)}
_SUITS = "shdc"


def expand_range(notation: str, dead: Collection[Card] = ()) -> frozenset[frozenset[Card]]:
    tokens = [part.strip() for part in notation.split(",")]
    if not tokens or any(token == "" for token in tokens):
        raise ValueError(notation)
    combos: set[frozenset[Card]] = set()
    for token in tokens:
        combos.update(_expand_token(token))
    blocked = set(dead)
    alive = frozenset(combo for combo in combos if combo.isdisjoint(blocked))
    if not alive:
        raise ValueError(notation)
    return alive


def _expand_token(token: str) -> set[frozenset[Card]]:
    if token == "random":
        return {frozenset(pair) for pair in combinations(deck(), 2)}

    parts = token.split()
    if len(parts) == 2:
        return {_two_cards(parts[0], parts[1], token)}
    if " " in token:
        raise ValueError(token)

    concrete = _compact_concrete(token)
    if concrete is not None:
        return {concrete}

    plus = token.endswith("+")
    body = token[:-1] if plus else token
    suited: bool | None = None
    if body.endswith("s"):
        suited = True
        body = body[:-1]
    elif body.endswith("o"):
        suited = False
        body = body[:-1]
    if len(body) != 2 or body[0] not in _RANKS or body[1] not in _RANKS:
        raise ValueError(token)

    first = _RANKS[body[0]]
    second = _RANKS[body[1]]
    if first == second:
        if suited is not None:
            raise ValueError(token)
        ranks = range(first, 15) if plus else (first,)
        return _pair_combos(ranks)
    if plus and not second < first:
        raise ValueError(token)
    if plus:
        return _unpaired_combos(first, range(second, first), suited)
    return _unpaired_combos(max(first, second), (min(first, second),), suited)


def _two_cards(left: str, right: str, token: str) -> frozenset[Card]:
    try:
        first = parse_card(left)
        second = parse_card(right)
    except ValueError:
        raise ValueError(token) from None
    if first == second:
        raise ValueError(token)
    return frozenset((first, second))


def _compact_concrete(token: str) -> frozenset[Card] | None:
    if len(token) != 4:
        return None
    try:
        first = parse_card(token[:2])
        second = parse_card(token[2:])
    except ValueError:
        return None
    if first == second:
        raise ValueError(token)
    return frozenset((first, second))


def _pair_combos(ranks: Collection[int]) -> set[frozenset[Card]]:
    combos: set[frozenset[Card]] = set()
    for rank in ranks:
        cards = [Card(rank, suit) for suit in _SUITS]
        combos.update(frozenset(pair) for pair in combinations(cards, 2))
    return combos


def _unpaired_combos(high: int, kickers: Collection[int], suited: bool | None) -> set[frozenset[Card]]:
    combos: set[frozenset[Card]] = set()
    for kicker in kickers:
        for high_suit in _SUITS:
            for kicker_suit in _SUITS:
                same_suit = high_suit == kicker_suit
                if suited is True and not same_suit:
                    continue
                if suited is False and same_suit:
                    continue
                combos.add(frozenset((Card(high, high_suit), Card(kicker, kicker_suit))))
    return combos
