import pytest

from poker_handline.cards import parse_cards
from poker_handline.evaluator import best_hand, rank_five


def rank(text: str):
    return rank_five(parse_cards(text))


def test_categories_and_names():
    assert rank("As Ks Qs Js Ts").name == "роял-флеш"
    assert rank("9h 8h 7h 6h 5h").key() == (8, (9,))
    assert rank("As Ks Qs Js Ts").key() > rank("9h 8h 7h 6h 5h").key()
    assert rank("Ah Ad Ac As Kd").key() == (7, (14, 13))
    assert rank("Kh Kd Kc 2s 2d").key() == (6, (13, 2))
    assert rank("Ah Ad Ac Ks Kd").key() > rank("Kh Kd Kc As Ad").key()
    assert rank("Ah Kh Qh Jh 9h").key() == (5, (14, 13, 12, 11, 9))
    assert rank("As Kd Qc Jh Td").key() == (4, (14,))
    assert rank("As 2d 3c 4h 5s").key() == (4, (5,))
    assert rank("As Kd Qc Jh Td").key() > rank("As 2d 3c 4h 5s").key()
    assert rank("Th Td Tc Ks Qd").key() == (3, (10, 13, 12))
    assert rank("Ah Ad Kh Kd 2c").key() == (2, (14, 13, 2))
    assert rank("Ah Ad Kh Kd Qc").key() > rank("Ah Ad Qh Qd Kc").key()
    assert rank("Ah Ad Ks Qd Jc").key() == (1, (14, 13, 12, 11))
    assert rank("Ah Kd Qc Jh 9s").key() == (0, (14, 13, 12, 11, 9))


def test_wheel_is_not_a_broadway_straight():
    assert rank("As 2d 3c 4h 5s").name == "стрит"
    assert rank("Ah 2h 3h 4h 5h").name == "стрит-флеш"
    assert rank("Ah 2h 3h 4h 5h").key() == (8, (5,))


def test_pair_kicker_order():
    assert rank("Ah Ad Ks Qd 2c").key() > rank("Ah Ad Qs Jd 9c").key()


def test_seven_cards_picks_full_house_not_two_pair():
    cards = parse_cards("Ah Ad As Kd Kc 2c 2d")
    assert best_hand(cards).key() == (6, (14, 13))
    assert best_hand(cards).name == "фулл-хаус"


def test_player_plays_the_board_flush():
    cards = parse_cards("2c 3d Ah Kh Qh Jh 9h")
    assert best_hand(cards).name == "флеш"
    assert best_hand(cards).key() == (5, (14, 13, 12, 11, 9))


def test_six_cards_drops_the_small_kicker():
    cards = parse_cards("Ah Ad Ks Qd Jc 2c")
    assert best_hand(cards).key() == (1, (14, 13, 12, 11))


def test_board_length_other_than_five_six_seven_rejected():
    with pytest.raises(ValueError):
        best_hand(parse_cards("As Kd Qc Jh"))
