"""Offline step: given a designed case, write each character's spoken line.

Takes the case dict produced by case_generator.py (background, victim, key
evidence, characters, killer, true timeline) and writes what each character
actually says. This is only ever invoked by generate_scenarios.py, so its
latency never leaks into the Jev-vs-LLM judge comparison at run time.

Uses a different OpenAI model than judge_llm.py so Judge B is never
evaluating text produced by its own weights/style.
"""

import json

from openai import AsyncOpenAI

from jev_game.config import GENERATOR_MODEL, OPENAI_API_KEY

_SYSTEM_PROMPT_TEMPLATE = """\
You are writing short in-character statements for a murder-mystery party \
game, based on a case you will be given: its background, victim, key \
evidence, characters, the true killer, and each character's true timeline.

Rules:
- Write 2-3 sentences per character, in first person.
- There are __N__ characters. All __N__ statements must be equally \
specific, equally confident, and similar in length and tone. Do NOT make \
the killer's statement vaguer, shorter, hedging, or less detailed than the \
others - that would give away the answer by writing style alone, which is \
not the point of this exercise.
- Every character except the killer gives a statement consistent with \
both their true timeline entry AND the key evidence.
- The killer's statement must contain exactly one concrete, checkable \
factual claim (a specific time, place, or corroborating detail) that \
directly contradicts the key evidence. This is the one fair clue that \
solves the case - it must be a checkable fact, not a vague or evasive tone.
- The killer must NOT confess and must NOT state anything that sounds \
inherently suspicious - only a careful reader cross-checking the key \
evidence should be able to catch the contradiction.
- Do not mention who the killer is anywhere in the text of the statements.
- Respond with ONLY a JSON object mapping each character's name to their \
statement string. No markdown, no commentary.
"""


async def generate_statements(case: dict) -> dict[str, str]:
    """Call the generator LLM once and return {name: statement}."""
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    user_prompt = json.dumps(
        {
            "background": case["background"],
            "victim": case["victim"],
            "key_evidence": case["key_evidence"],
            "characters": case["characters"],
            "killer": case["killer"],
            "timeline": case["timeline"],
        }
    )
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.replace("__N__", str(len(case["characters"])))
    response = await client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
