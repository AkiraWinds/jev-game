"""Loading and saving pre-generated scenarios.json.

A scenario is one round's fixed content: a designed case (title, background,
victim, characters with relationships/motives) plus the ground-truth killer,
each character's true timeline, and their pre-generated public statement.
Judges read scenarios at run time; nothing here calls an LLM.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Scenario:
    id: int
    title: str
    background: str
    victim: str
    characters: list[str]
    character_info: dict[str, dict[str, str]]
    killer: str
    timeline: dict[str, str]
    statements: dict[str, str]

    def public_state(self) -> dict:
        """State visible to judges - excludes the killer and true timeline."""
        return {
            "title": self.title,
            "background": self.background,
            "victim": self.victim,
            "characters": self.character_info,
            "statements": self.statements,
        }


def load_scenarios(path: str) -> list[Scenario]:
    data = json.loads(Path(path).read_text())
    return [Scenario(**item) for item in data]


def save_scenarios(path: str, scenarios: list[Scenario]) -> None:
    Path(path).write_text(json.dumps([asdict(s) for s in scenarios], indent=2))
