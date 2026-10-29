import random
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from poker_handline.cards import Card, deck, parse_cards
from poker_handline.evaluator import best_hand
from poker_handline.ranges import expand_range


@dataclass(frozen=True)
class EquityResult:
    win: float
    tie: float
    lose: float
    trials: int
    method: Literal["exact", "monte_carlo"]

    @property
    def share(self) -> float:
        return self.win + self.tie / 2.0


def equity(
    hero: str,
    villain: str,
    board: str = "",
    *,
    trials: int = 10_000,
    seed: int = 0,
) -> EquityResult:
    hero_cards = parse_cards(hero)
    board_cards = parse_cards(board)
    if len(hero_cards) != 2 or len(board_cards) not in (0, 3, 4, 5):
        raise ValueError(f"invalid hero or board: {hero!r} {board!r}")
    if set(hero_cards) & set(board_cards):
        raise ValueError(f"hero overlaps the board: {hero!r} {board!r}")

    missing = 5 - len(board_cards)
    dead = (*hero_cards, *board_cards)
    blocked = set(dead)
    pool = [card for card in deck() if card not in blocked]
    combos = [
        combo
        for combo in sorted(expand_range(villain, dead), key=_combo_key)
        if sum(card not in combo for card in pool) >= missing
    ]
    if not combos:
        raise ValueError(villain)
    if missing == 5:
        return _monte_carlo(hero_cards, combos, pool, trials, seed)
    return _exact(hero_cards, board_cards, combos, pool, missing)


def _exact(
    hero_cards: tuple[Card, ...],
    board_cards: tuple[Card, ...],
    combos: Sequence[frozenset[Card]],
    pool: Sequence[Card],
    missing: int,
) -> EquityResult:
    wins = ties = losses = total = 0
    for combo in combos:
        live = [card for card in pool if card not in combo]
        runouts = combinations(live, missing) if missing else ((),)
        for extra in runouts:
            outcome = _compare(hero_cards, combo, board_cards + extra)
            total += 1
            if outcome > 0:
                wins += 1
            elif outcome < 0:
                losses += 1
            else:
                ties += 1
    return _result(wins, ties, losses, total, "exact")


def _monte_carlo(
    hero_cards: tuple[Card, ...],
    combos: Sequence[frozenset[Card]],
    pool: Sequence[Card],
    trials: int,
    seed: int,
) -> EquityResult:
    rng = random.Random(seed)
    wins = ties = losses = 0
    live_pools = [[card for card in pool if card not in combo] for combo in combos]
    for _ in range(trials):
        index = rng.randrange(len(combos))
        board = tuple(rng.sample(live_pools[index], 5))
        outcome = _compare(hero_cards, combos[index], board)
        if outcome > 0:
            wins += 1
        elif outcome < 0:
            losses += 1
        else:
            ties += 1
    return _result(wins, ties, losses, trials, "monte_carlo")


def _compare(hero_cards: Sequence[Card], combo: frozenset[Card], board: Sequence[Card]) -> int:
    hero_key = best_hand((*hero_cards, *board)).key()
    villain_key = best_hand((*combo, *board)).key()
    return (hero_key > villain_key) - (hero_key < villain_key)


def _result(
    wins: int,
    ties: int,
    losses: int,
    total: int,
    method: Literal["exact", "monte_carlo"],
) -> EquityResult:
    return EquityResult(wins / total, ties / total, losses / total, total, method)


def _combo_key(combo: frozenset[Card]) -> tuple[tuple[int, str], ...]:
    return tuple(sorted((card.rank, card.suit) for card in combo))
