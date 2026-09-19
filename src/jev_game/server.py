"""FastAPI app: serves the comparison page and runs one round per request.

Run with:
    uvicorn jev_game.server:app --reload
"""

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from jev_game.config import SCENARIOS_PATH
from jev_game.round_runner import Scoreboard, run_round
from jev_game.scenarios import load_scenarios

app = FastAPI(title="Jev vs LLM Mafia Judge")

_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

scoreboard = Scoreboard()
_next_index = 0
_scenarios = None


def _get_scenarios():
    global _scenarios
    if _scenarios is None:
        _scenarios = load_scenarios(SCENARIOS_PATH)
    return _scenarios


@app.get("/")
def index():
    return FileResponse(_static_dir / "index.html")


@app.post("/api/round")
async def play_round():
    global _next_index
    scenarios = _get_scenarios()
    if _next_index >= len(scenarios):
        raise HTTPException(status_code=409, detail="No more pre-generated scenarios left.")
    scenario = scenarios[_next_index]
    _next_index += 1
    result = await run_round(scenario)
    scoreboard.record(result)
    return {
        "scenario_id": result.scenario_id,
        "title": scenario.title,
        "background": scenario.background,
        "victim": scenario.victim,
        "characters": scenario.characters,
        "character_info": scenario.character_info,
        "statements": scenario.statements,
        "killer": result.killer,
        "jev": asdict(result.jev),
        "llm": asdict(result.llm),
        "jev_correct": result.jev_correct,
        "llm_correct": result.llm_correct,
        "summary": scoreboard.summary(),
        "remaining": len(scenarios) - _next_index,
    }


@app.get("/api/scoreboard")
def get_scoreboard():
    return scoreboard.summary()
