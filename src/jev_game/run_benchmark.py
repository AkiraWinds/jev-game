"""Batch benchmark: runs every pre-generated scenario through all three
judges, optionally several times each, and reports accuracy, p50/p95
latency (seconds), and repeated-run stability.

Stability here means: for a given scenario and judge, do all `--repeats`
independent calls agree on the same killer? A judge that flips its answer
across repeats on the same fixed input is unreliable even if its
single-shot accuracy looks fine.

    python -m jev_game.run_benchmark --repeats 3
"""

import argparse
import asyncio
import json
from dataclasses import dataclass, field

from jev_game.config import SCENARIOS_PATH
from jev_game.judge_jev import close_client as close_jev_client
from jev_game.judge_llm import close_client as close_llm_client
from jev_game.round_runner import percentile, run_round
from jev_game.scenarios import load_scenarios

JUDGES = ("jev", "slm", "llm")


@dataclass
class JudgeTally:
    latencies_s: list[float] = field(default_factory=list)
    correct: int = 0
    total: int = 0
    consistent_scenarios: int = 0
    scenarios: int = 0

    def summary(self) -> dict:
        return {
            "rounds": self.total,
            "accuracy": self.correct / self.total if self.total else None,
            "avg_latency_s": sum(self.latencies_s) / self.total if self.total else None,
            "p50_latency_s": percentile(self.latencies_s, 50),
            "p95_latency_s": percentile(self.latencies_s, 95),
            "stability_rate": self.consistent_scenarios / self.scenarios if self.scenarios else None,
        }


async def run_benchmark(repeats: int, scenarios_path: str) -> dict:
    scenarios = load_scenarios(scenarios_path)
    tallies = {name: JudgeTally() for name in JUDGES}

    for scenario in scenarios:
        choices = {name: [] for name in JUDGES}
        for _ in range(repeats):
            result = await run_round(scenario)
            for name in JUDGES:
                judgment = getattr(result, name)
                tally = tallies[name]
                tally.latencies_s.append(judgment.latency_ms / 1000)
                tally.total += 1
                tally.correct += int(getattr(result, f"{name}_correct"))
                choices[name].append(judgment.choice)
        for name in JUDGES:
            tallies[name].scenarios += 1
            if len(set(choices[name])) == 1:
                tallies[name].consistent_scenarios += 1

    return {name: tallies[name].summary() for name in JUDGES}


def _fmt(report: dict) -> str:
    lines = []
    for name, s in report.items():
        lines.append(
            f"{name:>3}: rounds={s['rounds']:>3} "
            f"accuracy={s['accuracy']:.0%} "
            f"p50={s['p50_latency_s']:.3f}s p95={s['p95_latency_s']:.3f}s "
            f"avg={s['avg_latency_s']:.3f}s "
            f"stability={s['stability_rate']:.0%}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3, help="independent calls per scenario per judge")
    parser.add_argument("--scenarios", type=str, default=SCENARIOS_PATH)
    parser.add_argument("--json", action="store_true", help="print raw JSON instead of a formatted table")
    args = parser.parse_args()

    async def _run() -> dict:
        try:
            return await run_benchmark(args.repeats, args.scenarios)
        finally:
            await close_jev_client()
            await close_llm_client()

    report = asyncio.run(_run())
    print(json.dumps(report, indent=2) if args.json else _fmt(report))


if __name__ == "__main__":
    main()
