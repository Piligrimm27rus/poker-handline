import json

import httpx
import pytest

from poker_handline.narrate import LLMNarrator, TemplateNarrator
from poker_handline.report import build_report


def test_template_call_quotes_engine_numbers():
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)
    text = TemplateNarrator().narrate(report)
    assert "роял-флеш" in text
    assert "100,0%" in text
    assert "33,3%" in text
    assert "колл" in text
    assert "рейза" in text


def test_template_check_does_not_invent_a_bet():
    report = build_report("AsAh", "", "KdKh", pot=10, to_call=0, trials=50, seed=1)
    text = TemplateNarrator().narrate(report)
    assert "чек" in text
    assert "не рекомендует" in text


def test_llm_narrator_rejects_a_changed_action():
    report = build_report("AhKh", "Qh Jh Th 2c 3d", "2d2s", pot=100, to_call=50)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert "Не считай эквити заново" in body["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Лучше рейз."}}]})

    transport = httpx.MockTransport(handler)
    narrator = LLMNarrator("http://llm.test/v1", "test-key", "test-model", transport=transport)
    with pytest.raises(ValueError):
        narrator.narrate(report)
