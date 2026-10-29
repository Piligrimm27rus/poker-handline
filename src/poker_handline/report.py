from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from poker_handline.cards import Card, parse_cards
from poker_handline.equity import EquityResult, equity
from poker_handline.evaluator import best_hand

Action = Literal["fold", "call", "check"]
_RANK_CHAR = "23456789TJQKA"


@dataclass(frozen=True)
class HandReport:
    hero: tuple[str, str]
    board: tuple[str, ...]
    villain: str
    hand_name: str
    equity: EquityResult
    pot: int
    to_call: int
    required_equity: float | None
    action: Action


def hole_name(hero: Sequence[Card]) -> str:
    if hero[0].rank == hero[1].rank:
        return "пара"
    return "старшая карта"


def build_report(
    hero: str,
    board: str,
    villain: str,
    pot: int,
    to_call: int,
    *,
    trials: int = 10_000,
    seed: int = 0,
) -> HandReport:
    if pot < 0 or to_call < 0:
        raise ValueError(f"money must be >= 0, got pot={pot} to_call={to_call}")
    hero_cards = parse_cards(hero)
    board_cards = parse_cards(board)
    if len(hero_cards) != 2:
        raise ValueError(f"hero must be two cards: {hero!r}")
    result = equity(hero, villain, board, trials=trials, seed=seed)
    if board_cards:
        name = best_hand((*hero_cards, *board_cards)).name
    else:
        name = hole_name(hero_cards)
    if to_call == 0:
        required = None
        action: Action = "check"
    else:
        required = to_call / (pot + to_call)
        action = "call" if result.share + 1e-12 >= required else "fold"
    return HandReport(
        hero=(_card_text(hero_cards[0]), _card_text(hero_cards[1])),
        board=tuple(_card_text(card) for card in board_cards),
        villain=_villain_text(villain),
        hand_name=name,
        equity=result,
        pot=pot,
        to_call=to_call,
        required_equity=required,
        action=action,
    )


def _card_text(card: Card) -> str:
    return f"{_RANK_CHAR[card.rank - 2]}{card.suit}"


def _villain_text(villain: str) -> str:
    try:
        cards = parse_cards(villain)
    except ValueError:
        return villain.strip()
    if not cards:
        return villain.strip()
    return "".join(_card_text(card) for card in cards)
