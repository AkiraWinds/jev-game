"""Offline step: pre-generate N mafia rounds and write them to scenarios.json.

Run this once before starting the server:

    python -m jev_game.generate_scenarios --rounds 5

The server then only ever reads scenarios.json, so judge-vs-judge timing
never includes statement-generation latency.
"""

import argparse
import asyncio
import random

from jev_game.characters import pick_round_characters
from jev_game.config import SCENARIOS_PATH
from jev_game.generator import generate_statements
from jev_game.scenarios import Scenario, save_scenarios


async def build_scenarios(rounds: int, seed: int | None) -> list[Scenario]:
    rng = random.Random(seed)
    scenarios = []
    for round_id in range(1, rounds + 1):
        characters = pick_round_characters(rng)
        names = [c["name"] for c in characters]
        killer = rng.choice(names)
        statements = await generate_statements(characters, killer)
        scenarios.append(
            Scenario(id=round_id, characters=names, killer=killer, statements=statements)
        )
        print(f"generated round {round_id}/{rounds} (killer hidden from output)")
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
