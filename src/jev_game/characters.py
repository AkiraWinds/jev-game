"""Fixed pool of characters used to build mafia-mystery scenarios."""

import random

CHARACTER_POOL = [
    {"name": "Ava", "role": "the butler"},
    {"name": "Ben", "role": "the chef"},
    {"name": "Cara", "role": "the gardener"},
    {"name": "Dmitri", "role": "the houseguest"},
    {"name": "Elin", "role": "the driver"},
    {"name": "Faisal", "role": "the accountant"},
]

CHARACTERS_PER_ROUND = 4


def pick_round_characters(rng: random.Random) -> list[dict]:
    """Choose CHARACTERS_PER_ROUND characters for one round."""
    return rng.sample(CHARACTER_POOL, CHARACTERS_PER_ROUND)
