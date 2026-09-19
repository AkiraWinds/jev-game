"""Judges B and C: plain chat models, prompted to answer the same question
as Jev - one a small model (SLM), one a large model (LLM).

Note: these models' "confidence" is self-reported by the model, not a
calibrated probability the way Jev's is. That gap is part of what this
project is trying to surface, not a bug to paper over.
"""

import json
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from jev_game.config import JUDGE_LLM_MODEL, JUDGE_SLM_MODEL, OPENAI_API_KEY

# A fresh client per call would pay a new TCP/TLS handshake every round,
# which dwarfs any real difference in model latency. Reuse one client (with
# a persistent connection pool) for the life of the process instead.
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


_SYSTEM_PROMPT = """\
You are a careful detective judging a murder-mystery round. You will be \
given the case background, the victim, a piece of key evidence, each \
character's relationship to the victim and possible motive, and each \
character's statement about their whereabouts. Exactly one character's \
statement contains a specific factual claim that contradicts the key \
evidence - that character is the killer. Cross-check each statement \
against the key evidence carefully before answering.

Respond with ONLY a JSON object of the form:
{"killer": "<one of the given names, exactly as spelled>", "confidence": <number between 0 and 1>}
No markdown, no commentary.
"""


@dataclass
class LlmJudgment:
    choice: str
    confidence: float
    latency_ms: float


async def _judge_with_model(public_state: dict, model: str) -> LlmJudgment:
    client = _get_client()
    user_prompt = json.dumps(public_state)
    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    latency_ms = (time.perf_counter() - start) * 1000
    payload = json.loads(response.choices[0].message.content)
    return LlmJudgment(
        choice=payload["killer"],
        confidence=float(payload["confidence"]),
        latency_ms=latency_ms,
    )


async def judge_with_slm(public_state: dict) -> LlmJudgment:
    return await _judge_with_model(public_state, JUDGE_SLM_MODEL)


async def judge_with_llm(public_state: dict) -> LlmJudgment:
    return await _judge_with_model(public_state, JUDGE_LLM_MODEL)
