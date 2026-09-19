import pytest

from jev_game.judge_jev import JevJudgment
from jev_game.judge_llm import LlmJudgment
from jev_game.round_runner import Scoreboard, run_round
from jev_game.scenarios import Scenario


@pytest.fixture
def scenario():
    return Scenario(
        id=1,
        characters=["Ava", "Ben"],
        killer="Ben",
        statements={"Ava": "I was in the garden.", "Ben": "I was... around."},
    )


@pytest.mark.asyncio
async def test_run_round_scores_correctness(scenario, monkeypatch):
    async def fake_jev(statements):
        return JevJudgment(choice="Ben", confidence=0.9, probabilities={"Ava": 0.1, "Ben": 0.9}, latency_ms=120.0)

    async def fake_llm(statements):
        return LlmJudgment(choice="Ava", confidence=0.6, latency_ms=800.0)

    monkeypatch.setattr("jev_game.round_runner.judge_with_jev", fake_jev)
    monkeypatch.setattr("jev_game.round_runner.judge_with_llm", fake_llm)

    result = await run_round(scenario)

    assert result.jev_correct is True
    assert result.llm_correct is False
    assert result.jev.latency_ms == 120.0
    assert result.llm.latency_ms == 800.0


def test_scoreboard_summary_tracks_accuracy_and_latency():
    board = Scoreboard()
    assert board.summary()["jev"]["rounds"] == 0

    board.record(
        _fake_result(scenario_id=1, jev_correct=True, llm_correct=False, jev_ms=100.0, llm_ms=900.0)
    )
    board.record(
        _fake_result(scenario_id=2, jev_correct=True, llm_correct=True, jev_ms=140.0, llm_ms=700.0)
    )

    summary = board.summary()
    assert summary["jev"]["rounds"] == 2
    assert summary["jev"]["accuracy"] == 1.0
    assert summary["jev"]["avg_latency_ms"] == 120.0
    assert summary["llm"]["accuracy"] == 0.5
    assert summary["llm"]["avg_latency_ms"] == 800.0


def _fake_result(scenario_id, jev_correct, llm_correct, jev_ms, llm_ms):
    from jev_game.round_runner import RoundResult

    return RoundResult(
        scenario_id=scenario_id,
        killer="Ben",
        jev=JevJudgment(choice="Ben", confidence=0.9, probabilities={}, latency_ms=jev_ms),
        llm=LlmJudgment(choice="Ben", confidence=0.7, latency_ms=llm_ms),
        jev_correct=jev_correct,
        llm_correct=llm_correct,
    )
