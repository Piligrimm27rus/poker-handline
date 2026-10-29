import argparse
import os
import sys
from collections.abc import Callable

from poker_handline.narrate import LLMNarrator, TemplateNarrator
from poker_handline.report import HandReport, build_report

_LLM_BASE = "POKER_HANDLINE_LLM_BASE_URL"
_LLM_KEY = "POKER_HANDLINE_LLM_API_KEY"
_LLM_MODEL = "POKER_HANDLINE_LLM_MODEL"


def main(argv: list[str] | None = None, narrator_factory: Callable[[], object] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="poker-handline")
    parser.add_argument("--hero", required=True)
    parser.add_argument("--villain", required=True)
    parser.add_argument("--board", default="")
    parser.add_argument("--pot", type=int, required=True)
    parser.add_argument("--to-call", type=int, required=True, dest="to_call")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        report = build_report(
            args.hero,
            args.board,
            args.villain,
            args.pot,
            args.to_call,
            trials=args.trials,
            seed=args.seed,
        )
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    try:
        paragraph = _narrator(narrator_factory).narrate(report)
    except Exception:
        paragraph = TemplateNarrator().narrate(report)
    print(_render(report))
    print("---")
    print(paragraph)
    return 0


def _narrator(factory: Callable[[], object] | None):
    if factory is not None:
        return factory()
    base_url = os.environ.get(_LLM_BASE)
    api_key = os.environ.get(_LLM_KEY)
    model = os.environ.get(_LLM_MODEL)
    if base_url and api_key and model:
        return LLMNarrator(base_url, api_key, model)
    return TemplateNarrator()


def _render(report: HandReport) -> str:
    equity = report.equity
    if report.required_equity is None:
        price = "нет"
    else:
        price = _percent(report.required_equity)
    return "\n".join(
        (
            f"Рука: {report.hand_name}",
            (
                f"Эквити: {_percent(equity.share)} "
                f"(win {_points(equity.win)} / tie {_points(equity.tie)} / lose {_points(equity.lose)}), "
                f"{equity.method}, {equity.trials} раскладов"
            ),
            f"Нужно для колла: {price}",
            f"Решение: {report.action}",
        )
    )


def _percent(value: float) -> str:
    return _points(value) + "%"


def _points(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",")


if __name__ == "__main__":
    raise SystemExit(main())
