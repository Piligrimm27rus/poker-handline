import pytest

from poker_handline.cli import main


def test_cli_prints_call(capsys):
    code = main(
        ["--hero", "AhKh", "--board", "Qh Jh Th 2c 3d", "--villain", "2d2s", "--pot", "100", "--to-call", "50"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Рука: роял-флеш" in out
    assert "Решение: call" in out
    assert "100,0%" in out
    assert "колл" in out


def test_cli_rejects_bad_cards(capsys):
    code = main(["--hero", "AxKh", "--villain", "QQ", "--pot", "10", "--to-call", "0"])
    err = capsys.readouterr().err
    assert code == 2
    assert err
