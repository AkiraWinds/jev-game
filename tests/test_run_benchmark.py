import pytest

from jev_game.judge_jev import JevJudgment
from jev_game.judge_llm import LlmJudgment
from jev_game.round_runner import RoundResult, percentile
from jev_game.run_benchmark import run_benchmark


def test_percentile_linear_interpolation():
    values = [1.0, 2.0, 3.0, 4.0]
    assert percentile(values, 0) == 1.0
    assert percentile(values, 100) == 4.0
    assert percentile(values, 50) == pytest.approx(2.5)


def test_percentile_empty_returns_none():
    assert percentile([], 50) is None


@pytest.mark.asyncio
async def test_run_benchmark_reports_accuracy_latency_and_stability(monkeypatch, tmp_path):
    scenarios_path = tmp_path / "scenarios.json"
    scenarios_path.write_text(
        """
        [
          {
            "id": 1,
            "title": "The Locked Study",
            "background": "bg",
            "victim": "Mr. Grey",
            "key_evidence": "evidence",
            "characters": ["Ava", "Ben"],
            "character_info": {"Ava": {"role": "butler", "relationship_to_victim": "employee", "motive": "fired"},
                                "Ben": {"role": "nephew", "relationship_to_victim": "heir", "motive": "debts"}},
            "killer": "Ben",
            "timeline": {"Ava": "dining room", "Ben": "study"},
            "statements": {"Ava": "garden", "Ben": "around"}
          }
        ]
        """
    )

    # jev flips its answer across repeats (unstable, half-correct); slm and
    # llm are both consistent and always correct.
    jev_choices = iter(["Ben", "Ava"])

    async def fake_run_round(scenario):
        jev_choice = next(jev_choices)
        return RoundResult(
            scenario_id=scenario.id,
            killer=scenario.killer,
            jev=JevJudgment(choice=jev_choice, confidence=0.9, probabilities={}, latency_ms=100.0),
            slm=LlmJudgment(choice="Ben", confidence=0.5, latency_ms=200.0),
            llm=LlmJudgment(choice="Ben", confidence=0.6, latency_ms=300.0),
            jev_correct=jev_choice == scenario.killer,
            slm_correct=True,
            llm_correct=True,
        )

    monkeypatch.setattr("jev_game.run_benchmark.run_round", fake_run_round)

    report = await run_benchmark(repeats=2, scenarios_path=str(scenarios_path))

    assert report["jev"]["rounds"] == 2
    assert report["jev"]["accuracy"] == 0.5
    assert report["jev"]["stability_rate"] == 0.0
    assert report["jev"]["avg_latency_s"] == pytest.approx(0.1)
    assert report["jev"]["p50_latency_s"] == pytest.approx(0.1)

    assert report["slm"]["accuracy"] == 1.0
    assert report["slm"]["stability_rate"] == 1.0
    assert report["llm"]["accuracy"] == 1.0
    assert report["llm"]["stability_rate"] == 1.0
