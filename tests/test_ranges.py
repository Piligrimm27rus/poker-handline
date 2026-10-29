import pytest

from poker_handline.cards import parse_card, parse_cards
from poker_handline.ranges import expand_range


def test_concrete_hand_and_pair_combos():
    assert len(expand_range("AsKh")) == 1
    assert len(expand_range("QQ")) == 6
    assert len(expand_range("AKs")) == 4
    assert len(expand_range("AKo")) == 12
    assert len(expand_range("AK")) == 16


def test_plus_ranges_do_not_include_a_pair_of_aces_for_suited():
    pairs = expand_range("QQ+")
    assert len(pairs) == 6 + 6 + 6  # QQ KK AA
    suited = expand_range("ATs+")
    assert len(suited) == 4 * 4  # AT AJ AQ AK suited
    assert all(len(combo) == 2 for combo in suited)


def test_random_and_union():
    assert len(expand_range("random")) == 1326
    assert len(expand_range("QQ+,AKs")) == 18 + 4


def test_dead_cards_remove_combos():
    dead = parse_cards("As Ah")
    remaining = expand_range("AA", dead)
    assert len(remaining) == 1  # только AdAc
    with pytest.raises(ValueError):
        expand_range("AsKh", parse_cards("As"))


def test_bad_token():
    with pytest.raises(ValueError):
        expand_range("AKz")
