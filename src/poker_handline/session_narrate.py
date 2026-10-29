import json

import httpx

BANDS = {
    "vpip": (0.22, 0.28),
    "pfr": (0.18, 0.23),
    "wtsd": (0.24, 0.30),
    "wsd": (0.50, 0.56),
    "cbet_flop": (0.60, 0.75),
}

_LABELS = {
    "vpip": "VPIP",
    "pfr": "PFR",
    "wtsd": "WTSD",
    "wsd": "W$SD",
    "cbet_flop": "CBet флоп",
}
_SYSTEM = (
    "Ты объясняешь уже посчитанную статистику сессии NLHE. Пиши по-русски.\n"
    "Не пересчитывай проценты. Повтори цифры из JSON и не обещай винрейт."
)


def narrate_session(summary: dict) -> str:
    lines = [
        f"Рук: {summary['hands']}",
        _percent_line("VPIP", summary["vpip"]),
        _percent_line("PFR", summary["pfr"]),
        _percent_line("3bet", summary["three_bet"]),
        _af_line(summary["af"]),
        _percent_line("CBet флоп", summary["cbet_flop"]),
        _percent_line("WTSD", summary["wtsd"]),
        _percent_line("W$SD", summary["wsd"]),
        f"Результат: {_one_decimal(summary['net_bb'])} бб",
        "",
        *_band_lines(summary),
    ]
    return "\n".join(lines)


class LLMSessionNarrator:
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

    def narrate(self, summary: dict) -> str:
        with httpx.Client(transport=self.transport, timeout=30) as client:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": json.dumps(summary, ensure_ascii=False)},
                    ],
                },
            )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        quote = _percent(summary["vpip"])
        if quote not in text:
            raise ValueError("session narration does not quote the calculated VPIP")
        return text


def _band_lines(summary: dict) -> list[str]:
    lines: list[str] = []
    for key, (low, high) in BANDS.items():
        value = summary.get(key)
        if value is None or low <= value <= high:
            continue
        direction = "выше" if value > high else "ниже"
        lines.append(
            f"{_LABELS[key]} {_percent(value)} {direction} учебного коридора {_corridor(low, high)}."
        )
    vpip = summary.get("vpip")
    pfr = summary.get("pfr")
    if vpip is not None and pfr is not None and vpip - pfr > 0.08:
        lines.append("Разрыв VPIP и PFR больше 8%.")
    return lines


def _percent_line(label: str, value: float | None) -> str:
    if value is None:
        return f"{label}: нет"
    return f"{label} {_percent(value)}"


def _af_line(value: float | None) -> str:
    if value is None:
        return "AF: нет"
    return f"AF: {_one_decimal(value)}"


def _percent(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",") + "%"


def _one_decimal(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def _corridor(low: float, high: float) -> str:
    return f"{round(low * 100)}–{round(high * 100)}%"
