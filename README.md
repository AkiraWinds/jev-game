# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against a plain chat LLM as a judge.

## Jev vs LLM: Mafia judge comparison

Each round: 4 characters, one is secretly the killer. Character statements
are pre-generated once (offline) by an LLM and cached to `scenarios.json`.
At play time, two independent judges each see the same statements and try
to pick the killer:

- **Jev** (`Choice` primitive) — a calibrated probability per suspect
- **A second LLM** — prompted for the same pick + a self-reported confidence

Both are timed independently per round; a web page shows a running
accuracy and average-latency comparison.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in TYPESAFE_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
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
