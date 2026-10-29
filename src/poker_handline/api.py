from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from poker_handline.narrate import TemplateNarrator
from poker_handline.report import build_report


class AnalyzeIn(BaseModel):
    hero: str
    board: str = ""
    villain: str
    pot: int
    to_call: int


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        page = Path(__file__).parent / "web" / "index.html"
        return HTMLResponse(page.read_text(encoding="utf-8"))

    @app.post("/api/analyze")
    def analyze(body: AnalyzeIn):
        try:
            report = build_report(body.hero, body.board, body.villain, body.pot, body.to_call)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"error": str(exc)})
        return {
            "hand_name": report.hand_name,
            "equity_share": report.equity.share,
            "required_equity": report.required_equity,
            "action": report.action,
            "method": report.equity.method,
            "narration": TemplateNarrator().narrate(report),
        }

    return app
