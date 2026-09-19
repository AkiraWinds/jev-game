"""Loading and saving pre-generated scenarios.json.

A scenario is one round's fixed content: which characters appear, who the
ground-truth killer is, and each character's pre-generated statement. Judges
read scenarios at run time; nothing here calls an LLM.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Scenario:
    id: int
    characters: list[str]
    killer: str
    statements: dict[str, str]


def load_scenarios(path: str) -> list[Scenario]:
    data = json.loads(Path(path).read_text())
    return [Scenario(**item) for item in data]


def save_scenarios(path: str, scenarios: list[Scenario]) -> None:
    Path(path).write_text(json.dumps([asdict(s) for s in scenarios], indent=2))
