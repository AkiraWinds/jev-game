"""Offline step: pre-design N whodunit cases and write them to scenarios.json.

Run this once before starting the server:

    python -m jev_game.generate_scenarios --rounds 5

Each round: design a full case (background, victim, characters,
relationships, motives, ground-truth killer, and true timeline), then write
each character's spoken statement to match it. The server then only ever
reads scenarios.json, so judge-vs-judge timing never includes any of this
generation latency.
"""

import argparse
import asyncio
import random

from jev_game.case_generator import generate_case
from jev_game.config import SCENARIOS_PATH
from jev_game.generator import generate_statements
from jev_game.scenarios import Scenario, save_scenarios
from jev_game.settings import SETTING_SEEDS


async def build_scenarios(rounds: int, seed: int | None) -> list[Scenario]:
    rng = random.Random(seed)
    scenarios = []
    for round_id in range(1, rounds + 1):
        setting_seed = rng.choice(SETTING_SEEDS)
        case = await generate_case(setting_seed)
        statements = await generate_statements(case)

        names = [c["name"] for c in case["characters"]]
        character_info = {
            c["name"]: {
                "role": c["role"],
                "relationship_to_victim": c["relationship_to_victim"],
                "motive": c["motive"],
            }
            for c in case["characters"]
        }
        scenarios.append(
            Scenario(
                id=round_id,
                title=case["title"],
                background=case["background"],
                victim=case["victim"],
                characters=names,
                character_info=character_info,
                killer=case["killer"],
                timeline=case["timeline"],
                statements=statements,
            )
        )
        print(f"generated round {round_id}/{rounds}: {case['title']!r} (killer hidden from output)")
    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=str, default=SCENARIOS_PATH)
    args = parser.parse_args()

    scenarios = asyncio.run(build_scenarios(args.rounds, args.seed))
    save_scenarios(args.out, scenarios)
    print(f"wrote {len(scenarios)} scenarios to {args.out}")


if __name__ == "__main__":
    main()
