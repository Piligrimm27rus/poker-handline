import pytest

from poker_handline.report import build_report


def test_call_when_equity_covers_the_price():
    # Ривер, у героя роял-флеш, эквити 100%. Банк 100, колл 50 → нужно 1/3.
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)
    assert report.hand_name == "роял-флеш"
    assert report.required_equity == pytest.approx(50 / 150)
    assert report.action == "call"
    assert report.equity.share == 1.0


def test_fold_when_draw_does_not_cover_a_large_bet():
    # Та же раздача, что в тесте эквити: share = 9/44 ≈ 20,5%.
    # Нужно 50 / (10 + 50) ≈ 83%.
    report = build_report("8h7h", "Ah Kh 2c 3d", "QcQd", pot=10, to_call=50)
    assert report.equity.share == pytest.approx(9 / 44)
    assert report.action == "fold"


def test_check_when_nothing_to_call():
    report = build_report("AsAh", "", "KdKh", pot=10, to_call=0, trials=200, seed=1)
    assert report.hand_name == "пара"
    assert report.required_equity is None
    assert report.action == "check"


def test_negative_money_rejected():
    with pytest.raises(ValueError):
        build_report("AsKh", "Td 9c 2s", "QQ", pot=-1, to_call=0)
