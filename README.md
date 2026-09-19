# jev-game

A minimal Python starter project, now home to a small experiment comparing
TypeSafe's Jev model against two plain chat models - a small one (SLM) and
a large one (LLM) - as judges.

## Jev vs SLM vs LLM: Mafia judge comparison

Each round is a full whodunit case, designed offline before the server ever
runs:

1. **Case design** (`case_generator.py`) — an OpenAI model (`GENERATOR_MODEL`)
   invents an original background, victim, `CHARACTERS_PER_ROUND` characters
   (currently 6; with a role, relationship to the victim, and motive each),
   one piece of independent **key evidence**, a ground-truth killer, and each
   character's true timeline. The killer's true timeline is written to
   directly conflict with the key evidence — a "fair play" whodunit clue
   (present, checkable, but not spelled out) rather than a stylistic tell.
   Setting seeds (`settings.py`) are generic mystery tropes, not text from
   any specific existing book/show/film.
2. **Statement writing** (`generator.py`) — the same model then writes what
   each character actually says: all statements equally specific and
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

## Results (v3 — more characters)

Same case-design logic as v1 (one `key_evidence`, the killer's statement
contradicts it, everyone else is consistent), but `CHARACTERS_PER_ROUND`
raised from 4 to 6 in `settings.py`. One live 3-judge run against real APIs
(`jev-latest`, `JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`), 10 rounds, played through
`round_runner.run_round` (not simulated):

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| **v3 — 6 characters/round** | **100%** | **389 ms** | **100%** | **718 ms** | **100%** | **858 ms** |

**Takeaways:**
- Accuracy stayed at 100% for all three judges even with 6 suspects instead
  of 4 (a 16.7% random-guess floor vs. 25% before) — the "fair play" clue
  design is robust to more characters, so raw character count alone doesn't
  create a measurable accuracy gap between any of the three judges on
  `gpt-5.4-nano`/`gpt-5.4`.
- An earlier run of this same batch against `gpt-4.1-nano` as the SLM did
  show a gap (70% accuracy, missing 3/10), so the accuracy ceiling here is
  sensitive to which small model is used — `gpt-5.4-nano` closes the gap
  that `gpt-4.1-nano` opened on the identical 6-character case design.
- **Offline case generation itself did get noticeably more expensive**: 10
  rounds of case+statement generation (2 OpenAI calls/round) took ~4m30s
  wall-clock (~27s/round) with 6 characters — expected, since the generator
  model now has to invent and hold consistent 6 motives/relationships/
  timelines instead of 4. This cost is paid once offline into
  `scenarios.json` and never touches judge-vs-judge timing, but it's a real
  cost if scenario count grows.
- Making the case harder via raw character count doesn't widen the
  Jev-vs-chat-model accuracy gap; a red herring or a two-fact clue is a more
  promising lever to try next.

## Test

```bash
pytest
```
