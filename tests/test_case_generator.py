import json
from types import SimpleNamespace

import pytest

from jev_game.case_generator import generate_case


def _fake_openai_response(payload: dict):
    message = SimpleNamespace(content=json.dumps(payload))
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _valid_case():
    return {
        "title": "The Locked Study",
        "background": "A quiet evening ends badly.",
        "victim": "Mr. Grey",
        "characters": [
            {"name": "Ava", "role": "butler", "relationship_to_victim": "employee", "motive": "fired"},
            {"name": "Ben", "role": "nephew", "relationship_to_victim": "heir", "motive": "debts"},
            {"name": "Cara", "role": "guest", "relationship_to_victim": "rival", "motive": "envy"},
            {"name": "Dmitri", "role": "driver", "relationship_to_victim": "employee", "motive": "blackmail"},
        ],
        "killer": "Ben",
        "timeline": {
            "Ava": "in the dining room",
            "Ben": "near the study",
            "Cara": "on the terrace",
            "Dmitri": "in the garage",
        },
    }


@pytest.mark.asyncio
async def test_generate_case_returns_valid_payload(monkeypatch):
    case = _valid_case()

    async def fake_create(*args, **kwargs):
        return _fake_openai_response(case)

    monkeypatch.setattr(
        "jev_game.case_generator.AsyncOpenAI",
        lambda api_key: SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
        ),
    )

    result = await generate_case("a stormy weekend at a remote country manor")

    assert result == case


@pytest.mark.asyncio
async def test_generate_case_rejects_killer_not_in_roster(monkeypatch):
    case = _valid_case()
    case["killer"] = "Nobody"

    async def fake_create(*args, **kwargs):
        return _fake_openai_response(case)

    monkeypatch.setattr(
        "jev_game.case_generator.AsyncOpenAI",
        lambda api_key: SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
        ),
    )

    with pytest.raises(ValueError, match="not among characters"):
        await generate_case("a stormy weekend at a remote country manor")
