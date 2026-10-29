import pytest

from poker_handline.stats import load_session, parse_hand, summarize


def test_six_hand_fixture_matches_the_manual_tally():
    hands = load_session("tests/fixtures/session_six_hands.json")
    assert summarize(hands) == {
        "hands": 6,
        "vpip": 5 / 6,
        "pfr": 4 / 6,
        "three_bet": 1 / 2,
        "af": 1.0,
        "cbet_flop": 1 / 2,
        "wtsd": 1 / 4,
        "wsd": 0.0,
        "net_bb": 4.5,
    }


def test_showdown_flag_without_flop_is_rejected():
    with pytest.raises(ValueError):
        parse_hand(
            {
                "hand_id": "bad",
                "position": "BTN",
                "saw_flop": False,
                "went_to_showdown": True,
                "won_at_showdown": False,
                "result_bb": 0,
                "actions": [],
            }
        )
