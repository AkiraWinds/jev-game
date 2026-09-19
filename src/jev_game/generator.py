"""Offline statement generation: an LLM writes each character's alibi line.

This is intentionally kept separate from judging. It is only ever invoked by
generate_scenarios.py to pre-bake scenarios.json, so its latency never leaks
into the Jev-vs-LLM judge comparison at run time.
"""

import json

from anthropic import AsyncAnthropic

from jev_game.config import ANTHROPIC_API_KEY, GENERATOR_MODEL

_SYSTEM_PROMPT = """\
You are writing short in-character alibi statements for a murder-mystery \
party game. You will be given a list of characters and told, privately, \
which one is secretly the killer.

Rules:
- Write 2-3 sentences per character, in first person.
- Innocent characters give a truthful, mildly detailed account of their \
whereabouts at the time of the murder.
- The killer gives a statement that is subtly evasive or misleading, but \
must NOT confess or state anything impossible - it should read as \
plausible as the innocent statements.
- Do not mention who the killer is anywhere in the text of the statements.
- Respond with ONLY a JSON object mapping each character's name to their \
statement string. No markdown, no commentary.
"""


async def generate_statements(characters: list[dict], killer_name: str) -> dict[str, str]:
    """Call the generator LLM once and return {name: statement}."""
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    roster = "\n".join(f"- {c['name']}, {c['role']}" for c in characters)
    user_prompt = (
        f"Characters:\n{roster}\n\n"
        f"The killer is: {killer_name}\n\n"
        "Write the JSON object of statements now."
    )
    response = await client.messages.create(
        model=GENERATOR_MODEL,
        max_tokens=800,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return json.loads(text)
