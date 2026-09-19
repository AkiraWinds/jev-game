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

## Results (v4 — two-step evidence)

v1's `key_evidence` directly named an impossible time/place for the killer,
which was too easy to show a real gap. This variant changes
`case_generator.py`'s prompt so `key_evidence` is a standalone, neutral fact
(a sensor log, a door counter) that never names or implicates anyone, and
`background` separately states a load-bearing "connecting fact" (e.g. the
crime scene has exactly one entrance). The killer's statement only
contradicts the evidence once both facts are combined - a real two-step
inference, not a one-line lookup.

One live 3-judge run against real APIs (`jev-latest`,
`JUDGE_SLM_MODEL=gpt-5.4-nano-2026-03-17`,
`JUDGE_LLM_MODEL=gpt-5.4-2026-03-05`), 10 rounds, played through the actual
judges (not simulated), scenarios saved to `scenarios_two_step.json`:

| Case design | Jev accuracy | Jev avg latency | SLM accuracy | SLM avg latency | LLM accuracy | LLM avg latency |
|---|---|---|---|---|---|---|
| **v4 — two-step evidence** | **100%** (10/10) | **385 ms** | **90%** (9/10) | **705 ms** | **100%** (10/10) | **902 ms** |

Example case (round 2, "The Last Signal"): the signal room "could be opened
only with a brass key held by Rowan Vale" (the connecting fact, stated in
`background`); `key_evidence` says "The brass key was recorded turning in
the signal room lock at 10:14 p.m." - a neutral lock log that names no one.
The killer, Rowan Vale, claims "At 10:14 p.m., the brass key was hanging on
the sauna's hook beside me" - only provably false once you combine the lock
log (the key was in the door, not the sauna, at that exact time) with the
connecting fact (only Rowan held that key). Jev and the large chat model
both caught this; the SLM judge picked the wrong suspect (Tomas Reed) on
this round.

**Takeaways:**
- The two-step design produced a real accuracy gap: Jev and the large LLM
  judge both hit 100%, while the SLM judge missed 1/10 rounds (90%) - the
  accuracy gap here tracks model size (small vs. large chat model) rather
  than judge count.
- This is a single 10-round sample, so the gap is suggestive, not
  conclusive - worth re-running with more rounds or more seeds before
  treating it as reliable.
- Latency ordering held: Jev was fastest (385 ms), then the SLM (705 ms),
  then the LLM slowest (902 ms).
- Inspecting individual cases (e.g. round 2 above) confirms the generator is
  actually producing two-step clues as designed, not accidentally leaking a
  one-step tell - `key_evidence` alone never names a character or states an
  impossibility.

## Test

```bash
pytest
```
