from fastapi.testclient import TestClient

from poker_handline.api import create_app


def test_analyze_royal_flush():
    client = TestClient(create_app())
    response = client.post(
        "/api/analyze",
        json={"hero": "AhKh", "board": "Qh Jh Th 2c 3d", "villain": "2d2s", "pot": 100, "to_call": 50},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hand_name"] == "роял-флеш"
    assert body["action"] == "call"
    assert body["equity_share"] == 1.0
    assert body["required_equity"] == 50 / 150
    assert "100,0%" in body["narration"]
    assert "колл" in body["narration"]


def test_analyze_rejects_bad_cards():
    client = TestClient(create_app())
    response = client.post(
        "/api/analyze",
        json={"hero": "Ax", "board": "", "villain": "QQ", "pot": 10, "to_call": 0},
    )
    assert response.status_code == 400
    assert response.json()["error"]


def test_index_has_the_form():
    client = TestClient(create_app())
    text = client.get("/").text
    for piece in ("hero", "board", "villain", "pot", "to_call", "/api/analyze", "Разобрать"):
        assert piece in text
