"""Offline step: design one whodunit case before any statements are written.

A case fixes the background, victim, characters (with relationships and
motives), a piece of independent key evidence, the ground-truth killer, and
each character's true timeline. It is invented fresh per round from a
generic setting seed - never copied from a specific existing book, show, or
film. generator.py then writes each character's spoken statement: three
consistent with this case, and the killer's containing one concrete,
checkable contradiction with the key evidence (a "fair play" clue, per the
classic whodunit convention that a clue must be present and checkable, not
just implied by tone).
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
  "background": "2-4 sentences: the setting, the victim, how the body was found, AND exactly one concrete connecting fact about the crime scene or its access - e.g. it has exactly one door or entrance, only one person holds the key, a window is welded shut, the only path in passes a single guarded checkpoint, the room can only be reached by one staircase, etc. This connecting fact must be load-bearing: solving the case requires combining it with key_evidence, so state it plainly as part of the scene description, not as a hint or aside.",
  "victim": "name of the victim",
  "key_evidence": "1-2 sentences: one specific, objective, independently-verifiable fact about a time, place, or object (security footage, a locked door's timestamp, a broken clock, a witness who is not one of the characters, etc.). This fact must stand completely on its own: it must NOT name or point at any character, and must NOT by itself say that anyone's claim is impossible or suspicious - read alone it should look like a neutral, unremarkable detail. It only becomes a contradiction when combined with the connecting fact stated in background.",
  "characters": [
    {"name": "...", "role": "...", "relationship_to_victim": "...", "motive": "..."}
  ],
  "killer": "must exactly match one of the characters' name fields",
  "timeline": {
    "<character name>": "1 specific sentence with a concrete time and place: where this character actually was and what they actually did at the time of the murder - the ground truth, which may differ from what they will later claim"
  }
}
Requirements:
- "characters" must have exactly __N__ entries, one per name, and "timeline" \
must have exactly one entry per character name. Exactly one character is \
the killer.
- The killer's claimed alibi must conflict with "key_evidence" only when \
"key_evidence" is combined with the connecting fact in "background" - \
this two-fact combination (never key_evidence alone) is the one fair, \
checkable clue that solves the case. Neither fact by itself may give away \
the contradiction or mention the killer; a solver must reason through both \
to catch it.
- The other characters' true timeline entries must NOT conflict with \
"key_evidence" combined with "background", even though they may also be \
near or interact with the same connecting fact.
No markdown, no commentary.
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
    if not case.get("key_evidence"):
        raise ValueError("case is missing key_evidence")
    return case
