"""Judge A: TypeSafe's Jev model, asked a single Choice question per round."""

import time
from dataclasses import dataclass

from typesafe_sdk import AsyncTypeSafeClient, Choice

from jev_game.config import JEV_MODEL, TYPESAFE_API_KEY


@dataclass
class JevJudgment:
    choice: str
    confidence: float
    probabilities: dict[str, float]
    latency_ms: float


async def judge_with_jev(statements: dict[str, str]) -> JevJudgment:
    criteria = {
        name: f"{name} is the killer and gave the evasive/misleading statement."
        for name in statements
    }
    start = time.perf_counter()
    async with AsyncTypeSafeClient(api_key=TYPESAFE_API_KEY) as client:
        response = await client.system_one(
            model=JEV_MODEL,
            state={"statements": statements},
            questions={
                "killer": Choice(
                    instructions=(
                        "Each character gave a statement about their whereabouts "
                        "during a murder. Exactly one of them is the killer and is "
                        "being evasive or misleading. Identify who is most likely "
                        "the killer."
                    ),
                    criteria=criteria,
                ),
            },
        )
    latency_ms = (time.perf_counter() - start) * 1000
    answer = response.choices["killer"]
    return JevJudgment(
        choice=answer.choice,
        confidence=answer.confidence,
        probabilities=dict(answer.probabilities),
        latency_ms=latency_ms,
    )
