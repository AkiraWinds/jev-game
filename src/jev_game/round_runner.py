"""Runs one pre-generated scenario through all three judges and scores them."""

import asyncio
from dataclasses import dataclass, field

from jev_game.judge_jev import JevJudgment, judge_with_jev
from jev_game.judge_llm import LlmJudgment, judge_with_llm, judge_with_slm
from jev_game.scenarios import Scenario


def percentile(values: list[float], pct: float) -> float | None:
    """Linear-interpolated percentile (0-100) of a list of numbers."""
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (pct / 100)
    lo, hi = int(rank), min(int(rank) + 1, len(ordered) - 1)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)


@dataclass
class RoundResult:
    scenario_id: int
    killer: str
    jev: JevJudgment
    slm: LlmJudgment
    llm: LlmJudgment
    jev_correct: bool
    slm_correct: bool
    llm_correct: bool


async def run_round(scenario: Scenario) -> RoundResult:
    public_state = scenario.public_state()
    jev_result, slm_result, llm_result = await asyncio.gather(
        judge_with_jev(public_state),
        judge_with_slm(public_state),
        judge_with_llm(public_state),
    )
    return RoundResult(
        scenario_id=scenario.id,
        killer=scenario.killer,
        jev=jev_result,
        slm=slm_result,
        llm=llm_result,
        jev_correct=jev_result.choice == scenario.killer,
        slm_correct=slm_result.choice == scenario.killer,
        llm_correct=llm_result.choice == scenario.killer,
    )


@dataclass
class Scoreboard:
    rounds: list[RoundResult] = field(default_factory=list)

    def record(self, result: RoundResult) -> None:
        self.rounds.append(result)

    def _summary(self, correct_attr: str, latency_attr: str) -> dict:
        n = len(self.rounds)
        if n == 0:
            return {
                "rounds": 0,
                "accuracy": None,
                "avg_latency_ms": None,
                "avg_latency_s": None,
                "p50_latency_s": None,
                "p95_latency_s": None,
            }
        correct = sum(1 for r in self.rounds if getattr(r, correct_attr))
        latencies_ms = [getattr(r, latency_attr).latency_ms for r in self.rounds]
        latencies_s = [ms / 1000 for ms in latencies_ms]
        return {
            "rounds": n,
            "accuracy": correct / n,
            "avg_latency_ms": sum(latencies_ms) / n,
            "avg_latency_s": sum(latencies_s) / n,
            "p50_latency_s": percentile(latencies_s, 50),
            "p95_latency_s": percentile(latencies_s, 95),
        }

    def summary(self) -> dict:
        return {
            "jev": self._summary("jev_correct", "jev"),
            "slm": self._summary("slm_correct", "slm"),
            "llm": self._summary("llm_correct", "llm"),
        }
