"""Judge B: a plain chat LLM, prompted to answer the same question as Jev.

Note: this model's "confidence" is self-reported by the model, not a
calibrated probability the way Jev's is. That gap is part of what this
project is trying to surface, not a bug to paper over.
"""

import json
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from jev_game.config import JUDGE_LLM_MODEL, OPENAI_API_KEY

_SYSTEM_PROMPT = """\
You are a careful detective judging a murder-mystery round. You will be \
given the case background, the victim, each character's relationship to \
the victim and possible motive, and each character's statement about their \
whereabouts. Exactly one of them is the killer and is being evasive or \
misleading in their statement.

Respond with ONLY a JSON object of the form:
{"killer": "<one of the given names, exactly as spelled>", "confidence": <number between 0 and 1>}
No markdown, no commentary.
"""


@dataclass
class LlmJudgment:
    choice: str
    confidence: float
    latency_ms: float


async def judge_with_llm(public_state: dict) -> LlmJudgment:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    user_prompt = json.dumps(public_state)
    start = time.perf_counter()
    response = await client.chat.completions.create(
        model=JUDGE_LLM_MODEL,
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
