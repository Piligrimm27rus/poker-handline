import pytest

from poker_handline.stats import load_session, parse_hand, summarize, summarize_by_position


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


def test_button_and_big_blind_slices():
    hands = load_session("tests/fixtures/session_six_hands.json")
    by_pos = summarize_by_position(hands)
    assert by_pos["BTN"]["hands"] == 3
    assert by_pos["BB"]["vpip"] == 0.0
    assert set(by_pos) == {"BTN", "BB", "CO", "HJ"}
