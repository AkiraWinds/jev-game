# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against two plain chat models - a small one (SLM) and
a large one (LLM) - as judges.

## Jev vs SLM vs LLM: Mafia judge comparison

Each round is a full whodunit case, designed offline before the server ever
runs:

1. **Case design** (`case_generator.py`) — an OpenAI model (`GENERATOR_MODEL`)
   invents an original background, victim, 4 characters (with a role,
   relationship to the victim, and motive each), one piece of independent
   **key evidence**, a ground-truth killer, and each character's true
   timeline. The killer's true timeline is written to directly conflict with
   the key evidence — a "fair play" whodunit clue (present, checkable, but
   not spelled out) rather than a stylistic tell. Setting seeds
   (`settings.py`) are generic mystery tropes, not text from any specific
   existing book/show/film.
2. **Statement writing** (`generator.py`) — the same model then writes what
   each character actually says: all four statements equally specific and
   confident in tone, but the killer's contains one concrete factual claim
   that contradicts the key evidence.
3. Both steps are cached to `scenarios.json`.

At play time, three independent judges each see the case background,
victim, key evidence, character bios, and statements (never the
ground-truth killer or true timeline) and try to pick the killer:

- **Jev** (`Choice` primitive) — a calibrated probability per suspect
- **A small OpenAI chat model** (`JUDGE_SLM_MODEL`) — prompted for the same
  pick + a self-reported confidence
- **A large OpenAI chat model** (`JUDGE_LLM_MODEL`) — same prompt, bigger
  model

`GENERATOR_MODEL`, `JUDGE_SLM_MODEL`, and `JUDGE_LLM_MODEL` are deliberately
three different models so no judge is ever evaluating text written by its
own weights/style.

All three are timed independently per round; a web page shows a running
accuracy and average-latency comparison across all three.

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

## Results (v1 / baseline)

One live 3-judge run against real APIs (`jev-latest`,
`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`), 10 rounds, played through the actual
server + judges (not simulated):

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| **v1 — killer's statement contains one fact that contradicts an explicit `key_evidence`** | **100%** (10/10) | **449 ms** | **90%** (9/10) | **872 ms** | **100%** (10/10) | **1060 ms** |

**Takeaways:**
- Making the clue a concrete, checkable contradiction (a real "fair play"
  whodunit clue, not a stylistic hint) took Jev and the large LLM judge to
  100% accuracy on this batch, while the small-model judge (SLM) missed
  1/10 rounds (90%).
- Jev came out fastest of all three judges — not just faster than the small
  model, but ~2.4× faster than the large one too, while matching the large
  model's accuracy exactly.
- The SLM's 90% is a single 10-round sample (one missed round) — suggestive
  of a real small-vs-large capability gap on this task, not conclusive; worth
  re-running with more rounds/seeds.
- Open question for future variants: can a harder case (more characters, a
  red herring, or a clue that needs two facts combined) widen the gap
  further, especially for the small model?

## Test

```bash
pytest
```
