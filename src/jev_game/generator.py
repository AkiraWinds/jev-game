"""Offline step: given a designed case, write each character's spoken line.

Takes the case dict produced by case_generator.py (background, victim,
characters, killer, true timeline) and writes what each character actually
says. This is only ever invoked by generate_scenarios.py, so its latency
never leaks into the Jev-vs-LLM judge comparison at run time.

Uses a different OpenAI model than judge_llm.py so Judge B is never
evaluating text produced by its own weights/style.
"""

import json

from openai import AsyncOpenAI

from jev_game.config import GENERATOR_MODEL, OPENAI_API_KEY

_SYSTEM_PROMPT = """\
You are writing short in-character statements for a murder-mystery party \
game, based on a case you will be given: its background, victim, \
characters, the true killer, and each character's true timeline.

Rules:
- Write 2-3 sentences per character, in first person.
- Every character except the killer gives a statement consistent with \
their true timeline entry.
- The killer's statement should subtly diverge from their true timeline - \
evasive or misleading, but must NOT confess or state anything impossible; \
it should read as plausible as the other statements.
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
            "characters": case["characters"],
            "killer": case["killer"],
            "timeline": case["timeline"],
        }
    )
    response = await client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
