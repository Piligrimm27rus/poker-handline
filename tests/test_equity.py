from poker_handline.equity import equity


def test_river_royal_beats_a_pair_exactly():
    result = equity("AhKh", "2d2s", "Qh Jh Th 2c 3d")
    assert result.method == "exact"
    assert result.win == 1.0
    assert result.tie == 0.0
    assert result.share == 1.0


def test_river_same_straight_splits_exactly():
    result = equity("AsKd", "AhKc", "Qs Js Tc 2c 3d")
    assert result.tie == 1.0
    assert result.share == 0.5


def test_turn_flush_draw_versus_overpair_is_nine_hearts():
    # 8h7h против QcQd на Ah Kh 2c 3d. Пара дам без сета.
    # Из 44 живых карт выигрывают ровно 9 оставшихся черв:
    # 2h 3h 4h 5h 6h 9h Th Jh Qh. Флеш бьёт и QQ, и фулл-хаус тут не собирается.
    # Qh даёт злодею сет, но флеш старше сета. 2h и 3h тоже остаются аутами.
    result = equity("8h7h", "QcQd", "Ah Kh 2c 3d")
    assert result.method == "exact"
    assert result.trials == 44
    assert result.win == 9 / 44
    assert result.tie == 0.0
    assert result.lose == 35 / 44


def test_preflop_aces_versus_kings_is_about_82_percent():
    result = equity("AsAh", "KdKh", trials=8_000, seed=1)
    assert result.method == "monte_carlo"
    assert result.trials == 8_000
    assert abs(result.share - 0.822) < 0.03


def test_flop_is_exact_and_partial_board_rejected():
    import pytest

    flop = equity("AsKh", "QQ", "Td 9c 2s", trials=100, seed=1)
    assert flop.method == "exact"
    with pytest.raises(ValueError):
        equity("AsKh", "QQ", "Td")
