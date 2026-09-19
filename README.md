# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against a plain chat LLM as a judge.

## Jev vs LLM: Mafia judge comparison

Each round is a full whodunit case, designed offline before the server ever
runs:

1. **Case design** (`case_generator.py`) — an OpenAI model (`GENERATOR_MODEL`)
   invents an original background, victim, 4 characters (with a role,
   relationship to the victim, and motive each), a ground-truth killer, and
   each character's true timeline. Setting seeds (`settings.py`) are generic
   mystery tropes, not text from any specific existing book/show/film.
2. **Statement writing** (`generator.py`) — the same model then writes what
   each character actually says: innocents consistent with their true
   timeline, the killer subtly evasive without confessing.
3. Both steps are cached to `scenarios.json`.

At play time, two independent judges each see the case background, victim,
character bios, and statements (never the ground-truth killer or true
timeline) and try to pick the killer:

- **Jev** (`Choice` primitive) — a calibrated probability per suspect
- **A second, different OpenAI model** (`JUDGE_LLM_MODEL`) — prompted for
  the same pick + a self-reported confidence

`GENERATOR_MODEL` and `JUDGE_LLM_MODEL` are deliberately different models so
Judge B is never evaluating text written by its own weights/style.

Both are timed independently per round; a web page shows a running
accuracy and average-latency comparison.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in TYPESAFE_API_KEY, OPENAI_API_KEY
```

### Generate scenarios (offline, once)

```bash
python -m jev_game.generate_scenarios --rounds 5
```

### Run the comparison

```bash
uvicorn jev_game.server:app --reload
```

Open http://127.0.0.1:8000 and click "Run next round" to step through the
pre-generated scenarios.

## Test

```bash
pytest
```
