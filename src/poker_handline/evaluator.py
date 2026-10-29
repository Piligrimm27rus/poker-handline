from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from poker_handline.cards import Card

_CATEGORY_NAMES = {
    8: "стрит-флеш",
    7: "каре",
    6: "фулл-хаус",
    5: "флеш",
    4: "стрит",
    3: "тройка",
    2: "две пары",
    1: "пара",
    0: "старшая карта",
}


@dataclass(frozen=True)
class HandRank:
    category: int
    kickers: tuple[int, ...]
    name: str

    def key(self) -> tuple[int, tuple[int, ...]]:
        return (self.category, self.kickers)


def rank_five(cards: Sequence[Card]) -> HandRank:
    ranks = sorted((card.rank for card in cards), reverse=True)
    is_flush = len({card.suit for card in cards}) == 1
    straight_high = _straight_high(ranks)
    if straight_high is not None and is_flush:
        name = "роял-флеш" if straight_high == 14 else "стрит-флеш"
        return _hand(8, (straight_high,), name)

    grouped = sorted(Counter(ranks).items(), key=lambda item: (item[1], item[0]), reverse=True)
    counts = tuple(count for _, count in grouped)
    if counts[0] == 4:
        return _hand(7, (grouped[0][0], grouped[1][0]))
    if counts == (3, 2):
        return _hand(6, (grouped[0][0], grouped[1][0]))
    if is_flush:
        return _hand(5, tuple(ranks))
    if straight_high is not None:
        return _hand(4, (straight_high,))
    if counts[0] == 3:
        return _hand(3, (grouped[0][0], grouped[1][0], grouped[2][0]))
    if counts == (2, 2, 1):
        return _hand(2, (grouped[0][0], grouped[1][0], grouped[2][0]))
    if counts[0] == 2:
        return _hand(1, tuple(rank for rank, _ in grouped))
    return _hand(0, tuple(ranks))


def _hand(category: int, kickers: tuple[int, ...], name: str | None = None) -> HandRank:
    return HandRank(category, kickers, _CATEGORY_NAMES[category] if name is None else name)


def _straight_high(ranks: list[int]) -> int | None:
    unique = set(ranks)
    if len(unique) != 5:
        return None
    if unique == {14, 5, 4, 3, 2}:
        return 5
    if max(ranks) - min(ranks) == 4:
        return max(ranks)
    return None
