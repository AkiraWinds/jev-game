"""Runs one pre-generated scenario through both judges and scores them."""

import asyncio
from dataclasses import dataclass, field

from jev_game.judge_jev import JevJudgment, judge_with_jev
from jev_game.judge_llm import LlmJudgment, judge_with_llm
from jev_game.scenarios import Scenario


@dataclass
class RoundResult:
    scenario_id: int
    killer: str
    jev: JevJudgment
    llm: LlmJudgment
    jev_correct: bool
    llm_correct: bool


async def run_round(scenario: Scenario) -> RoundResult:
    public_state = scenario.public_state()
    jev_result, llm_result = await asyncio.gather(
        judge_with_jev(public_state),
        judge_with_llm(public_state),
    )
    return RoundResult(
        scenario_id=scenario.id,
        killer=scenario.killer,
        jev=jev_result,
        llm=llm_result,
        jev_correct=jev_result.choice == scenario.killer,
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
            return {"rounds": 0, "accuracy": None, "avg_latency_ms": None}
        correct = sum(1 for r in self.rounds if getattr(r, correct_attr))
        total_latency = sum(getattr(r, latency_attr).latency_ms for r in self.rounds)
        return {
            "rounds": n,
            "accuracy": correct / n,
            "avg_latency_ms": total_latency / n,
        }

    def summary(self) -> dict:
        return {
            "jev": self._summary("jev_correct", "jev"),
            "llm": self._summary("llm_correct", "llm"),
        }
