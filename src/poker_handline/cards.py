from dataclasses import dataclass

_RANKS = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}
_SUITS = ("s", "h", "d", "c")


@dataclass(frozen=True, order=True)
class Card:
    rank: int  # 2..14
    suit: str  # "s" | "h" | "d" | "c"


def parse_card(text: str) -> Card:
    if len(text) != 2:
        raise ValueError(f"invalid card: {text!r}")
    rank_text = text[0].upper()
    suit = text[1].lower()
    if rank_text not in _RANKS or suit not in _SUITS:
        raise ValueError(f"invalid card: {text!r}")
    return Card(_RANKS[rank_text], suit)


def parse_cards(text: str) -> tuple[Card, ...]:
    compact = "".join(text.split())
    if len(compact) % 2 != 0:
        raise ValueError(f"odd-length card string: {text!r}")
    cards = tuple(parse_card(compact[index : index + 2]) for index in range(0, len(compact), 2))
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate card: {text!r}")
    return cards


def deck() -> tuple[Card, ...]:
    return tuple(Card(rank, suit) for suit in _SUITS for rank in range(2, 15))
