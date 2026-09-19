"""Offline step: design one whodunit case before any statements are written.

A case fixes the background, victim, characters (with relationships and
motives), the ground-truth killer, and each character's true timeline. It is
invented fresh per round from a generic setting seed - never copied from a
specific existing book, show, or film. generator.py then writes each
character's spoken statement to be consistent (or, for the killer, subtly
inconsistent) with this case.
"""

import json

from openai import AsyncOpenAI

from jev_game.config import GENERATOR_MODEL, OPENAI_API_KEY
from jev_game.settings import CHARACTERS_PER_ROUND

_SYSTEM_PROMPT_TEMPLATE = """\
You are a mystery writer designing one whodunit case for a party game. \
Invent original characters and an original plot for this case - do not \
reuse characters, names, or plots from any specific existing book, show, \
or film. You will be given a one-line setting seed as inspiration only.

Respond with ONLY a JSON object of this exact shape:
{
  "title": "short case title",
  "background": "2-4 sentences: the setting, the victim, and how the body was found",
  "victim": "name of the victim",
  "characters": [
    {"name": "...", "role": "...", "relationship_to_victim": "...", "motive": "..."}
  ],
  "killer": "must exactly match one of the characters' name fields",
  "timeline": {
    "<character name>": "1 sentence: where this character actually was and what they actually did at the time of the murder - the ground truth, which may differ from what they will later claim"
  }
}
"characters" must have exactly __N__ entries, one per name, and "timeline" \
must have exactly one entry per character name. Exactly one character is \
the killer. No markdown, no commentary.
"""


async def generate_case(setting_seed: str) -> dict:
    """Call the generator LLM once and return a full case dict."""
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.replace("__N__", str(CHARACTERS_PER_ROUND))
    user_prompt = f"Setting inspiration: {setting_seed}"
    response = await client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    case = json.loads(response.choices[0].message.content)

    names = {c["name"] for c in case["characters"]}
    if len(case["characters"]) != CHARACTERS_PER_ROUND:
        raise ValueError(f"expected {CHARACTERS_PER_ROUND} characters, got {len(case['characters'])}")
    if case["killer"] not in names:
        raise ValueError(f"killer {case['killer']!r} is not among characters {names}")
    if set(case["timeline"]) != names:
        raise ValueError(f"timeline keys {set(case['timeline'])} do not match characters {names}")
    return case
