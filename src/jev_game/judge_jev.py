"""Judge A: TypeSafe's Jev model, asked a single Choice question per round."""

import time
from dataclasses import dataclass

from typesafe_sdk import AsyncTypeSafeClient, Choice

from jev_game.config import JEV_MODEL, TYPESAFE_API_KEY

# A fresh client per call would pay a new TCP/TLS handshake every round,
# which dwarfs any real difference in model latency. Reuse one client (with
# a persistent connection pool) for the life of the process instead.
_client: AsyncTypeSafeClient | None = None


def _get_client() -> AsyncTypeSafeClient:
    global _client
    if _client is None:
        _client = AsyncTypeSafeClient(api_key=TYPESAFE_API_KEY)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@dataclass
class JevJudgment:
    choice: str
    confidence: float
    probabilities: dict[str, float]
    latency_ms: float


async def judge_with_jev(public_state: dict) -> JevJudgment:
    character_info = public_state["characters"]
    criteria = {
        name: (
            f"{name} ({info['role']}, relationship to victim: "
            f"{info['relationship_to_victim']}, possible motive: {info['motive']}) "
            "is the killer."
        )
        for name, info in character_info.items()
    }
    state = {
        "title": public_state["title"],
        "background": public_state["background"],
        "victim": public_state["victim"],
        "characters": character_info,
        "statements": public_state["statements"],
    }
    client = _get_client()
    start = time.perf_counter()
    response = await client.system_one(
        model=JEV_MODEL,
        state=state,
        questions={
            "killer": Choice(
                instructions=(
                    "This is a murder mystery. Given the background, each "
                    "character's relationship to the victim and possible "
                    "motive, and each character's statement about their "
                    "whereabouts, exactly one character is the killer and is "
                    "being evasive or misleading in their statement. Identify "
                    "who is most likely the killer."
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
