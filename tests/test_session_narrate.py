import json

import httpx
import pytest

from poker_handline.session_narrate import LLMSessionNarrator, narrate_session
from poker_handline.stats import load_session, summarize


def test_template_flags_only_the_bands_this_fixture_misses():
    text = narrate_session(summarize(load_session("tests/fixtures/session_six_hands.json")))
    for line in (
        "VPIP 83,3% выше учебного коридора 22–28%.",
        "PFR 66,7% выше учебного коридора 18–23%.",
        "W$SD 0,0% ниже учебного коридора 50–56%.",
        "CBet флоп 50,0% ниже учебного коридора 60–75%.",
        "Разрыв VPIP и PFR больше 8%.",
    ):
        assert line in text
    assert "WTSD 25,0% выше" not in text
    assert "WTSD 25,0% ниже" not in text


def test_llm_session_narrator_must_quote_vpip():
    summary = summarize(load_session("tests/fixtures/session_six_hands.json"))

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert "Не пересчитывай проценты" in body["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "Сессия нормальная."}}]})

    narrator = LLMSessionNarrator(
        "http://llm.test/v1", "test-key", "test-model", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ValueError):
        narrator.narrate(summary)
