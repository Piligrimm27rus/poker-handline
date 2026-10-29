import json
from typing import Protocol

import httpx

from poker_handline.report import HandReport

_ACTION_RU = {"fold": "фолд", "call": "колл", "check": "чек"}
_SYSTEM = (
    "Ты объясняешь уже посчитанный отчёт по одной раздаче NLHE. Пиши по-русски, 4–6 предложений.\n"
    "Повтори название руки, эквити и действие ровно такими, как в JSON. Не считай эквити заново.\n"
    "Не рекомендуй рейз и не меняй fold, call или check. Если действия check, не предлагай размер ставки."
)


class Narrator(Protocol):
    def narrate(self, report: HandReport) -> str: ...


class TemplateNarrator:
    def narrate(self, report: HandReport) -> str:
        share_pct = _percent(report.equity.share)
        if report.action == "check":
            return (
                f"{report.hand_name}. Эквити против {report.villain}: {share_pct}. "
                "Ставки для колла нет. Решение движка: чек.\n"
                "Размер ставки эта версия не рекомендует."
            )
        required = report.required_equity
        if required is None:
            raise ValueError("call or fold requires a price")
        action_ru = _ACTION_RU[report.action]
        return (
            f"{report.hand_name}. Эквити против {report.villain}: {share_pct}. "
            f"Для колла нужно {_percent(required)}. Решение движка: {action_ru}.\n"
            "Движок не оценивает фолд-эквити рейза и выбирает только колл или фолд."
        )


class LLMNarrator:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.transport = transport

    def narrate(self, report: HandReport) -> str:
        payload = {
            "hand_name": report.hand_name,
            "villain": report.villain,
            "equity_share": report.equity.share,
            "required_equity": report.required_equity,
            "action": report.action,
            "method": report.equity.method,
        }
        with httpx.Client(transport=self.transport, timeout=30) as client:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                    ],
                },
            )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        if not _quotes_report(report, text):
            raise ValueError("narration does not quote the engine report")
        return text


def _percent(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",") + "%"


def _quotes_report(report: HandReport, text: str) -> bool:
    return (
        report.hand_name in text
        and _percent(report.equity.share) in text
        and _ACTION_RU[report.action] in text
    )
