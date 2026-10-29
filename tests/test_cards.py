import pytest

from poker_handline.cards import Card, deck, parse_card, parse_cards


def test_parse_card_rank_and_suit():
    assert parse_card("As") == Card(14, "s")
    assert parse_card("Td") == Card(10, "d")
    assert parse_card("2c") == Card(2, "c")


def test_parse_cards_splits_on_spaces_and_concat():
    assert parse_cards("As Kh") == (Card(14, "s"), Card(13, "h"))
    assert parse_cards("AsKh") == (Card(14, "s"), Card(13, "h"))
    assert parse_cards("") == ()


def test_ten_is_letter_t_not_digit_10():
    with pytest.raises(ValueError):
        parse_card("10s")


def test_duplicate_and_junk_rejected():
    with pytest.raises(ValueError):
        parse_cards("As As")
    with pytest.raises(ValueError):
        parse_card("Ax")
    with pytest.raises(ValueError):
        parse_card("1s")


def test_deck_has_52_unique_cards():
    cards = deck()
    assert len(cards) == 52
    assert len(set(cards)) == 52
    assert Card(14, "s") in cards
    assert cards == deck()
