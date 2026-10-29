import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Street = Literal["preflop", "flop", "turn", "river"]
Actor = Literal["hero", "villain"]
Kind = Literal["fold", "check", "call", "bet", "raise"]
Position = Literal["UTG", "HJ", "CO", "BTN", "SB", "BB"]

_STREETS = {"preflop", "flop", "turn", "river"}
_ACTORS = {"hero", "villain"}
_KINDS = {"fold", "check", "call", "bet", "raise"}
_POSITIONS = {"UTG", "HJ", "CO", "BTN", "SB", "BB"}


@dataclass(frozen=True)
class Action:
    street: Street
    actor: Actor
    kind: Kind
    amount_bb: float


@dataclass(frozen=True)
class SessionHand:
    hand_id: str
    position: Position
    saw_flop: bool
    went_to_showdown: bool
    won_at_showdown: bool
    result_bb: float
    actions: tuple[Action, ...]


def parse_hand(data: dict) -> SessionHand:
    saw_flop = bool(data["saw_flop"])
    went_to_showdown = bool(data["went_to_showdown"])
    won_at_showdown = bool(data["won_at_showdown"])
    if went_to_showdown and not saw_flop:
        raise ValueError("showdown requires a flop")
    if won_at_showdown and not went_to_showdown:
        raise ValueError("a showdown win requires a showdown")
    position = data["position"]
    if position not in _POSITIONS:
        raise ValueError(f"unknown position: {position}")
    return SessionHand(
        hand_id=str(data["hand_id"]),
        position=position,
        saw_flop=saw_flop,
        went_to_showdown=went_to_showdown,
        won_at_showdown=won_at_showdown,
        result_bb=float(data["result_bb"]),
        actions=tuple(_parse_action(item) for item in data["actions"]),
    )


def load_session(path: str | Path) -> tuple[SessionHand, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(parse_hand(item) for item in payload)


def summarize(hands: Sequence[SessionHand]) -> dict[str, float | int | None]:
    vpip = pfr = three_bet = three_bet_chances = 0
    aggression = calls = 0
    cbet = cbet_chances = 0
    saw_flop = showdowns = showdown_wins = 0
    net_bb = 0.0
    for hand in hands:
        if _vpip(hand):
            vpip += 1
        if _pfr(hand):
            pfr += 1
        if _faced_earlier_raise(hand):
            three_bet_chances += 1
            if _three_bet(hand):
                three_bet += 1
        aggression += _postflop_aggression(hand)
        calls += _postflop_calls(hand)
        cbet_result = _cbet_flop(hand)
        if cbet_result is not None:
            cbet_chances += 1
            if cbet_result:
                cbet += 1
        if hand.saw_flop:
            saw_flop += 1
        if hand.went_to_showdown:
            showdowns += 1
        if hand.won_at_showdown:
            showdown_wins += 1
        net_bb += hand.result_bb
    count = len(hands)
    return {
        "hands": count,
        "vpip": _rate(vpip, count),
        "pfr": _rate(pfr, count),
        "three_bet": _rate(three_bet, three_bet_chances),
        "af": _rate(aggression, calls),
        "cbet_flop": _rate(cbet, cbet_chances),
        "wtsd": _rate(showdowns, saw_flop),
        "wsd": _rate(showdown_wins, showdowns),
        "net_bb": net_bb,
    }


def summarize_by_position(hands: Sequence[SessionHand]) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[SessionHand]] = {}
    for hand in hands:
        grouped.setdefault(hand.position, []).append(hand)
    return {position: summarize(group) for position, group in grouped.items()}


def _parse_action(data: dict) -> Action:
    street = data["street"]
    actor = data["actor"]
    kind = data["kind"]
    if street not in _STREETS or actor not in _ACTORS or kind not in _KINDS:
        raise ValueError(f"unknown action: {data}")
    return Action(street, actor, kind, float(data["amount_bb"]))


def _hero_preflop(hand: SessionHand) -> tuple[Action, ...]:
    return tuple(action for action in hand.actions if action.street == "preflop" and action.actor == "hero")


def _vpip(hand: SessionHand) -> bool:
    return any(action.kind in {"call", "raise"} for action in _hero_preflop(hand))


def _pfr(hand: SessionHand) -> bool:
    return any(action.kind == "raise" for action in _hero_preflop(hand))


def _faced_earlier_raise(hand: SessionHand) -> bool:
    seen_villain_raise = False
    for action in hand.actions:
        if action.street != "preflop":
            continue
        if action.actor == "villain" and action.kind == "raise":
            seen_villain_raise = True
        elif action.actor == "hero" and seen_villain_raise:
            return True
    return False


def _three_bet(hand: SessionHand) -> bool:
    seen_villain_raise = False
    for action in hand.actions:
        if action.street != "preflop":
            continue
        if action.actor == "villain" and action.kind == "raise":
            seen_villain_raise = True
        elif action.actor == "hero" and action.kind == "raise" and seen_villain_raise:
            return True
    return False


def _postflop_aggression(hand: SessionHand) -> int:
    return sum(
        action.street != "preflop" and action.actor == "hero" and action.kind in {"bet", "raise"}
        for action in hand.actions
    )


def _postflop_calls(hand: SessionHand) -> int:
    return sum(
        action.street != "preflop" and action.actor == "hero" and action.kind == "call"
        for action in hand.actions
    )


def _last_preflop_raiser(hand: SessionHand) -> Actor | None:
    raiser: Actor | None = None
    for action in hand.actions:
        if action.street == "preflop" and action.kind == "raise":
            raiser = action.actor
    return raiser


def _cbet_flop(hand: SessionHand) -> bool | None:
    if not hand.saw_flop or _last_preflop_raiser(hand) != "hero":
        return None
    flop = [action for action in hand.actions if action.street == "flop" and action.actor == "hero"]
    if not flop:
        return None
    return flop[0].kind == "bet"


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator
